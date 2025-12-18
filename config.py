import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Azure Cosmos DB Configuration
    COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY = os.getenv("COSMOS_KEY")
    COSMOS_DATABASE = os.getenv("COSMOS_DATABASE")
    
    # Container Names
    ATTORNEY_CONTAINER = "attorney_profiles"
    PUBLIC_DATA_CONTAINER = "public_data_sources"
    
    # Azure Blob Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    BLOB_INTERNAL_CONTAINER = os.getenv("BLOB_INTERNAL_CONTAINER", "internaldoc")
    BLOB_ATTORNEY_HISTORY_CONTAINER = os.getenv("BLOB_ATTORNEY_HISTORY_CONTAINER", "pasthistoricaldata")
    
    # External API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT","https://testgptdemo.openai.azure.com/")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_TEMPERATURE = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7"))
    AZURE_OPENAI_MAX_TOKENS = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "3000"))
    
    # Azure AI Search Configuration
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
    AZURE_SEARCH_INTERNAL_INDEX = os.getenv("AZURE_SEARCH_INTERNAL_INDEX", "internaldoc-index")
    AZURE_SEARCH_HISTORICAL_INDEX = os.getenv("AZURE_SEARCH_HISTORICAL_INDEX", "pasthistoricaldata-index")
    
    AZURE_SEARCH_CONTENT_FIELD = os.getenv("AZURE_SEARCH_CONTENT_FIELD", "merged_content")
    AZURE_SEARCH_METADATA_NAME_FIELD = os.getenv("AZURE_SEARCH_METADATA_NAME_FIELD", "metadata_storage_name")
    AZURE_SEARCH_METADATA_PATH_FIELD = os.getenv("AZURE_SEARCH_METADATA_PATH_FIELD", "metadata_storage_path")

    # Validation Constants
    SENIORITY_LEVELS = ["Associate", "Senior Associate", "Partner", "Senior Partner"]
    PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
    IMPACT_LEVELS = ["Low", "Medium", "High"]
    
    # Business Rules
    MAX_PRACTICE_AREAS = 10
    MAX_NAME_LENGTH = 200
    MAX_YEARS_EXPERIENCE = 60
    MAX_ENRICHMENT_RETRIES = 3
    
    # File Upload
    UPLOAD_DIR = "temp_uploads"
    MAX_FILE_SIZE_MB = 10

settings = Settings()