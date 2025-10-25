import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    LAVA_API_KEY = os.getenv("LAVA_API_KEY")
    LAVA_ENDPOINT = os.getenv("LAVA_ENDPOINT", "https://api.lavanet.xyz")
    
    # Fetch.ai
    FETCH_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
    
    # Application
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Agent Settings
    CANARY_PERCENTAGE = 0.001  # 0.1% of systems
    MONITORING_INTERVAL = 5  # seconds
    ALERT_THRESHOLD = 0.8  # 80% confidence for alerts

config = Config()
