import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Fetch.ai Agentverse
    CANARY_SEED_PHRASE = os.getenv("CANARY_SEED_PHRASE")
    MONITORING_SEED_PHRASE = os.getenv("MONITORING_SEED_PHRASE")
    RESPONSE_SEED_PHRASE = os.getenv("RESPONSE_SEED_PHRASE")
    COMMUNICATION_SEED_PHRASE = os.getenv("COMMUNICATION_SEED_PHRASE")
    
    # Application
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Agent Settings
    CANARY_PERCENTAGE = 0.001
    MONITORING_INTERVAL = 5
    ALERT_THRESHOLD = 0.8

config = Config()