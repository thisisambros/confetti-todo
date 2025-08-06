"""
Comprehensive tests for the Energy Regeneration System.
Tests natural energy regeneration, pausing/resuming, and WebSocket updates.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app, energy_storage, regeneration_locks, REGENERATION_INTERVAL, REGENERATION_AMOUNT


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_energy_storage():
    """Reset energy storage before each test"""
    energy_storage.clear()
    regeneration_locks.clear()
    yield
    energy_storage.clear()
    regeneration_locks.clear()


class TestRegenerationEndpoint:
    """Test the regeneration state endpoint"""
    
    def test_get_regeneration_state_initial(self, client):
        """Test getting initial regeneration state"""
        response = client.get("/api/energy/regeneration")
        assert response.status_code == 200
        
        data = response.json()
        assert "regeneration_time_remaining" in data
        assert "is_regenerating" in data
        assert "last_regeneration_time" in data
        
        # With full energy, regeneration should be paused
        assert data["is_regenerating"] is False
        assert data["regeneration_time_remaining"] == 0
    
    def test_get_regeneration_state_after_consumption(self, client):
        """Test regeneration state after consuming energy"""
        # Consume some energy
        client.post("/api/energy/consume", json={"amount": 3})
        
        # Check regeneration state
        response = client.get("/api/energy/regeneration")
        data = response.json()
        
        # Should be regenerating now
        assert data["is_regenerating"] is True
        assert 0 < data["regeneration_time_remaining"] <= REGENERATION_INTERVAL
    
    def test_regeneration_state_with_session(self, client):
        """Test regeneration state with specific session"""
        # Consume energy in a specific session
        client.post("/api/energy/consume?session_id=test-session", json={"amount": 2})
        
        # Check regeneration state for that session
        response = client.get("/api/energy/regeneration?session_id=test-session")
        data = response.json()
        
        assert data["is_regenerating"] is True
        assert data["regeneration_time_remaining"] > 0


class TestRegenerationPauseResume:
    """Test pausing and resuming regeneration"""
    
    def test_pause_regeneration_on_work(self, client):
        """Test that regeneration pauses when working"""
        # Consume energy to enable regeneration
        client.post("/api/energy/consume", json={"amount": 2})
        
        # Get initial regeneration state
        regen1 = client.get("/api/energy/regeneration").json()
        assert regen1["is_regenerating"] is True
        
        # Pause regeneration (simulating work start)
        with client.websocket_connect("/ws") as websocket:
            response = client.post("/api/energy/regeneration/pause")
            assert response.status_code == 200
            
            # Check WebSocket message for regeneration pause
            message = websocket.receive_json()
            assert message["type"] == "regeneration_paused"
            assert message["data"]["is_regenerating"] is False
    
    def test_pause_regeneration_on_break(self, client):
        """Test that regeneration pauses during break"""
        # Consume energy to enable regeneration
        client.post("/api/energy/consume", json={"amount": 4})
        
        # Start a break
        client.post("/api/energy/break?duration_minutes=15")
        
        # Check regeneration state
        response = client.get("/api/energy/regeneration")
        data = response.json()
        
        # Should not be regenerating during break
        assert data["is_regenerating"] is False
        assert data["regeneration_time_remaining"] == 0
    
    def test_resume_regeneration(self, client):
        """Test resuming regeneration after work stops"""
        # Setup: consume energy and pause regeneration
        client.post("/api/energy/consume", json={"amount": 3})
        client.post("/api/energy/regeneration/pause")  # Pause it first
        time.sleep(0.1)  # Let some time pass
        
        # Resume regeneration
        with client.websocket_connect("/ws") as websocket:
            response = client.post("/api/energy/regeneration/resume")
            assert response.status_code == 200
            
            # Check WebSocket message
            message = websocket.receive_json()
            assert message["type"] == "regeneration_resumed"
            assert message["data"]["is_regenerating"] is True
    
    def test_resume_regeneration_no_effect_when_not_paused(self, client):
        """Test that resume has no effect when not paused"""
        # Consume energy to enable regeneration (but don't pause it)
        client.post("/api/energy/consume", json={"amount": 2})
        
        # Get initial state
        initial_state = client.get("/api/energy/regeneration").json()
        
        # Try to resume (should have no effect)
        response = client.post("/api/energy/regeneration/resume")
        assert response.status_code == 200
        
        # State should be unchanged
        final_state = client.get("/api/energy/regeneration").json()
        assert final_state["is_regenerating"] == initial_state["is_regenerating"]


class TestRegenerationTimingCalculations:
    """Test regeneration timing calculations"""
    
    def test_regeneration_time_countdown(self, client):
        """Test that regeneration time counts down properly"""
        # Consume energy to start regeneration
        client.post("/api/energy/consume", json={"amount": 3})
        
        # Get initial time
        time1 = client.get("/api/energy/regeneration").json()["regeneration_time_remaining"]
        
        # Wait a bit
        time.sleep(2.1)  # Sleep slightly more than 2 seconds
        
        # Get time again
        time2 = client.get("/api/energy/regeneration").json()["regeneration_time_remaining"]
        
        # Time should have decreased by at least 2 seconds
        assert time2 < time1
        assert time1 - time2 >= 2  # At least 2 seconds passed
    
    def test_regeneration_pause_preserves_time(self, client):
        """Test that pausing preserves regeneration time"""
        # Start regeneration
        client.post("/api/energy/consume", json={"amount": 2})
        
        # Wait a bit
        time.sleep(1)
        
        # Get time before pause
        time_before = client.get("/api/energy/regeneration").json()["regeneration_time_remaining"]
        
        # Pause regeneration
        client.post("/api/energy/regeneration/pause")
        
        # Wait while paused
        time.sleep(2)
        
        # Resume
        client.post("/api/energy/regeneration/resume")
        
        # Time should be approximately the same as before pause
        time_after = client.get("/api/energy/regeneration").json()["regeneration_time_remaining"]
        assert abs(time_after - time_before) < 2  # Allow small variance


class TestRegenerationIntegration:
    """Integration tests for regeneration with other energy features"""
    
    def test_regeneration_stops_at_max_energy(self, client):
        """Test that regeneration stops when energy is full"""
        # Consume just 1 energy
        client.post("/api/energy/consume", json={"amount": 1})
        
        # Check that regeneration is active
        regen_state = client.get("/api/energy/regeneration").json()
        assert regen_state["is_regenerating"] is True
        
        # Manually restore to full energy
        energy_state = client.get("/api/energy").json()
        if energy_state["current_energy"] < energy_state["max_energy"]:
            # Force energy to max (simulating regeneration completion)
            from server import get_or_create_energy_state
            state = get_or_create_energy_state("default")
            state.current_energy = state.max_energy
        
        # Check regeneration state
        regen_state = client.get("/api/energy/regeneration").json()
        assert regen_state["is_regenerating"] is False
    
    def test_regeneration_after_break_completion(self, client):
        """Test regeneration resumes after break completes"""
        # Consume energy
        client.post("/api/energy/consume", json={"amount": 6})
        
        # Take a break
        client.post("/api/energy/break?duration_minutes=15")
        
        # Complete the break
        client.post("/api/energy/restore")
        
        # Check energy state
        energy_state = client.get("/api/energy").json()
        
        # If not at max energy, regeneration should be active
        if energy_state["current_energy"] < energy_state["max_energy"]:
            regen_state = client.get("/api/energy/regeneration").json()
            assert regen_state["is_regenerating"] is True
    
    def test_daily_reset_regeneration_state(self, client):
        """Test that daily reset properly initializes regeneration"""
        # Setup: consume energy and modify regeneration state
        client.post("/api/energy/consume", json={"amount": 5})
        
        # Manually trigger daily reset
        from server import get_or_create_energy_state
        state = get_or_create_energy_state("default")
        state.last_reset_date = datetime.now().date() - timedelta(days=1)
        
        # Get energy to trigger reset
        client.get("/api/energy")
        
        # Check regeneration state
        regen_state = client.get("/api/energy/regeneration").json()
        
        # Should not be regenerating (full energy after reset)
        assert regen_state["is_regenerating"] is False
        assert regen_state["regeneration_time_remaining"] == 0


class TestRegenerationWebSocketUpdates:
    """Test WebSocket updates for regeneration events"""
    
    @pytest.mark.asyncio
    async def test_regeneration_broadcast(self):
        """Test that regeneration events are broadcast via WebSocket"""
        client = TestClient(app)
        
        with client.websocket_connect("/ws") as websocket:
            # Consume energy to start regeneration
            client.post("/api/energy/consume", json={"amount": 3})
            
            # Should receive energy consumed message
            message = websocket.receive_json()
            assert message["type"] == "energy_consumed"
            
            # Pause regeneration
            client.post("/api/energy/regeneration/pause")
            
            # Should receive regeneration paused message
            message = websocket.receive_json()
            assert message["type"] == "regeneration_paused"
            
            # Resume regeneration
            client.post("/api/energy/regeneration/resume")
            
            # Should receive regeneration resumed message
            message = websocket.receive_json()
            assert message["type"] == "regeneration_resumed"
            assert "regeneration_time_remaining" in message["data"]
            assert "is_regenerating" in message["data"]
            assert "last_regeneration_time" in message["data"]


class TestRegenerationBackgroundTask:
    """Test the background regeneration task (requires manual verification)"""
    
    def test_regeneration_data_structure(self, client):
        """Test that regeneration maintains proper data structure"""
        # Consume energy
        client.post("/api/energy/consume", json={"amount": 4})
        
        # Get both energy and regeneration state
        energy_state = client.get("/api/energy").json()
        regen_state = client.get("/api/energy/regeneration").json()
        
        # Verify data consistency
        assert energy_state["current_energy"] == 8  # 12 - 4
        assert regen_state["is_regenerating"] is True
        assert isinstance(regen_state["regeneration_time_remaining"], int)
        assert isinstance(regen_state["last_regeneration_time"], str)
        
        # Verify ISO format for datetime
        try:
            datetime.fromisoformat(regen_state["last_regeneration_time"].replace('Z', '+00:00'))
        except:
            pytest.fail("last_regeneration_time is not in valid ISO format")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])