# HR Resume Screening System - Technical Documentation

## For Team Presentation & Knowledge Transfer

---

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture Deep Dive](#2-architecture-deep-dive)
3. [Technology Stack](#3-technology-stack)
4. [Backend Components](#4-backend-components)
5. [Agent System](#5-agent-system)
6. [RAG Pipeline & Vector Database](#6-rag-pipeline--vector-database)
7. [UltraSafe API Integration](#7-ultrasafe-api-integration)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Data Flow & Sequence Diagrams](#9-data-flow--sequence-diagrams)
10. [Scoring Algorithm](#10-scoring-algorithm)
11. [API Endpoints](#11-api-endpoints)
12. [How to Run](#12-how-to-run)

---

## 1. System Overview

### What This System Does
This is an **AI-powered HR Resume Screening System** that:
- Parses resumes (PDF/DOCX) and extracts structured candidate information
- Manages job descriptions with skill requirements
- Uses **semantic similarity** to match candidates to jobs
- Ranks candidates with detailed scoring and reasoning
- Provides a modern web interface for HR teams

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                 │
│                         React + TailwindCSS (Port 3000)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ HTTP REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                                │
│                              (Port 8000)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API ROUTES (routes.py)                       │   │
│  │  /candidates/upload  /jobs  /rankings/{job_id}  /search/candidates   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌───────────────────────────────────┼───────────────────────────────────┐ │
│  │                          SERVICES LAYER                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │ Resume      │  │   USF       │  │   Vector    │  │    RAG      │   │ │
│  │  │ Parser      │  │   Client    │  │   Store     │  │  Pipeline   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                      │                                      │
│  ┌───────────────────────────────────┼───────────────────────────────────┐ │
│  │                           AGENT SYSTEM                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │ Router      │  │ Screening   │  │ Matching    │  │ Ranking     │   │ │
│  │  │ Agent       │  │ Agent       │  │ Agent       │  │ Agent       │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
           │  ChromaDB   │   │  UltraSafe  │   │    File     │
           │  (Vectors)  │   │     API     │   │   System    │
           └─────────────┘   └─────────────┘   └─────────────┘
```

---

## 2. Architecture Deep Dive

### 2.1 Request Flow Example: Upload Resume

```
1. User selects PDF file in React UI
2. React sends POST /api/v1/candidates/upload with FormData
3. FastAPI receives file, validates type and size
4. ResumeParser extracts text using PyMuPDF
5. USFClient sends text to UltraSafe Chat API for LLM extraction
6. Structured data (name, skills, experience) is extracted
7. Candidate object is created and stored in memory
8. RAGPipeline indexes candidate in ChromaDB with embeddings
9. Response sent back to React with candidate details
10. UI updates to show new candidate
```

### 2.2 Request Flow Example: Get Rankings

```
1. User selects job and clicks "Find Matches"
2. React sends GET /api/v1/rankings/{job_id}
3. FastAPI retrieves all candidates from database
4. MatchingAgent.batch_match() is called for all candidates
5. For each candidate:
   a. RAGPipeline.analyze_candidate_job_fit() calculates:
      - Skill score (required + preferred matching)
      - Experience score
      - Education score
      - Semantic similarity (via embeddings)
   b. Overall score is computed using weighted formula
6. RankingAgent sorts candidates by score
7. RankingAgent generates AI summary via UltraSafe Chat API
8. Response includes ranked candidates + reasoning + summary
9. React displays expandable cards with score breakdowns
```

---

## 3. Technology Stack

### Backend
| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Backend language | 3.11+ |
| **FastAPI** | REST API framework | 0.109.0 |
| **Uvicorn** | ASGI server | 0.27.0 |
| **Pydantic** | Data validation | 2.5.3 |
| **httpx** | Async HTTP client | 0.26.0 |

### Resume Parsing
| Technology | Purpose |
|------------|---------|
| **PyMuPDF (fitz)** | PDF text extraction |
| **python-docx** | DOCX text extraction |

### Vector Database & AI
| Technology | Purpose |
|------------|---------|
| **ChromaDB** | Vector database for semantic search |
| **UltraSafe API** | LLM chat, embeddings, reranking |
| **NumPy** | Cosine similarity calculations |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool & dev server |
| **TailwindCSS** | Styling |
| **Axios** | HTTP client |
| **Lucide React** | Icons |

---

## 4. Backend Components

### 4.1 File Structure
```
app/
├── __init__.py
├── main.py                 # FastAPI app entry point
├── config.py               # Environment configuration
│
├── api/
│   └── routes.py           # All REST API endpoints
│
├── models/
│   ├── candidate.py        # Candidate, ResumeData, Experience, Education
│   ├── job.py              # JobDescription, SkillRequirement
│   └── matching.py         # MatchResult, RankingResult, ScreeningResult
│
├── services/
│   ├── resume_parser.py    # PDF/DOCX parsing + text extraction
│   ├── usf_client.py       # UltraSafe API client
│   ├── vector_store.py     # ChromaDB operations
│   └── rag_pipeline.py     # Semantic indexing & matching
│
└── agents/
    ├── base_agent.py       # Base agent class
    ├── router_agent.py     # Workflow coordinator
    ├── screening_agent.py  # Minimum requirements filter
    ├── matching_agent.py   # Semantic similarity matching
    └── ranking_agent.py    # Scoring & ranking
```

### 4.2 Configuration (config.py)
```python
class Settings(BaseSettings):
    # UltraSafe API
    usf_api_key: str = "ec040bd9-b594-44bc-a196-1da99949a514"
    usf_base_url: str = "https://api.us.inc/usf/v1/hiring"
    
    # Model Names
    chat_model: str = "usf-mini"           # For LLM extraction
    embed_model: str = "usf1-embed"        # For embeddings (1024 dims)
    rerank_model: str = "usf1-rerank"      # For reranking
    
    # Storage
    chroma_persist_dir: str = "./data/chroma_db"
    upload_dir: str = "./data/uploads"
```

### 4.3 Data Models

#### Candidate Model
```python
class ResumeData(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    skills: List[str] = []
    education: List[Education] = []
    experience: List[Experience] = []
    raw_text: str = ""
    
    def get_total_experience_years(self) -> float:
        # Calculates total years from experience entries
```

#### Job Description Model
```python
class JobDescription(BaseModel):
    id: str
    title: str
    description: str
    required_skills: List[SkillRequirement]
    preferred_skills: List[SkillRequirement]
    min_experience_years: float
    required_education: Optional[str]
```

---

## 5. Agent System

### 5.1 Agent Architecture
The system uses a **multi-agent architecture** where each agent has a specific responsibility:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ROUTER AGENT                                     │
│                  (Orchestrates the entire workflow)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│  SCREENING AGENT    │   │   MATCHING AGENT    │   │   RANKING AGENT     │
│                     │   │                     │   │                     │
│ • Check min years   │   │ • Skill matching    │   │ • Sort by score     │
│ • Check required    │   │ • Semantic sim      │   │ • Categorize        │
│   skills            │   │ • Experience score  │   │ • Generate summary  │
│ • Check education   │   │ • Education score   │   │ • AI recommendations│
│                     │   │ • AI insights       │   │                     │
│ Output: PASS/FAIL   │   │ Output: MatchResult │   │ Output: RankingResult│
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

### 5.2 Router Agent (router_agent.py)
**Purpose:** Coordinates the entire screening pipeline

```python
async def execute(self, candidates, job, skip_screening, strict_screening):
    # Step 1: Screening (optional)
    if not skip_screening:
        screening_results = await self.screening_agent.batch_screen(candidates, job)
        passed_candidates = [c for c in candidates if passed_screening]
    
    # Step 2: Matching
    matching_results = await self.matching_agent.batch_match(passed_candidates, job)
    
    # Step 3: Ranking
    ranking_result = await self.ranking_agent.execute(matching_results, candidates_dict, job)
    
    return results
```

### 5.3 Screening Agent (screening_agent.py)
**Purpose:** Filter candidates by minimum requirements

**Checks:**
- Minimum years of experience
- Required skills presence
- Education level

**Output:** `ScreeningResult` with `passed: bool` and `reasons: List[str]`

### 5.4 Matching Agent (matching_agent.py)
**Purpose:** Detailed candidate-job matching using multiple signals

```python
async def execute(self, candidate, job) -> MatchResult:
    # Get comprehensive analysis
    analysis = await self.rag_pipeline.analyze_candidate_job_fit(candidate, job)
    
    # Generate AI insights
    insights = await self.rag_pipeline.generate_match_insights(candidate, job, analysis)
    
    return MatchResult(
        overall_score=analysis["overall_score"],
        skill_score=analysis["skill_score"],
        experience_score=analysis["experience_score"],
        education_score=analysis["education_score"],
        semantic_similarity=analysis["semantic_similarity"],
        strengths=insights.get("strengths", []),
        concerns=insights.get("concerns", [])
    )
```

### 5.5 Ranking Agent (ranking_agent.py)
**Purpose:** Final scoring, ranking, and report generation

**Responsibilities:**
- Sort candidates by overall score
- Categorize into: highly_recommended, recommended, consider, not_recommended
- Generate AI-powered summary using UltraSafe Chat API
- Create detailed candidate reports

---

## 6. RAG Pipeline & Vector Database

### 6.1 What is RAG?
**RAG (Retrieval-Augmented Generation)** combines:
1. **Retrieval:** Find relevant documents using semantic search
2. **Augmentation:** Use retrieved context to enhance AI responses
3. **Generation:** Generate insights based on retrieved data

### 6.2 Vector Store (ChromaDB)

ChromaDB stores three collections:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CHROMADB                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   candidates    │  │      jobs       │  │     skills      │              │
│  │                 │  │                 │  │                 │              │
│  │ ID: candidate_id│  │ ID: job_id      │  │ ID: skill_name  │              │
│  │ Text: profile   │  │ Text: job desc  │  │ Text: skill     │              │
│  │ Metadata: {...} │  │ Metadata: {...} │  │                 │              │
│  │ Embedding: [...]│  │ Embedding: [...]│  │ Embedding: [...]│              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Indexing Process

**When a resume is uploaded:**
```python
# 1. Create rich text representation
text = f"""
Name: {name}
Summary: {summary}
Skills: {skills}
Experience: {job_title} at {company} - {description}
Education: {degree} in {field} from {institution}
"""

# 2. Get embedding from UltraSafe API
embedding = await usf_client.get_embeddings([text])  # Returns 1024-dim vector

# 3. Store in ChromaDB
collection.add(
    ids=[candidate_id],
    documents=[text],
    embeddings=[embedding],
    metadatas=[{name, email, skills_count, experience_years}]
)
```

### 6.4 Semantic Similarity Calculation

```python
async def get_semantic_similarity(self, text1: str, text2: str) -> float:
    # 1. Get embeddings for both texts
    embeddings = await self.usf_client.get_embeddings([text1, text2])
    
    # 2. Calculate cosine similarity
    vec1 = np.array(embeddings[0])  # 1024-dimensional
    vec2 = np.array(embeddings[1])  # 1024-dimensional
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    similarity = dot_product / (norm1 * norm2)  # Range: -1 to 1, typically 0.5-0.9
    
    return similarity
```

**Why this matters:** 
- Traditional keyword matching: "Python" ≠ "Py" ≠ "python programming"
- Semantic matching: "Python developer" ≈ "programmer with Python experience" (high similarity)

---

## 7. UltraSafe API Integration

### 7.1 API Configuration
```
Base URL: https://api.us.inc/usf/v1/hiring
API Key: ec040bd9-b594-44bc-a196-1da99949a514 (via x-api-key header)
```

### 7.2 Three API Endpoints Used

#### 7.2.1 Chat Completions (`/chat/completions`)
**Model:** `usf-mini`
**Purpose:** LLM-powered text generation

**Used for:**
- Resume information extraction (name, skills, experience)
- Generating match insights (strengths, concerns)
- Creating ranking summaries

**Critical Parameter:** `web_search: true` (required for responses)

```python
payload = {
    "model": "usf-mini",
    "messages": [
        {"role": "system", "content": "Extract resume info..."},
        {"role": "user", "content": resume_text}
    ],
    "temperature": 0.1,
    "max_tokens": 2048,
    "web_search": True  # REQUIRED!
}
```

#### 7.2.2 Embeddings (`/embed/embeddings`)
**Model:** `usf1-embed`
**Output:** 1024-dimensional float vector

**Used for:**
- Indexing candidates and jobs in ChromaDB
- Calculating semantic similarity between texts

```python
payload = {
    "model": "usf1-embed",
    "input": "Python developer with 5 years experience..."
}
# Response: {"data": [{"embedding": [0.02, -0.06, 0.13, ...]}]}
```

#### 7.2.3 Reranking (`/embed/reranker`)
**Model:** `usf1-rerank`

**Used for:**
- Reranking search results by relevance
- Fine-tuning candidate rankings

```python
payload = {
    "model": "usf1-rerank",
    "query": "Python developer needed",
    "texts": ["Resume 1...", "Resume 2...", "Resume 3..."]
}
# Response: Sorted by relevance score
```

---

## 8. Frontend Architecture

### 8.1 Component Structure
```
frontend/src/
├── main.jsx          # React entry point
├── App.jsx           # Main component with all tabs
└── index.css         # TailwindCSS imports
```

### 8.2 App.jsx Components

```jsx
function App() {
  // State
  const [candidates, setCandidates] = useState([])
  const [jobs, setJobs] = useState([])
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  
  return (
    <>
      <Header />
      <TabNavigation />
      
      {activeTab === 'upload' && <UploadTab />}
      {activeTab === 'jobs' && <JobsTab />}
      {activeTab === 'match' && <MatchTab />}
      
      {selectedCandidate && <CandidateProfileModal />}
    </>
  )
}
```

### 8.3 Key Features

| Feature | Component | Description |
|---------|-----------|-------------|
| Multi-file upload | `UploadTab` | Drag & drop PDF/DOCX, progress indicator |
| Candidate list | `UploadTab` | Shows name, skills, experience, clickable for details |
| Job creation | `JobsTab` | Form with title, description, skills, experience |
| Candidate matching | `MatchTab` | Select job → Find matches → Expandable ranking cards |
| Profile modal | `CandidateProfileModal` | Full candidate details in overlay |
| Score breakdown | `MatchTab` (expanded) | Visual bars for skill/exp/edu/semantic scores |
| AI summary | `MatchTab` | Blue box with AI-generated analysis |

---

## 9. Data Flow & Sequence Diagrams

### 9.1 Resume Upload Sequence

```
User          React           FastAPI         ResumeParser      USF API       ChromaDB
 │              │                │                │                │              │
 │─ Select PDF ─►│                │                │                │              │
 │              │── POST /upload ─►│                │                │              │
 │              │                │── parse_resume ─►│                │              │
 │              │                │                │── extract_text ─►│              │
 │              │                │                │◄─ raw_text ─────│              │
 │              │                │                │                │              │
 │              │                │                │── POST /chat ───►│              │
 │              │                │                │  (LLM extract)   │              │
 │              │                │                │◄─ structured ────│              │
 │              │                │◄── ResumeData ──│                │              │
 │              │                │                                   │              │
 │              │                │── index_candidate ────────────────►│              │
 │              │                │   (with embedding)                 │              │
 │              │                │◄── success ───────────────────────│              │
 │              │◄── Candidate ──│                                                  │
 │◄── Show card ─│                                                                  │
```

### 9.2 Ranking Sequence

```
User          React           FastAPI         MatchingAgent     RAG Pipeline    USF API
 │              │                │                │                │              │
 │─ Click Match ─►│                │                │                │              │
 │              │── GET /rankings ─►│                │                │              │
 │              │                │                │                │              │
 │              │                │  for each candidate:             │              │
 │              │                │── analyze_fit ──►│                │              │
 │              │                │                │── get_similarity─►│              │
 │              │                │                │                │── embeddings ─►│
 │              │                │                │                │◄──────────────│
 │              │                │                │◄─ scores ───────│              │
 │              │                │◄── MatchResult ─│                │              │
 │              │                │                                                  │
 │              │                │── generate_summary ─────────────────────────────►│
 │              │                │◄── AI text ─────────────────────────────────────│
 │              │◄── Rankings ───│                                                  │
 │◄── Display ───│                                                                  │
```

---

## 10. Scoring Algorithm

### 10.1 Overall Score Formula

```
OVERALL_SCORE = (SKILL × 0.4) + (EXPERIENCE × 0.3) + (EDUCATION × 0.3) + (SEMANTIC × 0.2)

Maximum possible: ~120 (normalized to 100 scale in some displays)
```

### 10.2 Skill Score (0-100)

```python
def calculate_skill_score(candidate_skills, required_skills, preferred_skills):
    # Match required skills (70% weight)
    required_matched = count_matches(candidate_skills, required_skills)
    required_score = (required_matched / len(required_skills)) * 70
    
    # Match preferred skills (30% weight)
    preferred_matched = count_matches(candidate_skills, preferred_skills)
    preferred_score = (preferred_matched / len(preferred_skills)) * 30
    
    return required_score + preferred_score

# Example: 3/5 required + 2/3 preferred = (0.6 × 70) + (0.67 × 30) = 62
```

### 10.3 Experience Score (0-100)

```python
def calculate_experience_score(candidate_years, required_years):
    if candidate_years >= required_years:
        # Bonus for extra experience (max 100)
        excess = candidate_years - required_years
        return min(100, 80 + (excess * 5))
    else:
        # Partial credit
        ratio = candidate_years / required_years
        return max(30, ratio * 80)

# Example: 5 years (req 3) = 80 + (2 × 5) = 90
# Example: 2 years (req 5) = (2/5) × 80 = 32 → 32
```

### 10.4 Education Score (0-100)

```python
EDUCATION_SCORES = {
    "phd": 100,
    "doctorate": 100,
    "master": 90,
    "mba": 90,
    "bachelor": 80,
    "associate": 60,
    "other": 50
}
```

### 10.5 Semantic Similarity (0-1)

```python
# Cosine similarity between candidate profile embedding and job description embedding
# Higher = more semantically similar content
# Typical range: 0.5 - 0.8 for related content
```

### 10.6 Recommendation Categories

| Score Range | Category | Meaning |
|-------------|----------|---------|
| ≥80 | `highly_recommended` | Strong match, proceed to interview |
| ≥65 | `recommended` | Good match, consider for interview |
| ≥50 | `consider` | Moderate match, review requirements |
| <50 | `not_recommended` | Significant gaps |

---

## 11. API Endpoints

### Candidates
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/candidates/upload` | Upload single resume |
| `POST` | `/api/v1/candidates/upload/bulk` | Upload multiple resumes |
| `GET` | `/api/v1/candidates` | List all candidates |
| `GET` | `/api/v1/candidates/{id}` | Get candidate details |
| `DELETE` | `/api/v1/candidates/{id}` | Delete candidate |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/jobs` | Create job description |
| `GET` | `/api/v1/jobs` | List all jobs |
| `GET` | `/api/v1/jobs/{id}` | Get job details |
| `PUT` | `/api/v1/jobs/{id}` | Update job |
| `DELETE` | `/api/v1/jobs/{id}` | Delete job |

### Matching & Ranking
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/screen/{job_id}/{candidate_id}` | Screen single candidate |
| `POST` | `/api/v1/match/{job_id}/{candidate_id}` | Match single candidate |
| `GET` | `/api/v1/rankings/{job_id}` | Get ranked candidates for job |
| `GET` | `/api/v1/report/{job_id}/{candidate_id}` | Generate candidate report |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/search/candidates?query=...` | Semantic search candidates |
| `GET` | `/api/v1/search/jobs?query=...` | Semantic search jobs |

---

## 12. How to Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup
```bash
# 1. Navigate to project
cd "HR Screening"

# 2. Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start backend server
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
# 1. Navigate to frontend
cd "HR Screening/frontend"

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

### Access URLs
| Service | URL |
|---------|-----|
| React Frontend | http://localhost:3000 |
| FastAPI Backend | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Summary

This HR Resume Screening System demonstrates:

1. **Modern Python Backend** with FastAPI, async/await, and Pydantic models
2. **Multi-Agent Architecture** for modular, maintainable workflow processing
3. **RAG Pipeline** combining vector search with LLM-powered analysis
4. **Semantic Matching** using 1024-dimensional embeddings for intelligent similarity
5. **External API Integration** with proper error handling and response parsing
6. **React Frontend** with modern UI/UX patterns

The system successfully transforms unstructured resumes into structured data, matches candidates to jobs using both traditional skill matching and AI-powered semantic understanding, and provides HR teams with actionable rankings and insights.

---

*Document generated for team knowledge transfer - April 2026*
