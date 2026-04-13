"""FastAPI routes for the HR Screening application."""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.candidate import Candidate, CandidateResponse, ResumeData
from app.models.job import JobDescription, JobDescriptionCreate, JobDescriptionResponse, SkillRequirement
from app.models.matching import ScreeningResult, MatchResult, RankingResult
from app.services.resume_parser import resume_parser
from app.services.vector_store import vector_store
from app.services.rag_pipeline import rag_pipeline
from app.agents.router_agent import router_agent
from app.agents.screening_agent import screening_agent
from app.agents.matching_agent import matching_agent
from app.agents.ranking_agent import ranking_agent

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage (replace with database in production)
candidates_db = {}
jobs_db = {}


# ==================== Health Check ====================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ==================== Candidate Endpoints ====================

@router.post("/candidates/upload", response_model=CandidateResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload and parse a resume file.
    
    Accepts PDF and DOCX files.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    extension = file.filename.lower().split(".")[-1]
    if extension not in ["pdf", "docx", "doc"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {extension}. Supported: PDF, DOCX"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    try:
        # Parse resume
        resume_data, file_path = await resume_parser.parse_resume_from_bytes(
            content=content,
            filename=file.filename,
            upload_dir=settings.upload_dir
        )
        
        # Create candidate
        candidate = Candidate(
            resume_data=resume_data,
            file_name=file.filename,
            file_path=file_path
        )
        
        # Store candidate
        candidates_db[candidate.id] = candidate
        
        # Index in vector store
        await rag_pipeline.index_candidate(candidate)
        
        logger.info(f"Successfully uploaded resume: {file.filename} -> {candidate.id}")
        
        return CandidateResponse.from_candidate(candidate)
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_single_resume(file: UploadFile):
    """Helper function to process a single resume (for parallel processing)."""
    try:
        if not file.filename:
            return None, {"file": "unknown", "error": "No filename"}
        
        extension = file.filename.lower().split(".")[-1]
        if extension not in ["pdf", "docx", "doc"]:
            return None, {"file": file.filename, "error": f"Unsupported format: {extension}"}
        
        content = await file.read()
        
        resume_data, file_path = await resume_parser.parse_resume_from_bytes(
            content=content,
            filename=file.filename,
            upload_dir=settings.upload_dir
        )
        
        candidate = Candidate(
            resume_data=resume_data,
            file_name=file.filename,
            file_path=file_path
        )
        
        candidates_db[candidate.id] = candidate
        await rag_pipeline.index_candidate(candidate)
        
        return CandidateResponse.from_candidate(candidate).model_dump(), None
        
    except Exception as e:
        return None, {"file": file.filename, "error": str(e)}


@router.post("/candidates/upload/bulk")
async def upload_resumes_bulk(files: List[UploadFile] = File(...)):
    """
    Upload multiple resume files at once IN PARALLEL.
    """
    # Process all files in parallel
    tasks = [_process_single_resume(file) for file in files]
    results_with_errors = await asyncio.gather(*tasks, return_exceptions=True)
    
    results = []
    errors = []
    
    for result_or_error in results_with_errors:
        if isinstance(result_or_error, Exception):
            errors.append({"file": "unknown", "error": str(result_or_error)})
        else:
            candidate_result, error = result_or_error
            if candidate_result:
                results.append(candidate_result)
            if error:
                errors.append(error)
    
    return {
        "uploaded": len(results),
        "failed": len(errors),
        "candidates": results,
        "errors": errors
    }


@router.get("/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all candidates with pagination."""
    candidates = list(candidates_db.values())[skip:skip + limit]
    return [CandidateResponse.from_candidate(c) for c in candidates]


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str):
    """Get detailed candidate information."""
    candidate = candidates_db.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "id": candidate.id,
        "resume_data": candidate.resume_data.model_dump(),
        "file_name": candidate.file_name,
        "created_at": candidate.created_at.isoformat()
    }


@router.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str):
    """Delete a candidate."""
    if candidate_id not in candidates_db:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    del candidates_db[candidate_id]
    vector_store.delete_candidate(candidate_id)
    
    return {"status": "deleted", "candidate_id": candidate_id}


# ==================== Job Description Endpoints ====================

@router.post("/jobs", response_model=JobDescriptionResponse)
async def create_job(job_data: JobDescriptionCreate):
    """Create a new job description."""
    try:
        # Convert skill lists to SkillRequirement objects
        required_skills = [
            SkillRequirement(skill=s, importance="required")
            for s in job_data.required_skills
        ]
        preferred_skills = [
            SkillRequirement(skill=s, importance="preferred")
            for s in job_data.preferred_skills
        ]
        
        job = JobDescription(
            title=job_data.title,
            department=job_data.department,
            location=job_data.location,
            employment_type=job_data.employment_type,
            remote_policy=job_data.remote_policy,
            description=job_data.description,
            responsibilities=job_data.responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            min_experience_years=job_data.min_experience_years,
            max_experience_years=job_data.max_experience_years,
            required_education=job_data.required_education,
            required_certifications=job_data.required_certifications,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max
        )
        
        # Store job
        jobs_db[job.id] = job
        
        # Index in vector store
        await rag_pipeline.index_job(job)
        
        logger.info(f"Created job: {job.title} -> {job.id}")
        
        return JobDescriptionResponse.from_job(job)
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobDescriptionResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True)
):
    """List all job descriptions with pagination."""
    jobs = list(jobs_db.values())
    
    if active_only:
        jobs = [j for j in jobs if j.is_active]
    
    jobs = jobs[skip:skip + limit]
    return [JobDescriptionResponse.from_job(j) for j in jobs]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get detailed job description."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.model_dump()


@router.put("/jobs/{job_id}")
async def update_job(job_id: str, job_data: JobDescriptionCreate):
    """Update a job description."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    existing_job = jobs_db[job_id]
    
    # Update fields
    existing_job.title = job_data.title
    existing_job.department = job_data.department
    existing_job.location = job_data.location
    existing_job.employment_type = job_data.employment_type
    existing_job.remote_policy = job_data.remote_policy
    existing_job.description = job_data.description
    existing_job.responsibilities = job_data.responsibilities
    existing_job.required_skills = [
        SkillRequirement(skill=s, importance="required")
        for s in job_data.required_skills
    ]
    existing_job.preferred_skills = [
        SkillRequirement(skill=s, importance="preferred")
        for s in job_data.preferred_skills
    ]
    existing_job.min_experience_years = job_data.min_experience_years
    existing_job.max_experience_years = job_data.max_experience_years
    existing_job.required_education = job_data.required_education
    existing_job.updated_at = datetime.now()
    
    # Re-index in vector store
    await rag_pipeline.index_job(existing_job)
    
    return JobDescriptionResponse.from_job(existing_job)


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job description."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del jobs_db[job_id]
    vector_store.delete_job(job_id)
    
    return {"status": "deleted", "job_id": job_id}


# ==================== Screening & Matching Endpoints ====================

@router.post("/screen/{job_id}/{candidate_id}")
async def screen_candidate(
    job_id: str,
    candidate_id: str,
    strict_mode: bool = Query(False)
):
    """Screen a single candidate against a job."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    result = await screening_agent.execute(candidate, job, strict_mode)
    return result.model_dump()


@router.post("/match/{job_id}/{candidate_id}")
async def match_candidate(job_id: str, candidate_id: str):
    """Perform detailed matching for a candidate-job pair."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    result = await matching_agent.execute(candidate, job)
    return result.model_dump()


@router.post("/pipeline/{job_id}")
async def run_pipeline(
    job_id: str,
    candidate_ids: List[str] = Body(default=None),
    skip_screening: bool = Query(False),
    strict_screening: bool = Query(False)
):
    """
    Run the full screening pipeline for candidates against a job.
    
    If candidate_ids is not provided, runs against all candidates.
    """
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get candidates
    if candidate_ids:
        candidates = [candidates_db[cid] for cid in candidate_ids if cid in candidates_db]
        if not candidates:
            raise HTTPException(status_code=404, detail="No valid candidates found")
    else:
        candidates = list(candidates_db.values())
    
    if not candidates:
        raise HTTPException(status_code=400, detail="No candidates to process")
    
    result = await router_agent.execute(
        candidates=candidates,
        job=job,
        skip_screening=skip_screening,
        strict_screening=strict_screening
    )
    
    return result


@router.post("/pipeline/single/{job_id}/{candidate_id}")
async def run_pipeline_single(
    job_id: str,
    candidate_id: str,
    skip_screening: bool = Query(False)
):
    """Run the pipeline for a single candidate."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    result = await router_agent.process_single_candidate(
        candidate=candidate,
        job=job,
        skip_screening=skip_screening
    )
    
    return result.model_dump()


# ==================== Ranking Endpoints ====================

@router.get("/rankings/{job_id}")
async def get_rankings(
    job_id: str,
    top_k: int = Query(10, ge=1, le=100),
    min_score: float = Query(0.0, ge=0, le=100)
):
    """Get candidate rankings for a job (requires pipeline to have been run)."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Run matching for all candidates
    candidates = list(candidates_db.values())
    if not candidates:
        return {"rankings": [], "total": 0}
    
    # Get match results
    match_results = await matching_agent.batch_match(candidates, job)
    
    # Create rankings
    candidates_dict = {c.id: c for c in candidates}
    ranking_result = await ranking_agent.execute(match_results, candidates_dict, job)
    
    # Filter by min_score
    filtered_rankings = [
        r for r in ranking_result.rankings
        if r.get("overall_score", 0) >= min_score
    ][:top_k]
    
    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_candidates": len(candidates),
        "rankings": filtered_rankings,
        "summary": ranking_result.summary
    }


@router.get("/report/{job_id}/{candidate_id}")
async def get_candidate_report(job_id: str, candidate_id: str):
    """Generate a detailed candidate report for a job."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = candidates_db.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get match result
    match_result = await matching_agent.execute(candidate, job)
    
    # Create ranking data
    ranking_data = {
        "rank": 1,
        "recommendation": "highly_recommended" if match_result.overall_score >= 80 else 
                         "recommended" if match_result.overall_score >= 65 else
                         "consider" if match_result.overall_score >= 50 else "not_recommended"
    }
    
    # Generate report
    report = await ranking_agent.generate_candidate_report(
        candidate, match_result, ranking_data, job
    )
    
    return {
        "job_id": job_id,
        "candidate_id": candidate_id,
        "report": report,
        "match_result": match_result.model_dump()
    }


# ==================== Search Endpoints ====================

@router.get("/search/candidates")
async def search_candidates(
    query: str = Query(..., min_length=3),
    top_k: int = Query(10, ge=1, le=50)
):
    """Search candidates using semantic search."""
    results = await vector_store.search_candidates(query, n_results=top_k)
    
    # Enrich with candidate data
    enriched = []
    for r in results:
        candidate = candidates_db.get(r["id"])
        if candidate:
            enriched.append({
                "id": r["id"],
                "name": candidate.resume_data.name,
                "skills": candidate.resume_data.skills[:10],
                "experience_years": candidate.resume_data.get_total_experience_years(),
                "relevance_score": 1 - r.get("distance", 0)
            })
    
    return {"query": query, "results": enriched}


@router.get("/search/jobs")
async def search_jobs(
    query: str = Query(..., min_length=3),
    top_k: int = Query(10, ge=1, le=50)
):
    """Search jobs using semantic search."""
    results = await vector_store.search_jobs(query, n_results=top_k)
    
    # Enrich with job data
    enriched = []
    for r in results:
        job = jobs_db.get(r["id"])
        if job:
            enriched.append({
                "id": r["id"],
                "title": job.title,
                "department": job.department,
                "location": job.location,
                "relevance_score": 1 - r.get("distance", 0)
            })
    
    return {"query": query, "results": enriched}


@router.get("/candidates/{candidate_id}/matching-jobs")
async def find_matching_jobs(
    candidate_id: str,
    top_k: int = Query(5, ge=1, le=20)
):
    """Find jobs that match a candidate's profile."""
    candidate = candidates_db.get(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    matching_jobs = await router_agent.find_jobs_for_candidate(candidate, top_k)
    
    # Enrich with job data
    enriched = []
    for j in matching_jobs:
        job = jobs_db.get(j["id"])
        if job:
            enriched.append({
                "id": j["id"],
                "title": job.title,
                "department": job.department,
                "match_score": j.get("rerank_score", 0)
            })
    
    return {"candidate_id": candidate_id, "matching_jobs": enriched}


@router.get("/jobs/{job_id}/matching-candidates")
async def find_matching_candidates(
    job_id: str,
    top_k: int = Query(10, ge=1, le=50)
):
    """Find candidates that match a job description."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    matching_candidates = await router_agent.find_candidates_for_job(job, top_k)
    
    # Enrich with candidate data
    enriched = []
    for c in matching_candidates:
        candidate = candidates_db.get(c["id"])
        if candidate:
            enriched.append({
                "id": c["id"],
                "name": candidate.resume_data.name,
                "skills": candidate.resume_data.skills[:10],
                "match_score": c.get("rerank_score", 0)
            })
    
    return {"job_id": job_id, "matching_candidates": enriched}


# ==================== Analytics Endpoints ====================

@router.get("/analytics/overview")
async def get_analytics_overview():
    """Get overview analytics."""
    total_candidates = len(candidates_db)
    total_jobs = len(jobs_db)
    active_jobs = sum(1 for j in jobs_db.values() if j.is_active)
    
    # Calculate average experience
    experiences = [c.resume_data.get_total_experience_years() for c in candidates_db.values()]
    avg_experience = sum(experiences) / len(experiences) if experiences else 0
    
    # Get skill distribution
    all_skills = []
    for c in candidates_db.values():
        all_skills.extend(c.resume_data.skills)
    
    skill_counts = {}
    for skill in all_skills:
        skill_lower = skill.lower()
        skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1
    
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "average_experience_years": round(avg_experience, 1),
        "top_skills": [{"skill": s[0], "count": s[1]} for s in top_skills]
    }
