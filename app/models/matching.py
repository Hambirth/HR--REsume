"""Matching and ranking result models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ScreeningResult(BaseModel):
    """Result from the screening agent."""
    candidate_id: str
    job_id: str
    passed: bool
    reasons: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    met_requirements: List[str] = Field(default_factory=list)
    screening_notes: Optional[str] = None
    screened_at: datetime = Field(default_factory=datetime.now)


class MatchResult(BaseModel):
    """Result from the matching agent."""
    candidate_id: str
    job_id: str
    
    # Scores (0-100)
    overall_score: float
    skill_score: float
    experience_score: float
    education_score: float
    semantic_similarity: float
    
    # Skill matching details
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    additional_skills: List[str] = Field(default_factory=list)
    
    # Experience matching
    experience_years: float
    experience_gap: float  # Positive means candidate has more, negative means less
    
    # AI-generated insights
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    
    matched_at: datetime = Field(default_factory=datetime.now)


class RankingResult(BaseModel):
    """Result from the ranking agent."""
    job_id: str
    rankings: List[Dict[str, Any]] = Field(default_factory=list)
    total_candidates: int = 0
    ranked_at: datetime = Field(default_factory=datetime.now)
    ranking_criteria: Dict[str, float] = Field(default_factory=dict)
    summary: Optional[str] = None


class CandidateRanking(BaseModel):
    """Individual candidate ranking within a job."""
    rank: int
    candidate_id: str
    candidate_name: Optional[str]
    overall_score: float
    skill_score: float
    experience_score: float
    education_score: float
    semantic_similarity: float
    recommendation: str  # highly_recommended, recommended, consider, not_recommended
    key_strengths: List[str] = Field(default_factory=list)
    key_concerns: List[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Complete pipeline result for a candidate-job pair."""
    candidate_id: str
    job_id: str
    screening: ScreeningResult
    matching: Optional[MatchResult] = None
    final_recommendation: str
    processed_at: datetime = Field(default_factory=datetime.now)
