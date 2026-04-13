# HR Resume Screening & Matching Pipeline

An AI-powered HR system that screens resumes, matches candidates to job descriptions, and ranks applicants based on fit using semantic search and RAG (Retrieval-Augmented Generation).

## 🏗️ Architecture

```
Resume Upload → Resume Parser → Router Agent → [Screening Agent / Matching Agent / Ranking Agent]
                                                              ↓
                                                       RAG Pipeline (Job Descriptions + Skills DB)
                                                              ↓
                                                      Candidate Ranking & Report
```

## ✨ Features

- **Resume Parsing**: Parse PDF and DOCX resumes with AI-powered extraction
- **Job Description Management**: Create and manage job postings with skill requirements
- **Multi-Agent Screening Pipeline**:
  - **Screening Agent**: Filter candidates based on minimum requirements
  - **Matching Agent**: Semantic similarity matching between resumes and jobs
  - **Ranking Agent**: Score and rank candidates with detailed reasoning
  - **Router Agent**: Coordinate the entire workflow
- **RAG Pipeline**: Vector database with ChromaDB for semantic search
- **Semantic Matching**: Use embeddings for intelligent skill and experience matching
- **Candidate Reports**: Generate detailed evaluation reports
- **Web Interface**: Modern Streamlit dashboard

## 🛠️ Technology Stack

- **Python 3.11+**
- **FastAPI** - Backend REST API
- **Streamlit** - Web Interface
- **ChromaDB** - Vector Database
- **PyMuPDF & python-docx** - Resume Parsing
- **UltraSafe APIs** - LLM, Embeddings, and Reranking

## 📋 Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd "HR Screening"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is pre-configured with the UltraSafe API key:

```env
USF_API_KEY=ec040bd9-b594-44bc-a196-1da99949a514
USF_BASE_URL=https://api.us.inc/usf/v1/hiring
```

### 3. Run the Application

**Start the FastAPI Backend:**
```bash
python run_api.py
```
The API will be available at `http://localhost:8000`

**Start the Streamlit Frontend (in a new terminal):**
```bash
python run_streamlit.py
# Or directly:
streamlit run streamlit_app.py
```
The web interface will be available at `http://localhost:8501`

## 📖 API Documentation

Once the API is running, access the interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/candidates/upload` | POST | Upload and parse a resume |
| `/api/v1/candidates/upload/bulk` | POST | Upload multiple resumes |
| `/api/v1/candidates` | GET | List all candidates |
| `/api/v1/jobs` | POST | Create a job description |
| `/api/v1/jobs` | GET | List all jobs |
| `/api/v1/pipeline/{job_id}` | POST | Run full screening pipeline |
| `/api/v1/screen/{job_id}/{candidate_id}` | POST | Screen a candidate |
| `/api/v1/match/{job_id}/{candidate_id}` | POST | Match candidate to job |
| `/api/v1/rankings/{job_id}` | GET | Get candidate rankings |
| `/api/v1/report/{job_id}/{candidate_id}` | GET | Generate candidate report |

## 🔧 Project Structure

```
HR Screening/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── main.py                # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API endpoints
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py      # Base agent class
│   │   ├── screening_agent.py # Initial candidate filtering
│   │   ├── matching_agent.py  # Semantic matching
│   │   ├── ranking_agent.py   # Candidate ranking
│   │   └── router_agent.py    # Workflow coordination
│   ├── models/
│   │   ├── __init__.py
│   │   ├── candidate.py       # Candidate data models
│   │   ├── job.py             # Job description models
│   │   └── matching.py        # Matching result models
│   └── services/
│       ├── __init__.py
│       ├── usf_client.py      # UltraSafe API client
│       ├── resume_parser.py   # PDF/DOCX parsing
│       ├── vector_store.py    # ChromaDB operations
│       └── rag_pipeline.py    # RAG implementation
├── data/
│   ├── uploads/               # Uploaded resumes
│   └── chroma_db/             # Vector database
├── streamlit_app.py           # Streamlit web interface
├── run_api.py                 # API server runner
├── run_streamlit.py           # Streamlit runner
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── .env.example               # Example environment file
├── .gitignore
└── README.md
```

## 🎯 Usage Guide

### 1. Upload Resumes

Upload candidate resumes through the web interface or API:

```python
import requests

# Upload a resume
with open("resume.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/candidates/upload",
        files={"file": f}
    )
print(response.json())
```

### 2. Create Job Descriptions

Create job postings with required skills and qualifications:

```python
job_data = {
    "title": "Senior Software Engineer",
    "department": "Engineering",
    "description": "We are looking for an experienced software engineer...",
    "required_skills": ["Python", "AWS", "Docker", "PostgreSQL"],
    "preferred_skills": ["Kubernetes", "GraphQL"],
    "min_experience_years": 5,
    "required_education": "Bachelor's in Computer Science"
}

response = requests.post(
    "http://localhost:8000/api/v1/jobs",
    json=job_data
)
```

### 3. Run Screening Pipeline

Execute the full screening pipeline for a job:

```python
# Run pipeline for all candidates
response = requests.post(
    "http://localhost:8000/api/v1/pipeline/{job_id}",
    params={"skip_screening": False, "strict_screening": False}
)
results = response.json()

# View rankings
print(results["summary"])
print(results["ranking_result"]["rankings"])
```

### 4. Generate Reports

Get detailed evaluation reports:

```python
response = requests.get(
    f"http://localhost:8000/api/v1/report/{job_id}/{candidate_id}"
)
print(response.json()["report"])
```

## 🔌 UltraSafe API Integration

This project uses UltraSafe APIs for:

- **Chat Completions** (`/chat/completions`): Resume parsing and analysis
- **Embeddings** (`/embed/embeddings`): Semantic search and matching
- **Reranking** (`/embed/reranker`): Result reranking for better matches

API Documentation: https://documenter.getpostman.com/view/41719622/2sB2qXjN3a

## 📊 Scoring System

Candidates are scored on multiple dimensions:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Skills | 40% | Match between candidate and required skills |
| Experience | 30% | Years of experience vs requirements |
| Education | 20% | Education level and field match |
| Semantic | 10% | Overall semantic similarity |

### Recommendation Categories

- **Highly Recommended** (80+): Strong match, proceed to interview
- **Recommended** (65-79): Good match with minor gaps
- **Consider** (50-64): Moderate match, review carefully
- **Not Recommended** (<50): Significant gaps in requirements

## 🔒 Security Notes

- API key is stored in `.env` file (never commit to git)
- `.gitignore` excludes sensitive files
- Uploaded resumes are stored locally in `data/uploads/`

## � Docker Deployment

### Quick Start with Docker

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services
- **API**: http://localhost:8000
- **Frontend**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

### Docker Files
- `Dockerfile` - FastAPI backend
- `Dockerfile.streamlit` - Streamlit frontend
- `docker-compose.yml` - Orchestration
- `.dockerignore` - Build exclusions

### Environment Variables
Set in `docker-compose.yml` or pass via `.env`:
```env
USF_API_KEY=ec040bd9-b594-44bc-a196-1da99949a514
USF_BASE_URL=https://api.us.inc/usf/v1/hiring
```

---

## �🐛 Troubleshooting

### API Connection Issues
```bash
# Check if API is running
curl http://localhost:8000/api/v1/health
```

### ChromaDB Issues
```bash
# Clear the database
rm -rf data/chroma_db/
```

### Resume Parsing Issues
- Ensure the resume is a valid PDF or DOCX file
- Check file is not password protected
- Verify file size is under 10MB

## 📄 License

This project is for R&D purposes.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Submit a pull request

---

Built with ❤️ using UltraSafe APIs
