"""
Legal Data Management API
FastAPI application with Azure Cosmos DB backend
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import shutil
from datetime import datetime
import uuid 
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import models
from models import AttorneyCreate, PublicSourceCreate
from risk_analysis_model import RiskAnalysisRequest, RiskAnalysisResponse
from services.blob_storage_service import internal_container, attorney_history_container, generate_sas_url
from models.blob_storage import UploadResponse, ListResponse, FileItem

# Import services
from services import (
    AttorneyService,
    PublicSourceService,
    EnrichmentService
)
from services.risk_analysis_service import RiskAnalysisService

# Import utils
from utils import ExcelValidator

# Import config
from config import settings

# Create FastAPI app
app = FastAPI(
    title="Legal Data Management API",
    description="Azure Cosmos DB API for Attorney Profiles and Public Data Sources and blob storage",
    version="1.0.0"
)

# Create upload directory
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize services
attorney_service = AttorneyService()
public_source_service = PublicSourceService()
enrichment_service = EnrichmentService()
risk_analysis_service = RiskAnalysisService()

#===========================================
# RISK ANALYSIS ENDPOINT (NEW)
#===========================================

@app.post("/api/v1/risk-analysis", response_model=RiskAnalysisResponse)
async def analyze_company_risk(request: RiskAnalysisRequest):
    """
    Analyze company legal risks using RAG-based approach
    
    This endpoint:
    1. Retrieves relevant documents from AI Search (internal docs + historical data)
    2. Queries public data sources for recent legal developments
    3. Uses Azure OpenAI to analyze risks based on context
    4. Matches the best attorney based on practice area and experience
    5. Generates a professional email template
    6. Returns comprehensive risk analysis with references
    
    Example Request:
    {
        "companyName": "Acme Manufacturing",
        "companyemail": "contact@acme.com",
        "companyphonenumber": "+1-555-0100",
        "practicearea": "Compliance"
    }
    """
    try:
        result = risk_analysis_service.analyze_company_risks(request)
        return result
    except Exception as e:
        logging.error(f"Risk analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error performing risk analysis: {str(e)}"
        )


#===========================================
#BLOB STORAGE ENDPOINTS
#===========================================    

@app.post("/upload/internal", response_model=UploadResponse)
async def upload_internal_file(file: UploadFile = File(...)):
    blob_name = f"internal/{uuid.uuid4()}_{file.filename}"
    internal_container.upload_blob(
        name=blob_name,
        data=file.file,
        overwrite=True,
        metadata={
            "uploaded_at": str(datetime.utcnow()),
            "category": "internal"
        }
    )
    return UploadResponse(filename=blob_name, container="internal-data", uploaded=True)

@app.post("/upload/attorney-history", response_model=UploadResponse)
async def upload_attorney_history_file(file: UploadFile = File(...)):
    blob_name = f"attorney-history/{uuid.uuid4()}_{file.filename}"
    attorney_history_container.upload_blob(
        name=blob_name,
        data=file.file,
        overwrite=True,
        metadata={
            "uploaded_at": str(datetime.utcnow()),
            "category": "attorney_history"
        }
    )
    return UploadResponse(filename=blob_name, container="attorney-history", uploaded=True)

# -------------------- LIST ENDPOINTS WITH SAS --------------------
@app.get("/list/internal", response_model=ListResponse)
def list_internal_files():
    blobs = internal_container.list_blobs(name_starts_with="internal/")
    files = [
        FileItem(filename=blob.name, url=generate_sas_url(internal_container, blob.name))
        for blob in blobs
    ]
    return ListResponse(container="internal-data", files=files)

@app.get("/list/attorney-history", response_model=ListResponse)
def list_attorney_history_files():
    blobs = attorney_history_container.list_blobs(name_starts_with="attorney-history/")
    files = [
        FileItem(filename=blob.name, url=generate_sas_url(attorney_history_container, blob.name))
        for blob in blobs
    ]
    return ListResponse(container="attorney-history", files=files)


# ============================================
# ATTORNEY ENDPOINTS
# ============================================

@app.post("/api/v1/attorneys")
async def create_attorney(attorney: AttorneyCreate):
    """Create a single attorney profile manually"""
    try:
        result = attorney_service.create_attorney(attorney)
        return {
            "message": "Attorney created successfully",
            "attorney_id": result['attorney_id'],
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v1/attorneys/bulk/excel")
async def upload_attorneys_excel(file: UploadFile = File(...)):
    """Bulk upload attorneys from Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format (.xlsx or .xls)")
    
    # Save uploaded file temporarily
    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate Excel
        is_valid, attorneys, errors = ExcelValidator.validate_attorney_excel(str(file_path))
        
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"message": "Validation failed", "errors": errors}
            )
        
        # Bulk create attorneys
        created_ids = attorney_service.bulk_create_attorneys(attorneys)
        
        return {
            "message": f"Successfully created {len(created_ids)} attorneys",
            "created_ids": created_ids,
            "skipped": len(attorneys) - len(created_ids)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temp file
        file_path.unlink(missing_ok=True)


@app.get("/api/v1/attorneys")
async def get_attorneys(
    practice_area: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    min_experience: Optional[int] = Query(None)
):
    """Get all attorneys with optional filters"""
    try:
        attorneys = attorney_service.get_attorneys(
            practice_area=practice_area,
            seniority=seniority,
            min_experience=min_experience
        )
        return {"count": len(attorneys), "attorneys": attorneys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching attorneys: {str(e)}")


@app.get("/api/v1/attorneys/{attorney_id}")
async def get_attorney(attorney_id: str):
    """Get a specific attorney by ID"""
    attorney = attorney_service.get_attorney_by_id(attorney_id)
    if not attorney:
        raise HTTPException(status_code=404, detail="Attorney not found")
    return attorney


@app.delete("/api/v1/attorneys/{attorney_id}")
async def delete_attorney(attorney_id: str):
    """Delete an attorney profile"""
    success = attorney_service.delete_attorney(attorney_id)
    if not success:
        raise HTTPException(status_code=404, detail="Attorney not found")
    return {"message": "Attorney deleted successfully", "attorney_id": attorney_id}


# ============================================
# PUBLIC DATA SOURCE ENDPOINTS
# ============================================

@app.post("/api/v1/public-sources")
async def create_public_source(
    source: PublicSourceCreate,
    background_tasks: BackgroundTasks
):
    """Create a public data source with minimal info (title + URL)"""
    try:
        result = public_source_service.create_public_source(source)
        news_id = result['news_id']
        
        # Schedule background enrichment
        background_tasks.add_task(enrichment_service.enrich_public_source, news_id)
        
        return {
            "message": "Public source created and queued for enrichment",
            "news_id": news_id,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating public source: {str(e)}")


@app.post("/api/v1/public-sources/bulk/excel")
async def upload_public_sources_excel(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """[TEMPORARY] Bulk upload public sources from Excel"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be Excel format")
    
    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate Excel
        is_valid, sources, errors = ExcelValidator.validate_public_data_excel(str(file_path))
        
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"message": "Validation failed", "errors": errors}
            )
        
        # Bulk create public sources
        created_ids = public_source_service.bulk_create_public_sources(sources)
        
        return {
            "message": f"Successfully created {len(created_ids)} public sources",
            "created_ids": created_ids,
            "note": "This endpoint is temporary for initial data seeding"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        file_path.unlink(missing_ok=True)


@app.get("/api/v1/public-sources")
async def get_public_sources(
    risk_area: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    enrichment_status: Optional[str] = Query(None)
):
    """Get all public sources with optional filters"""
    try:
        sources = public_source_service.get_public_sources(
            risk_area=risk_area,
            jurisdiction=jurisdiction,
            enrichment_status=enrichment_status
        )
        return {"count": len(sources), "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching public sources: {str(e)}")


@app.get("/api/v1/public-sources/{news_id}")
async def get_public_source(news_id: str):
    """Get a specific public source by ID"""
    source = public_source_service.get_public_source_by_id(news_id)
    if not source:
        raise HTTPException(status_code=404, detail="Public source not found")
    return source


@app.patch("/api/v1/public-sources/{news_id}/enrich")
async def trigger_enrichment(news_id: str, background_tasks: BackgroundTasks):
    """Manually trigger enrichment for a public source"""
    
    source = public_source_service.get_public_source_by_id(news_id)
    if not source:
        raise HTTPException(status_code=404, detail="Public source not found")
    
    # Check if already completed
    if source['enrichment_status'] == 'completed':
        return {"message": "Already enriched", "news_id": news_id}
    
    # Check retry limit
    if source.get('enrichment_retry_count', 0) >= settings.MAX_ENRICHMENT_RETRIES:
        raise HTTPException(status_code=400, detail="Max retry attempts reached")
    
    # Schedule enrichment
    background_tasks.add_task(enrichment_service.enrich_public_source, news_id)
    
    return {"message": "Enrichment queued", "news_id": news_id}


@app.delete("/api/v1/public-sources/{news_id}")
async def delete_public_source(news_id: str):
    """Delete a public source"""
    success = public_source_service.delete_public_source(news_id)
    if not success:
        raise HTTPException(status_code=404, detail="Public source not found")
    return {"message": "Public source deleted successfully", "news_id": news_id}


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": settings.COSMOS_DATABASE,
        "containers": {
            "attorney_profiles": settings.ATTORNEY_CONTAINER,
            "public_data_sources": settings.PUBLIC_DATA_CONTAINER
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Legal Data Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)