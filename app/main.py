"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting HR Screening Pipeline...")
    logger.info(f"API Base URL: {settings.usf_base_url}")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"ChromaDB directory: {settings.chroma_persist_dir}")
    yield
    logger.info("Shutting down HR Screening Pipeline...")


app = FastAPI(
    title="HR Resume Screening & Matching Pipeline",
    description="""
    AI-powered HR system that screens resumes, matches candidates to job descriptions,
    and ranks applicants based on fit using semantic search and RAG.
    
    ## Features
    
    - **Resume Upload**: Parse PDF and DOCX resumes
    - **Job Management**: Create and manage job descriptions
    - **Screening**: Filter candidates by minimum requirements
    - **Matching**: Semantic similarity matching
    - **Ranking**: Score and rank candidates
    - **Reports**: Generate detailed candidate reports
    
    ## Architecture
    
    Resume Upload → Resume Parser → Router Agent → [Screening Agent / Matching Agent / Ranking Agent]
                                                              ↓
                                                       RAG Pipeline (Job Descriptions + Skills DB)
                                                              ↓
                                                      Candidate Ranking & Report
    """,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["HR Screening"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "HR Resume Screening & Matching Pipeline",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
