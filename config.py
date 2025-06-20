import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")
    AZURE_OPENAI_APP_KEY = os.getenv("AZURE_APP_KEY", "egai-prd-operations-123170050-rag-1747299288771")

    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    OAUTH_URL = os.getenv('OAUTH_URL')

    GOOGLE_PLACES_MAX_REQUESTS_PER_SECOND = int(os.getenv("GOOGLE_PLACES_MAX_REQUESTS_PER_SECOND", 10))
    GOOGLE_PLACES_MAX_REQUESTS_PER_DAY = int(os.getenv("GOOGLE_PLACES_MAX_REQUESTS_PER_DAY", 100000))
    
    # Google Places API Configuration
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
    
    # App Configuration
    MAX_CONTEXT_MESSAGES = 10
    DEFAULT_SEARCH_RADIUS = 50000  # 50km in meters
    MAX_RESULTS = 10