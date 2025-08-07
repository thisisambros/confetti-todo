// Configuration and Constants
export const CONFIG = {
    API_URL: 'http://localhost:8000',
    MAX_ENERGY: 12,
    ENERGY_WARNING_THRESHOLD: 2,
    ENERGY_SUGGESTION_THRESHOLD: 4,
    REGENERATION_INTERVAL: 15 * 60 * 1000, // 15 minutes
    EFFORT_VALUES: {
        '5m': 1,
        '15m': 3,
        '30m': 6,
        '1h': 12,
        '4h': 48
    },
    CATEGORIES: {
        admin: { color: '#ff6b6b', emoji: '📊' },
        selling: { color: '#4ecdc4', emoji: '💰' },
        research: { color: '#45aaf2', emoji: '🔬' },
        product: { color: '#fd79a8', emoji: '🚀' },
        hiring: { color: '#a29bfe', emoji: '👥' },
        other: { color: '#778ca3', emoji: '📌' }
    },
    FRICTION_EMOJI: {
        1: '🍃',
        2: '💨', 
        3: '🌪️'
    }
};

// Determine if we're in test mode
const urlParams = new URLSearchParams(window.location.search);
export const TEST_MODE = urlParams.get('test') === 'true';