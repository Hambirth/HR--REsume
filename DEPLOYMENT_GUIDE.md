# Docker Deployment Guide
## HR Resume Screening System

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Configuration](#configuration)
5. [Deployment Steps](#deployment-steps)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software

1. **Docker Desktop**
   - Windows: Download from https://www.docker.com/products/docker-desktop
   - Minimum version: 20.10+
   - Ensure WSL 2 is enabled (for Windows)

2. **Docker Compose**
   - Included with Docker Desktop
   - Minimum version: 2.0+

3. **Git** (for cloning repository)
   - Download from https://git-scm.com/

### System Requirements

- **RAM:** Minimum 8GB (16GB recommended)
- **Disk Space:** 10GB free space
- **CPU:** 2+ cores recommended
- **OS:** Windows 10/11, macOS, or Linux

---

## Quick Start

### 1. Clone or Navigate to Project

```bash
cd "c:\Users\Aron\Desktop\HR Screening"
```

### 2. Create Environment File

```bash
# Copy example environment file
copy .env.example .env

# Edit .env with your API key
notepad .env
```

### 3. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 4. Access Application

- **Frontend:** http://localhost
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Detailed Setup

### Step 1: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version 2.0.0 or higher

# Verify Docker is running
docker ps
# Should show empty list or running containers
```

### Step 2: Configure Environment Variables

Edit the `.env` file:

```bash
# UltraSafe API Configuration (REQUIRED)
USF_API_KEY=your_actual_api_key_here
USF_BASE_URL=https://api.us.inc/usf/v1/hiring

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

# Database Settings
CHROMA_PERSIST_DIR=/app/data/chroma_db

# Upload Settings
UPLOAD_DIR=/app/data/uploads
MAX_FILE_SIZE_MB=10

# Performance Settings (from load testing)
API_TIMEOUT=60
MAX_CONCURRENT_RANKINGS=3
UPLOAD_BATCH_SIZE=10
```

**Important:** Replace `your_actual_api_key_here` with your UltraSafe API key!

### Step 3: Review Docker Configuration

The project includes three Docker files:

1. **`Dockerfile`** - Backend (FastAPI)
2. **`Dockerfile.frontend`** - Frontend (React + Nginx)
3. **`docker-compose.yml`** - Orchestrates both services

---

## Configuration

### Docker Compose Services

#### Backend Service (API)
```yaml
api:
  - Port: 8000
  - Container: hr-screening-api
  - Health check: Every 30 seconds
  - Restart policy: unless-stopped
  - Data persistence: hr_data volume
```

#### Frontend Service
```yaml
frontend:
  - Port: 80 (HTTP)
  - Container: hr-screening-frontend
  - Depends on: API service
  - Web server: Nginx
  - Restart policy: unless-stopped
```

### Volumes

- **hr_data:** Persists uploaded resumes and ChromaDB data
- **Location:** Docker managed volume (survives container restarts)

### Networks

- **hr-network:** Bridge network for inter-service communication

---

## Deployment Steps

### Development Deployment

#### Step 1: Build Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api
docker-compose build frontend
```

**Expected Output:**
```
[+] Building 45.2s (15/15) FINISHED
 => [internal] load build definition
 => => transferring dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata
 => CACHED [1/8] FROM docker.io/library/python:3.11-slim
 => [2/8] WORKDIR /app
 => [3/8] COPY requirements.txt .
 => [4/8] RUN pip install...
 => [5/8] COPY . .
 => exporting to image
 => => naming to docker.io/library/hr-screening-api
```

#### Step 2: Start Services

```bash
# Start all services (foreground - see logs)
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Start specific service
docker-compose up api
```

**Expected Output:**
```
[+] Running 3/3
 ✔ Network hr-network          Created
 ✔ Container hr-screening-api  Started
 ✔ Container hr-screening-frontend  Started
```

#### Step 3: View Logs

```bash
# View all logs
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# View specific service logs
docker-compose logs api
docker-compose logs frontend

# Last 100 lines
docker-compose logs --tail=100
```

#### Step 4: Check Status

```bash
# List running containers
docker-compose ps

# Expected output:
NAME                    STATUS              PORTS
hr-screening-api        Up 2 minutes        0.0.0.0:8000->8000/tcp
hr-screening-frontend   Up 2 minutes        0.0.0.0:80->80/tcp
```

---

## Verification

### 1. Health Checks

#### Backend Health Check
```bash
# Using curl
curl http://localhost:8000/api/v1/health

# Expected response:
{"status":"healthy","timestamp":"2026-04-27T12:00:00"}
```

#### Frontend Health Check
```bash
# Open in browser
http://localhost

# Should see the HR Screening application
```

### 2. API Documentation

```bash
# Open Swagger UI
http://localhost:8000/docs

# Open ReDoc
http://localhost:8000/redoc
```

### 3. Test Upload

1. Open http://localhost
2. Click "Upload Resume"
3. Select a PDF or DOCX file
4. Verify upload succeeds
5. Check candidate appears in list

### 4. Test Ranking

1. Create a job description
2. Upload some resumes
3. Click "Find Best Candidates"
4. Verify rankings appear

---

## Common Commands

### Container Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Debugging

```bash
# Execute command in running container
docker-compose exec api bash
docker-compose exec frontend sh

# View container details
docker inspect hr-screening-api

# View resource usage
docker stats

# View networks
docker network ls

# View volumes
docker volume ls
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Complete cleanup (CAUTION: removes all data)
docker-compose down -v --rmi all
```

---

## Troubleshooting

### Issue 1: Port Already in Use

**Error:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (Windows)
taskkill /PID <process_id> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Issue 2: Build Fails

**Error:**
```
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete successfully
```

**Solution:**
```bash
# Clear Docker cache
docker-compose build --no-cache

# Check requirements.txt exists
dir requirements.txt

# Verify internet connection
ping google.com
```

### Issue 3: Container Exits Immediately

**Check logs:**
```bash
docker-compose logs api
```

**Common causes:**
- Missing environment variables
- Invalid API key
- Port conflict
- Missing dependencies

**Solution:**
```bash
# Verify .env file exists
type .env

# Check environment variables loaded
docker-compose config

# Rebuild with no cache
docker-compose up --build --force-recreate
```

### Issue 4: Frontend Can't Connect to Backend

**Error in browser console:**
```
Failed to fetch: http://localhost:8000/api/v1/candidates
```

**Solution:**

1. **Check API is running:**
```bash
curl http://localhost:8000/api/v1/health
```

2. **Check network:**
```bash
docker network inspect hr-network
```

3. **Verify nginx configuration:**
```bash
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

4. **Check CORS settings in backend:**
```python
# app/main.py should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 5: Data Not Persisting

**Problem:** Uploaded resumes disappear after restart

**Solution:**
```bash
# Check volume exists
docker volume ls | findstr hr_data

# Inspect volume
docker volume inspect hr_data

# Ensure volume is mounted in docker-compose.yml
volumes:
  - hr_data:/app/data
```

### Issue 6: Out of Memory

**Error:**
```
Container killed: OOMKilled
```

**Solution:**

1. **Increase Docker memory:**
   - Docker Desktop → Settings → Resources
   - Increase Memory to 8GB+

2. **Check memory usage:**
```bash
docker stats
```

3. **Optimize application:**
   - Reduce batch sizes
   - Clear cache periodically
   - Limit concurrent operations

---

## Production Deployment

### Security Checklist

- [ ] Change default API keys
- [ ] Set `DEBUG=false`
- [ ] Use HTTPS (SSL certificates)
- [ ] Enable firewall rules
- [ ] Set up authentication
- [ ] Configure CORS properly
- [ ] Use secrets management
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hr-screening-api-prod
    ports:
      - "8000:8000"
    environment:
      - USF_API_KEY=${USF_API_KEY}
      - USF_BASE_URL=${USF_BASE_URL}
      - DEBUG=false
      - MAX_CONCURRENT_RANKINGS=5  # Increase for production
      - UPLOAD_BATCH_SIZE=20
    volumes:
      - hr_data:/app/data
    restart: always  # Always restart in production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - hr-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: hr-screening-frontend-prod
    ports:
      - "80:80"
      - "443:443"  # HTTPS
    depends_on:
      api:
        condition: service_healthy
    restart: always
    networks:
      - hr-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  hr_data:
    driver: local

networks:
  hr-network:
    driver: bridge
```

### HTTPS Setup (Optional but Recommended)

1. **Get SSL Certificate:**
   - Use Let's Encrypt (free)
   - Or purchase from certificate authority

2. **Update nginx.conf:**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

3. **Mount certificates:**
```yaml
volumes:
  - ./ssl:/etc/nginx/ssl:ro
```

### Monitoring Setup

**Add monitoring service:**

```yaml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - hr-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - hr-network
```

### Backup Strategy

```bash
# Backup data volume
docker run --rm -v hr_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/hr_data_backup_$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm -v hr_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/hr_data_backup_20260427.tar.gz -C /
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Docker and Docker Compose installed
- [ ] `.env` file configured with valid API key
- [ ] All dependencies in `requirements.txt`
- [ ] Frontend built successfully locally
- [ ] Backend runs without errors locally
- [ ] Load testing completed
- [ ] Documentation updated

### Deployment

- [ ] Build Docker images successfully
- [ ] Start containers without errors
- [ ] Health checks passing
- [ ] Frontend accessible at http://localhost
- [ ] Backend API accessible at http://localhost:8000
- [ ] API documentation accessible
- [ ] Test file upload
- [ ] Test job creation
- [ ] Test candidate ranking
- [ ] Verify data persistence

### Post-Deployment

- [ ] Monitor logs for errors
- [ ] Check resource usage (CPU, memory)
- [ ] Verify backups working
- [ ] Test from different devices
- [ ] Collect user feedback
- [ ] Document any issues
- [ ] Plan next iteration

---

## Performance Tuning

### Based on Load Testing Results

From our load testing, we know the system can handle:
- 100 concurrent uploads
- 20-30 concurrent users
- 84 resumes per minute

**Recommended Production Settings:**

```bash
# .env for production
MAX_CONCURRENT_RANKINGS=5  # Increase from 3
UPLOAD_BATCH_SIZE=20       # Increase from 10
API_TIMEOUT=120            # Increase from 60

# For larger servers
MAX_CONCURRENT_RANKINGS=10
UPLOAD_BATCH_SIZE=50
```

### Docker Resource Limits

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

---

## Quick Reference

### Essential Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f

# Status
docker-compose ps

# Rebuild
docker-compose up -d --build

# Clean everything
docker-compose down -v --rmi all
```

### URLs

- Frontend: http://localhost
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

### Important Files

- `docker-compose.yml` - Service orchestration
- `Dockerfile` - Backend image
- `Dockerfile.frontend` - Frontend image
- `nginx.conf` - Web server config
- `.env` - Environment variables
- `requirements.txt` - Python dependencies
- `frontend/package.json` - Node dependencies

---

## Support

### Getting Help

1. **Check logs first:**
   ```bash
   docker-compose logs -f
   ```

2. **Verify configuration:**
   ```bash
   docker-compose config
   ```

3. **Check Docker status:**
   ```bash
   docker ps -a
   docker volume ls
   docker network ls
   ```

4. **Review documentation:**
   - This deployment guide
   - Load testing documentation
   - README.md

---

## Next Steps

After successful deployment:

1. ✅ **Test all features** thoroughly
2. ✅ **Set up monitoring** (Prometheus + Grafana)
3. ✅ **Configure backups** (automated daily)
4. ✅ **Enable HTTPS** (Let's Encrypt)
5. ✅ **Add authentication** (if required)
6. ✅ **Performance monitoring** (track metrics)
7. ✅ **User training** (document workflows)
8. ✅ **Feedback collection** (iterate and improve)

---

## Conclusion

Your HR Screening System is now ready for Docker deployment! 

**Key Achievements:**
- ✅ Multi-container architecture
- ✅ Data persistence
- ✅ Health monitoring
- ✅ Auto-restart on failure
- ✅ Production-ready configuration
- ✅ Load tested and optimized

**Deployment Status:** Ready to deploy! 🚀

---

**Last Updated:** April 27, 2026  
**Version:** 1.0  
**Maintainer:** Development Team
