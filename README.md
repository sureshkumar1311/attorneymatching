# Legal Data Management System

A comprehensive FastAPI application for managing attorney profiles and public data sources with Azure Cosmos DB and Azure Blob Storage integration.

## 🎯 Features

### Core Functionality
- ✅ **Attorney Profile Management**: Create, read, update, delete attorney profiles
- ✅ **Public Data Source Management**: Manage news articles, regulations, and public sources
- ✅ **Bulk Operations**: Upload data via Excel files
- ✅ **Background Enrichment**: Automatic data enrichment using OpenAI
- ✅ **Document Storage**: Upload and manage documents in Azure Blob Storage
- ✅ **SAS URL Generation**: Secure temporary access to blob storage files

### Technical Features
- 🔐 Azure Cosmos DB for NoSQL data storage
- ☁️ Azure Blob Storage for document management
- 🚀 FastAPI with automatic API documentation
- 📊 Excel file validation and bulk upload
- 🔄 Background task processing
- 🏥 Health check endpoints

---

## 📋 Prerequisites

- Python 3.8 or higher
- Azure Cosmos DB account
- Azure Storage account
- (Optional) OpenAI API key for enrichment

---

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
cd "C:\Users\OneDrive - Kryptos\Desktop\AFS-CHAT - Copy"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# Azure Cosmos DB Configuration
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-primary-key
COSMOS_DATABASE=ai-attorneymatch

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your-account;AccountKey=your-key;EndpointSuffix=core.windows.net
BLOB_INTERNAL_CONTAINER=internaldoc
BLOB_ATTORNEY_HISTORY_CONTAINER=pasthistoricaldata

# Optional: OpenAI for Enrichment
OPENAI_API_KEY=your-openai-api-key
```

### 4. Test Connections

```bash
python test_connections.py
```

This will verify:
- ✅ Configuration is properly loaded
- ✅ Cosmos DB connection works
- ✅ Blob Storage connection works
- ✅ All containers are accessible

### 5. Start the Server

**Option A: Using the startup script (Windows)**
```bash
start.bat
```

**Option B: Using Python directly**
```bash
python main.py
```

The API will start on `http://localhost:8000`

---

## 📚 API Documentation

Once the server is running, access:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

For detailed endpoint documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 🏗️ Project Structure

```
AFS-CHAT - Copy/
│
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration management
├── database.py                  # Cosmos DB client
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create this)
│
├── models/                      # Pydantic models
│   ├── attorney.py             # Attorney data models
│   ├── public_source.py        # Public source models
│   └── blob_storage.py         # Blob storage models
│
├── services/                    # Business logic
│   ├── attorney_service.py     # Attorney operations
│   ├── public_source_service.py # Public source operations
│   ├── blob_storage_service.py # Blob storage operations
│   ├── enrichment_service.py   # Data enrichment logic
│   └── database_service.py     # Database abstraction
│
├── utils/                       # Utility functions
│   └── excel_validator.py      # Excel file validation
│
├── temp_uploads/                # Temporary file storage
│
├── test_connections.py          # Connection testing script
├── start.bat                    # Windows startup script
│
└── API_DOCUMENTATION.md         # Detailed API documentation
```

---

## 💾 Database Schema

### Attorney Profile (Cosmos DB)
```json
{
  "attorney_id": "uuid",
  "name": "John Doe",
  "seniority": "Partner",
  "years_of_experience": 15,
  "practice_areas": [
    {
      "area": "Corporate Law",
      "proficiency": "Expert"
    }
  ],
  "major_cases": [
    {
      "case_title": "ABC Corp vs XYZ Inc",
      "outcome": "Won",
      "impact_level": "High"
    }
  ],
  "jurisdictions": ["New York", "California"],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Public Data Source (Cosmos DB)
```json
{
  "news_id": "uuid",
  "title": "New Regulation Announced",
  "url": "https://example.com/article",
  "risk_area": "Compliance",
  "jurisdiction": "New York",
  "summary": "Auto-generated summary...",
  "key_points": ["point1", "point2"],
  "enrichment_status": "completed",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Blob Storage Structure
```
internaldoc/
  └── internal/
      └── uuid_document.pdf

pasthistoricaldata/
  └── attorney-history/
      └── uuid_history.pdf
```

---

## 🧪 Testing

### Test Connection
```bash
python test_connections.py
```

### Test API Endpoints

**Using cURL:**
```bash
# Health check
curl http://localhost:8000/health

# Upload a document
curl -X POST http://localhost:8000/upload/internal -F "file=@test.pdf"

# Create an attorney
curl -X POST http://localhost:8000/api/v1/attorneys \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","seniority":"Partner","years_of_experience":15,"practice_areas":[{"area":"Corporate Law","proficiency":"Expert"}],"jurisdictions":["NY"]}'
```

**Using Python:**
```python
import requests

# Upload file
with open('test.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload/internal',
        files={'file': f}
    )
    print(response.json())

# Create attorney
attorney_data = {
    "name": "Jane Smith",
    "seniority": "Partner",
    "years_of_experience": 12,
    "practice_areas": [{"area": "Criminal Law", "proficiency": "Expert"}],
    "jurisdictions": ["TX"]
}
response = requests.post(
    'http://localhost:8000/api/v1/attorneys',
    json=attorney_data
)
print(response.json())
```

---

## 🔧 Configuration

### Settings (config.py)

All configuration is managed through the `Settings` class:

```python
class Settings:
    # Cosmos DB
    COSMOS_ENDPOINT
    COSMOS_KEY
    COSMOS_DATABASE
    
    # Blob Storage
    AZURE_STORAGE_CONNECTION_STRING
    BLOB_INTERNAL_CONTAINER
    BLOB_ATTORNEY_HISTORY_CONTAINER
    
    # Validation
    SENIORITY_LEVELS = ["Associate", "Senior Associate", "Partner", "Senior Partner"]
    PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
    
    # File Upload
    MAX_FILE_SIZE_MB = 10
    UPLOAD_DIR = "temp_uploads"
```

---

## 🐛 Troubleshooting

### Common Issues

**1. AttributeError: 'NoneType' object has no attribute 'rstrip'**
- **Cause**: Missing `AZURE_STORAGE_CONNECTION_STRING` in `.env`
- **Solution**: Add the connection string to your `.env` file

**2. CosmosResourceNotFoundError**
- **Cause**: Invalid Cosmos DB credentials
- **Solution**: Verify `COSMOS_ENDPOINT` and `COSMOS_KEY` in `.env`

**3. Container creation fails**
- **Cause**: Insufficient permissions or incorrect container names
- **Solution**: Check Azure portal permissions and container names

**4. Import errors**
- **Cause**: Missing dependencies
- **Solution**: Run `pip install -r requirements.txt`

### Debug Mode

Enable debug logging by running:
```bash
python test_connections.py
```

This will show detailed connection information.

---

## 📊 Performance Considerations

- **Blob Storage**: Files are uploaded with unique UUIDs to prevent conflicts
- **SAS URLs**: Expire after 10 minutes for security
- **Background Tasks**: Enrichment runs asynchronously to avoid blocking
- **Partition Keys**: Cosmos DB uses `seniority` and `jurisdiction` for optimal performance

---

## 🔐 Security

- All sensitive credentials are stored in `.env` (never commit this file)
- SAS URLs provide temporary, limited access to blob storage
- Cosmos DB uses secure HTTPS connections
- API supports CORS for web applications

---

## 📈 Future Enhancements

- [ ] Authentication and authorization
- [ ] Advanced search and filtering
- [ ] Document OCR and text extraction
- [ ] Real-time notifications
- [ ] Analytics dashboard
- [ ] Rate limiting
- [ ] Caching layer

---

## 📞 Support

For issues or questions:
1. Check the [API Documentation](API_DOCUMENTATION.md)
2. Review the troubleshooting section above
3. Run `python test_connections.py` to diagnose connection issues

---

## 📄 License

This project is proprietary and confidential.

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Microsoft Azure for cloud services
- Pydantic for data validation
