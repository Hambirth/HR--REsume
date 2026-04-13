# HR Resume Screening System - Complete Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REACT FRONTEND (Port 3000)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │ Upload Tab   │  │  Jobs Tab    │  │  Match Tab   │                       │
│  │ - Multi-file │  │ - Create job │  │ - Select job │                       │
│  │ - PDF/DOCX   │  │ - Set skills │  │ - View ranks │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP API Calls
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND (Port 8000)                          │
│                                                                             │
│  Endpoints:                                                                 │
│  POST /api/v1/candidates/upload  → Upload & parse resume                    │
│  GET  /api/v1/candidates         → List all candidates                      │
│  POST /api/v1/jobs               → Create job description                   │
│  GET  /api/v1/jobs               → List all jobs                            │
│  GET  /api/v1/rankings/{job_id}  → Get ranked candidates for job            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   SERVICES  │ │   AGENTS    │ │  ULTRASAFE  │
            │             │ │             │ │     API     │
            └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 1. RESUME PROCESSING WORKFLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESUME UPLOAD FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

User uploads PDF/DOCX
        │
        ▼
┌─────────────────┐
│  ResumeParser   │ (app/services/resume_parser.py)
├─────────────────┤
│ 1. Extract text │───▶ PyMuPDF (PDF) or python-docx (DOCX)
│ 2. Clean text   │───▶ Remove special chars, normalize whitespace
│ 3. LLM Extract  │───▶ UltraSafe API (usf-mini + web_search:true)
│ 4. Basic Extract│───▶ Regex fallback for name/email/phone/skills
│ 5. Experience   │───▶ Parse "X years" or date ranges (2019-Present)
│ 6. Education    │───▶ Detect Bachelor's/Master's/PhD
└─────────────────┘
        │
        ▼
┌─────────────────┐
│   ResumeData    │ (app/models/candidate.py)
├─────────────────┤
│ - name          │
│ - email         │
│ - phone         │
│ - skills[]      │
│ - experience[]  │ ──▶ duration_months calculated
│ - education[]   │ ──▶ degree, field, institution
│ - raw_text      │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  RAG Pipeline   │ (app/services/rag_pipeline.py)
├─────────────────┤
│ index_candidate │───▶ Store in ChromaDB with embeddings
└─────────────────┘
```

---

## 2. JOB DESCRIPTION MANAGEMENT

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JOB CREATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

User creates job
        │
        ▼
┌─────────────────┐
│ JobDescription  │ (app/models/job.py)
├─────────────────┤
│ - title         │
│ - description   │
│ - required_skills[]    │ ──▶ Must-have skills (70% weight)
│ - preferred_skills[]   │ ──▶ Nice-to-have (30% weight)
│ - min_experience_years │
│ - required_education   │
│ - skill_weight: 0.4    │ ──▶ Configurable scoring weights
│ - experience_weight: 0.3│
│ - education_weight: 0.3 │
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  RAG Pipeline   │
├─────────────────┤
│   index_job     │───▶ Store in ChromaDB for semantic search
└─────────────────┘
```

---

## 3. AGENT SYSTEM WORKFLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CANDIDATE RANKING FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

GET /rankings/{job_id}
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ROUTER AGENT                                       │
│                    (app/agents/router_agent.py)                             │
│              Coordinates the entire screening workflow                      │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        │ Step 1: Filter
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCREENING AGENT                                      │
│                   (app/agents/screening_agent.py)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Filters candidates based on minimum requirements:                           │
│ - Minimum experience years                                                  │
│ - Required skills presence                                                  │
│ - Education level                                                           │
│ - strict_mode: true = all requirements, false = partial match              │
│                                                                             │
│ Output: List of qualified candidates                                        │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        │ Step 2: Match
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MATCHING AGENT                                       │
│                   (app/agents/matching_agent.py)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Performs detailed candidate-job matching:                                   │
│                                                                             │
│ Uses RAG Pipeline to calculate:                                             │
│ ┌─────────────────────────────────────────────────────────────────────┐     │
│ │ SKILL SCORE (40% weight)                                            │     │
│ │ - matched_required / total_required × 70                            │     │
│ │ - matched_preferred / total_preferred × 30                          │     │
│ └─────────────────────────────────────────────────────────────────────┘     │
│ ┌─────────────────────────────────────────────────────────────────────┐     │
│ │ EXPERIENCE SCORE (30% weight)                                       │     │
│ │ - Meets requirement: 80-100                                         │     │
│ │ - Below requirement: partial credit (ratio × 80)                    │     │
│ └─────────────────────────────────────────────────────────────────────┘     │
│ ┌─────────────────────────────────────────────────────────────────────┐     │
│ │ EDUCATION SCORE (30% weight)                                        │     │
│ │ - PhD: 100, Master's: 90, Bachelor's: 80                            │     │
│ └─────────────────────────────────────────────────────────────────────┘     │
│ ┌─────────────────────────────────────────────────────────────────────┐     │
│ │ SEMANTIC SIMILARITY (20% bonus)                                     │     │
│ │ - Cosine similarity of embeddings (usf1-embed, 1024-dim)            │     │
│ │ - Compares candidate profile text vs job description text           │     │
│ └─────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│ Output: MatchResult per candidate                                           │
└─────────────────────────────────────────────────────────────────────────────┘
        │
        │ Step 3: Rank
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RANKING AGENT                                        │
│                   (app/agents/ranking_agent.py)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Final scoring and ranking:                                                  │
│                                                                             │
│ OVERALL_SCORE = skill_score × 0.4                                           │
│               + experience_score × 0.3                                      │
│               + education_score × 0.3                                       │
│               + semantic_similarity × 100 × 0.2                             │
│                                                                             │
│ RECOMMENDATION:                                                             │
│ - ≥80 + no missing required skills = "highly_recommended"                   │
│ - ≥70 or (≥60 + ≤1 missing skill) = "recommended"                           │
│ - ≥50 = "consider"                                                          │
│ - <50 = "not_recommended"                                                   │
│                                                                             │
│ Output: RankingResult with sorted candidates + AI summary                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. RAG PIPELINE & VECTOR DATABASE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAG PIPELINE                                      │
│                    (app/services/rag_pipeline.py)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ index_candidate │       │    index_job    │       │ analyze_fit     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ Create text:    │       │ Create text:    │       │ Calculate:      │
│ - Name          │       │ - Title         │       │ - Skill match   │
│ - Skills        │       │ - Description   │       │ - Exp match     │
│ - Experience    │       │ - Required      │       │ - Edu match     │
│ - Education     │       │ - Preferred     │       │ - Semantic sim  │
│ - Raw text      │       │                 │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VECTOR STORE                                       │
│                    (app/services/vector_store.py)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ChromaDB Collections:                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                          │
│  │ candidates  │  │    jobs     │  │   skills    │                          │
│  └─────────────┘  └─────────────┘  └─────────────┘                          │
│                                                                             │
│  Semantic Similarity:                                                       │
│  - Get embeddings via USF API (usf1-embed, 1024 dimensions)                 │
│  - Calculate cosine similarity between vectors                              │
│  - Fallback to keyword overlap if API fails                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. ULTRASAFE API INTEGRATION

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ULTRASAFE API CLIENT                                │
│                      (app/services/usf_client.py)                           │
└─────────────────────────────────────────────────────────────────────────────┘

Base URL: https://api.us.inc/usf/v1/hiring
API Key:  ec040bd9-b594-44bc-a196-1da99949a514

┌─────────────────────────────────────────────────────────────────────────────┐
│ CHAT COMPLETIONS                                                            │
│ POST /chat/completions                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Model: usf-mini                                                             │
│ Key Parameter: web_search: true (REQUIRED for responses)                    │
│                                                                             │
│ Used for:                                                                   │
│ - Resume info extraction (name, skills, experience)                         │
│ - Match insights generation (strengths, concerns)                           │
│ - Ranking summary generation                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ EMBEDDINGS                                                                  │
│ POST /embed/embeddings                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Model: usf1-embed                                                           │
│ Output: 1024-dimensional vectors                                            │
│                                                                             │
│ Used for:                                                                   │
│ - Semantic similarity between candidate & job                               │
│ - Vector search in ChromaDB                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ RERANK                                                                      │
│ POST /embed/reranker                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Model: usf1-rerank                                                          │
│                                                                             │
│ Used for:                                                                   │
│ - Reranking search results                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE DATA FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   USER ACTION   │
                    └─────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   UPLOAD    │     │ CREATE JOB  │     │ FIND MATCH  │
│   RESUME    │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Parse PDF/  │     │ Store job   │     │ Get all     │
│ DOCX text   │     │ description │     │ candidates  │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │                   │
        ▼                   ▼                   │
┌─────────────┐     ┌─────────────┐             │
│ LLM Extract │     │ Index in    │             │
│ + Fallback  │     │ ChromaDB    │             │
└─────────────┘     └─────────────┘             │
        │                   │                   │
        ▼                   │                   │
┌─────────────┐             │                   │
│ Create      │             │                   │
│ Candidate   │─────────────┘                   │
└─────────────┘                                 │
        │                                       │
        ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│ Index in    │                         │ Screening   │
│ ChromaDB    │                         │ Agent       │
└─────────────┘                         └─────────────┘
        │                                       │
        │                                       ▼
        │                               ┌─────────────┐
        │                               │ Matching    │
        │                               │ Agent       │
        │                               └─────────────┘
        │                                       │
        │                                       ▼
        │                               ┌─────────────┐
        │                               │ Ranking     │
        │                               │ Agent       │
        │                               └─────────────┘
        │                                       │
        │                                       ▼
        │                               ┌─────────────┐
        └──────────────────────────────▶│  RESPONSE   │
                                        │  Rankings   │
                                        │  + Scores   │
                                        │  + Summary  │
                                        └─────────────┘
```

---

## 7. FILE STRUCTURE

```
HR Screening/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Settings (API keys, models)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # REST API endpoints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── candidate.py        # ResumeData, Candidate, Experience, Education
│   │   ├── job.py              # JobDescription
│   │   └── matching.py         # MatchResult, RankingResult, CandidateRanking
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── usf_client.py       # UltraSafe API client
│   │   ├── resume_parser.py    # PDF/DOCX parsing + extraction
│   │   ├── vector_store.py     # ChromaDB operations
│   │   └── rag_pipeline.py     # Indexing + semantic matching
│   │
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py       # Base agent class
│       ├── screening_agent.py  # Filter by requirements
│       ├── matching_agent.py   # Semantic similarity matching
│       ├── ranking_agent.py    # Score and rank
│       └── router_agent.py     # Workflow coordinator
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # React app with 3 tabs
│   │   ├── main.jsx            # Entry point
│   │   └── index.css           # TailwindCSS
│   ├── package.json
│   ├── vite.config.js          # Proxy to backend
│   └── tailwind.config.js
│
├── data/
│   ├── uploads/                # Uploaded resume files
│   └── chroma_db/              # Vector database storage
│
├── mock_resumes/               # Test PDF resumes
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## 8. SCORING FORMULA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCORING BREAKDOWN                                   │
└─────────────────────────────────────────────────────────────────────────────┘

OVERALL_SCORE = (SKILL × 0.4) + (EXPERIENCE × 0.3) + (EDUCATION × 0.3) + (SEMANTIC × 0.2)

┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL SCORE (0-100)                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ = (matched_required / total_required) × 70                                  │
│ + (matched_preferred / total_preferred) × 30                                │
│                                                                             │
│ Example: 3/5 required + 2/3 preferred = (0.6 × 70) + (0.67 × 30) = 62       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ EXPERIENCE SCORE (0-100)                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ If candidate_years >= required_years:                                       │
│   score = 80 + (excess_years × 5), max 100                                  │
│ Else:                                                                       │
│   score = (candidate_years / required_years) × 80, min 30                   │
│                                                                             │
│ Example: 5 years (req 3) = 80 + (2 × 5) = 90                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ EDUCATION SCORE (0-100)                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ PhD/Doctorate = 100                                                         │
│ Master's/MBA  = 90                                                          │
│ Bachelor's    = 80                                                          │
│ Other/None    = 50                                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ SEMANTIC SIMILARITY (0-1)                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ = cosine_similarity(candidate_embedding, job_embedding)                     │
│                                                                             │
│ Embeddings: 1024-dimensional vectors from usf1-embed                        │
│ Fallback: Keyword overlap (Jaccard + overlap coefficient)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. API ENDPOINTS

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/candidates/upload` | Upload resume file |
| GET | `/api/v1/candidates` | List all candidates |
| GET | `/api/v1/candidates/{id}` | Get candidate details |
| DELETE | `/api/v1/candidates/{id}` | Delete candidate |
| POST | `/api/v1/jobs` | Create job description |
| GET | `/api/v1/jobs` | List all jobs |
| GET | `/api/v1/jobs/{id}` | Get job details |
| DELETE | `/api/v1/jobs/{id}` | Delete job |
| GET | `/api/v1/rankings/{job_id}` | Get ranked candidates |

---

## 10. RUNNING THE SYSTEM

```bash
# Terminal 1: Start Backend
cd "HR Screening"
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd "HR Screening/frontend"
npm run dev

# Access
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:3000
# API Docs:    http://localhost:8000/docs
```

---

## Summary

**Everything is integrated and working:**
1. ✅ Resume parsing extracts all candidate info
2. ✅ Job descriptions with configurable weights
3. ✅ 4-agent system coordinates the workflow
4. ✅ RAG pipeline with real embeddings (usf1-embed)
5. ✅ Semantic similarity scoring
6. ✅ React UI for all operations
7. ✅ UltraSafe API integration (chat + embeddings)
