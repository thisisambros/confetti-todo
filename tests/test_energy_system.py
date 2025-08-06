"""
Comprehensive tests for the Energy System API endpoints.
Tests all energy-related functionality including consumption, breaks, restoration, and WebSocket updates.
"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient
from fastapi import WebSocket
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app, energy_storage, get_or_create_energy_state


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_energy_storage():
    """Reset energy storage before each test"""
    energy_storage.clear()
    yield
    energy_storage.clear()


class TestEnergyEndpoints:
    """Test all energy system endpoints"""
    
    def test_get_initial_energy_state(self, client):
        """Test getting initial energy state"""
        response = client.get("/api/energy")
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_energy"] == 12
        assert data["max_energy"] == 12
        assert data["is_on_break"] is False
        assert data["break_end_time"] is None
        assert data["session_id"] == "default"
    
    def test_get_energy_with_session_id(self, client):
        """Test getting energy state with specific session ID"""
        response = client.get("/api/energy?session_id=test-session")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == "test-session"
        assert data["current_energy"] == 12
    
    def test_consume_energy_basic(self, client):
        """Test basic energy consumption"""
        response = client.post("/api/energy/consume", json={
            "amount": 3,
            "task_id": "task_123"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_energy"] == 9
        assert data["energy_consumed"] == 3
        assert data["success"] is True
        
        # Verify state persists
        response = client.get("/api/energy")
        assert response.json()["current_energy"] == 9
    
    def test_consume_energy_with_task_metadata(self, client):
        """Test energy consumption calculated from task metadata"""
        # Test 1 hour task with normal friction
        response = client.post("/api/energy/consume", json={
            "amount": 1,  # Will be overridden by calculation
            "task_id": "task_456",
            "task_metadata": {
                "effort": "1h",
                "friction": 2
            }
        })
        assert response.status_code == 200
        assert response.json()["energy_consumed"] == 2  # 60 minutes / 30 = 2
        
        # Test high friction task
        response = client.post("/api/energy/consume", json={
            "amount": 1,
            "task_metadata": {
                "effort": "30m",
                "friction": 5
            }
        })
        assert response.status_code == 200
        assert response.json()["energy_consumed"] == 4  # base 1 + (5-2) = 4
    
    def test_consume_energy_insufficient(self, client):
        """Test consuming more energy than available"""
        # First consume most energy
        client.post("/api/energy/consume", json={"amount": 10})
        
        # Try to consume more than remaining
        response = client.post("/api/energy/consume", json={"amount": 5})
        assert response.status_code == 400
        assert "Insufficient energy" in response.json()["detail"]
    
    def test_consume_energy_while_on_break(self, client):
        """Test that energy cannot be consumed while on break"""
        # Consume some energy first to be able to take a break
        client.post("/api/energy/consume", json={"amount": 2})
        
        # Start a break
        client.post("/api/energy/break")
        
        # Try to consume energy
        response = client.post("/api/energy/consume", json={"amount": 2})
        assert response.status_code == 400
        assert "Cannot consume energy while on break" in response.json()["detail"]
    
    def test_start_break(self, client):
        """Test starting a break"""
        # Consume some energy first
        client.post("/api/energy/consume", json={"amount": 4})
        
        # Start break
        response = client.post("/api/energy/break?duration_minutes=30")
        assert response.status_code == 200
        
        data = response.json()
        assert "break_end_time" in data
        assert data["duration_minutes"] == 30
        assert data["energy_to_restore"] == 2  # 30 minutes / 15 = 2
        
        # Verify state
        response = client.get("/api/energy")
        assert response.json()["is_on_break"] is True
    
    def test_start_break_already_on_break(self, client):
        """Test starting a break when already on break"""
        # Consume some energy first to be able to take a break
        client.post("/api/energy/consume", json={"amount": 2})
        
        client.post("/api/energy/break")
        
        response = client.post("/api/energy/break")
        assert response.status_code == 400
        assert "Already on break" in response.json()["detail"]
    
    def test_start_break_full_energy(self, client):
        """Test starting a break with full energy"""
        response = client.post("/api/energy/break")
        assert response.status_code == 400
        assert "Energy is already full" in response.json()["detail"]
    
    def test_break_duration_limits(self, client):
        """Test break duration limits"""
        client.post("/api/energy/consume", json={"amount": 6})
        
        # Test minimum duration
        response = client.post("/api/energy/break?duration_minutes=2")
        data = response.json()
        assert data["duration_minutes"] == 5  # Minimum is 5
        
        # Complete break
        client.post("/api/energy/restore")
        
        # Test maximum duration
        response = client.post("/api/energy/break?duration_minutes=120")
        data = response.json()
        assert data["duration_minutes"] == 60  # Maximum is 60
    
    def test_complete_break_early(self, client):
        """Test completing a break early"""
        # Consume energy and start break
        client.post("/api/energy/consume", json={"amount": 6})
        client.post("/api/energy/break?duration_minutes=30")
        
        # Complete break immediately
        response = client.post("/api/energy/restore")
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_energy"] > 6
        assert data["energy_restored"] >= 1
        assert data["success"] is True
        
        # Verify no longer on break
        response = client.get("/api/energy")
        assert response.json()["is_on_break"] is False
    
    def test_complete_break_not_on_break(self, client):
        """Test completing break when not on break"""
        response = client.post("/api/energy/restore")
        assert response.status_code == 400
        assert "Not currently on break" in response.json()["detail"]
    
    def test_daily_reset(self, client):
        """Test daily energy reset"""
        # Consume energy
        client.post("/api/energy/consume", json={"amount": 8})
        
        # Manually modify last reset date to yesterday
        state = get_or_create_energy_state("default")
        yesterday = datetime.now().date() - timedelta(days=1)
        state.last_reset_date = yesterday
        
        # Get energy - should trigger reset
        response = client.get("/api/energy")
        data = response.json()
        assert data["current_energy"] == 12
        assert data["is_on_break"] is False
    
    def test_multiple_sessions(self, client):
        """Test energy management across multiple sessions"""
        # Session 1
        client.post("/api/energy/consume?session_id=user1", json={"amount": 3})
        
        # Session 2
        client.post("/api/energy/consume?session_id=user2", json={"amount": 5})
        
        # Verify independent states
        response1 = client.get("/api/energy?session_id=user1")
        assert response1.json()["current_energy"] == 9
        
        response2 = client.get("/api/energy?session_id=user2")
        assert response2.json()["current_energy"] == 7
    
    def test_energy_calculation_edge_cases(self, client, reset_energy_storage):
        """Test edge cases in energy calculation"""
        # Test with day-long task
        response = client.post("/api/energy/consume", json={
            "amount": 1,
            "task_metadata": {
                "effort": "2d",
                "friction": 2
            }
        })
        assert response.status_code == 200
        # 2 days = 16 hours = 960 minutes / 30 = 32, but capped at 12
        assert response.json()["energy_consumed"] == 12
        
        # Reset energy state for second test
        energy_storage.clear()
        
        # Test with minimal task
        response = client.post("/api/energy/consume", json={
            "amount": 1,
            "task_metadata": {
                "effort": "5m",
                "friction": 1
            }
        })
        assert response.status_code == 200
        assert response.json()["energy_consumed"] == 1  # Minimum is 1


class TestWebSocketIntegration:
    """Test WebSocket broadcasting for energy updates"""
    
    @pytest.mark.asyncio
    async def test_energy_consumed_broadcast(self):
        """Test WebSocket broadcast when energy is consumed"""
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            # Consume energy
            response = client.post("/api/energy/consume", json={
                "amount": 3,
                "task_id": "test_task"
            })
            
            # Check WebSocket message
            message = websocket.receive_json()
            assert message["type"] == "energy_consumed"
            assert message["data"]["current_energy"] == 9
            assert message["data"]["energy_consumed"] == 3
            assert message["data"]["task_id"] == "test_task"
    
    @pytest.mark.asyncio
    async def test_break_started_broadcast(self):
        """Test WebSocket broadcast when break starts"""
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            # Consume energy first
            client.post("/api/energy/consume", json={"amount": 4})
            websocket.receive_json()  # Consume message
            
            # Start break
            response = client.post("/api/energy/break?duration_minutes=15")
            
            # Check WebSocket message
            message = websocket.receive_json()
            assert message["type"] == "break_started"
            assert message["data"]["duration_minutes"] == 15
            assert message["data"]["energy_to_restore"] == 1
    
    @pytest.mark.asyncio
    async def test_energy_restored_broadcast(self):
        """Test WebSocket broadcast when energy is restored"""
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            # Setup: consume energy and start break
            client.post("/api/energy/consume", json={"amount": 6})
            websocket.receive_json()
            
            client.post("/api/energy/break?duration_minutes=30")
            websocket.receive_json()
            
            # Complete break
            response = client.post("/api/energy/restore")
            
            # Check WebSocket message
            message = websocket.receive_json()
            assert message["type"] == "energy_restored"
            assert message["data"]["current_energy"] > 6
            assert message["data"]["energy_restored"] >= 1


class TestEnergySystemIntegration:
    """Integration tests for energy system with task management"""
    
    def test_energy_with_task_completion_flow(self, client):
        """Test complete flow: consume energy, work on task, take break"""
        # Get initial stats
        initial_stats = client.get("/api/stats").json()
        
        # Start working on a task (consume energy)
        response = client.post("/api/energy/consume", json={
            "amount": 3,
            "task_id": "task_1",
            "task_metadata": {
                "effort": "1h",
                "friction": 3,
                "category": "work"
            }
        })
        assert response.status_code == 200
        assert response.json()["energy_consumed"] == 3  # base 2 + (3-2) = 3
        
        # Take a break
        response = client.post("/api/energy/break?duration_minutes=15")
        assert response.status_code == 200
        
        # Complete break
        response = client.post("/api/energy/restore")
        assert response.status_code == 200
        
        # Verify energy was restored
        final_energy = client.get("/api/energy").json()
        assert final_energy["current_energy"] == 10  # 12 - 3 + 1 = 10
    
    def test_quick_win_energy_consideration(self, client):
        """Test that quick win suggestions consider current energy"""
        # This test verifies the integration point where quick wins
        # should consider available energy (future enhancement)
        
        # Consume most energy
        client.post("/api/energy/consume", json={"amount": 10})
        
        # Get quick win suggestion
        response = client.get("/api/quick-win")
        # Currently quick-win doesn't filter by energy, but this test
        # documents where that integration would happen
        
        # Verify we still get suggestions even with low energy
        if response.status_code == 200 and response.json():
            quick_win = response.json()
            assert "effort" in quick_win
            assert "xp" in quick_win


if __name__ == "__main__":
    pytest.main([__file__, "-v"])