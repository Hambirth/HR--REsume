# 🔥 Load Testing Guide for HR Screening System

## Overview

This guide covers load testing the HR Screening system to measure:
- **Concurrent resume upload capacity**
- **API performance under load**
- **System bottlenecks and limits**
- **Response times and throughput**

---

## Prerequisites

1. **Backend must be running:**
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Install load testing tools:**
   ```bash
   pip install locust httpx aiohttp faker
   ```

3. **Have test resume files:**
   - Place PDF/DOCX files in `./data/uploads/`
   - At least 3-5 sample resumes recommended

---

## Method 1: Simple Python Load Test (Recommended for Beginners)

### Run the test:
```bash
python load_test.py
```

### What it tests:
- ✅ **5 concurrent resume uploads**
- ✅ **10 concurrent GET /candidates requests**
- ✅ **5 concurrent job creations**
- ✅ **3 concurrent ranking operations**

### Sample Output:
```
============================================================
TEST 1: Concurrent Resume Uploads (5 files)
============================================================
📁 Found 3 resume files
🚀 Uploading 5 resumes concurrently...

📊 RESULTS:
   Total uploads: 5
   ✅ Successful: 5
   ❌ Failed: 0
   ⏱️  Total time: 3.45s
   ⚡ Avg time per upload: 2.12s
   🚀 Throughput: 1.45 uploads/second

   📈 Upload Time Stats:
      Min: 1.89s
      Max: 2.34s
      Median: 2.10s
```

### Customize the test:
Edit `load_test.py` and change:
```python
await tester.test_concurrent_uploads(num_concurrent=10)  # Test 10 uploads
await tester.test_get_candidates(num_requests=50)        # Test 50 GET requests
await tester.test_ranking_under_load(num_concurrent=5)   # Test 5 rankings
```

---

## Method 2: Locust Load Testing (Advanced - Industry Standard)

### Step 1: Start Locust
```bash
locust -f locustfile.py --host=http://127.0.0.1:8000
```

### Step 2: Open Web UI
Open browser: **http://localhost:8089**

### Step 3: Configure Test
- **Number of users:** Start with 10, increase gradually
- **Spawn rate:** 1-2 users per second
- **Host:** http://127.0.0.1:8000

### Step 4: Start Test
Click "Start Swarming" and monitor:
- **RPS (Requests Per Second)**
- **Response times (50th, 95th, 99th percentile)**
- **Failure rate**

### Step 5: Analyze Results
Locust shows:
- 📊 Real-time charts
- 📈 Response time distribution
- ❌ Failed requests
- 📉 Performance degradation points

---

## Load Testing Scenarios

### Scenario 1: Normal Load (Baseline)
**Goal:** Measure normal performance

```bash
# Simple test
python load_test.py

# Locust test
locust -f locustfile.py --users 5 --spawn-rate 1 --run-time 2m
```

**Expected Results:**
- Upload time: 1-3 seconds per resume
- GET /candidates: < 100ms
- Ranking: 3-8 seconds for 10 candidates
- Success rate: 100%

---

### Scenario 2: Moderate Load
**Goal:** Test with realistic concurrent users

```bash
locust -f locustfile.py --users 20 --spawn-rate 2 --run-time 5m
```

**Expected Results:**
- Upload time: 2-5 seconds
- GET /candidates: < 200ms
- Ranking: 5-15 seconds
- Success rate: > 95%

---

### Scenario 3: Stress Test
**Goal:** Find breaking point

```bash
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m
```

**Watch for:**
- ⚠️ Response times > 10 seconds
- ❌ Failure rate > 5%
- 💥 Server errors (500)
- 🐌 System slowdown

---

### Scenario 4: Spike Test
**Goal:** Test sudden traffic surge

```bash
locust -f locustfile.py --users 100 --spawn-rate 20 --run-time 2m
```

**Tests:**
- Rapid user increase
- Cache effectiveness
- Connection pool limits
- API rate limiting

---

## Key Metrics to Monitor

### 1. Response Times
- **Excellent:** < 1 second
- **Good:** 1-3 seconds
- **Acceptable:** 3-5 seconds
- **Poor:** > 5 seconds

### 2. Throughput
- **Resume uploads:** Target 1-2 per second
- **GET requests:** Target 10-50 per second
- **Rankings:** Target 0.5-1 per second (expensive)

### 3. Error Rates
- **Production ready:** < 1% errors
- **Acceptable:** < 5% errors
- **Needs work:** > 5% errors

### 4. Concurrent Users
- **Small team:** 5-10 users
- **Medium team:** 20-50 users
- **Large team:** 50-100 users

---

## Bottlenecks to Watch For

### 1. UltraSafe API Rate Limits
**Symptom:** Sudden failures after many requests
**Solution:** 
- Implement rate limiting
- Add retry logic with exponential backoff
- Increase caching TTL

### 2. ChromaDB Performance
**Symptom:** Slow ranking with many candidates
**Solution:**
- Limit collection size
- Use pagination
- Optimize vector search parameters

### 3. Memory Usage
**Symptom:** System slows down over time
**Solution:**
- Clear old cache entries
- Implement memory limits
- Use persistent database

### 4. File Upload Size
**Symptom:** Timeouts on large resumes
**Solution:**
- Add file size limits (e.g., 5MB max)
- Compress uploaded files
- Stream large files

---

## Interpreting Results

### Good Performance Example:
```
📊 LOAD TEST SUMMARY:
   Resume Uploads: 95% success, avg 2.1s
   GET Candidates: 100% success, avg 0.05s
   Ranking: 90% success, avg 6.2s
   Throughput: 15 req/sec
```
✅ **System is production-ready**

### Poor Performance Example:
```
📊 LOAD TEST SUMMARY:
   Resume Uploads: 60% success, avg 15.3s
   GET Candidates: 85% success, avg 2.5s
   Ranking: 40% success, avg 45.1s
   Throughput: 2 req/sec
```
❌ **System needs optimization**

---

## Recommendations Based on Load Test Results

### If upload times > 5 seconds:
1. Check UltraSafe API latency
2. Verify network connection
3. Increase timeout limits
4. Add upload progress indicators

### If GET requests > 500ms:
1. Implement response caching
2. Optimize database queries
3. Add pagination
4. Use CDN for static assets

### If ranking > 15 seconds:
1. Reduce candidate pool size
2. Optimize vector search
3. Cache ranking results
4. Use background jobs

### If error rate > 5%:
1. Add retry logic
2. Implement circuit breakers
3. Check API rate limits
4. Add error logging

---

## Sample Load Test Report

```
╔══════════════════════════════════════════════════════════╗
║         HR SCREENING SYSTEM - LOAD TEST REPORT          ║
╚══════════════════════════════════════════════════════════╝

Test Date: 2026-04-22
Duration: 5 minutes
Peak Users: 20 concurrent

📤 RESUME UPLOADS:
   Total Uploads: 45
   Success Rate: 95.6% (43/45)
   Avg Time: 2.3s
   Min/Max: 1.8s / 4.2s
   Throughput: 0.15 uploads/sec

📥 GET CANDIDATES:
   Total Requests: 523
   Success Rate: 100% (523/523)
   Avg Response: 0.08s
   95th Percentile: 0.15s
   Throughput: 1.74 req/sec

🎯 RANKING:
   Total Rankings: 12
   Success Rate: 91.7% (11/12)
   Avg Time: 7.2s
   Min/Max: 5.1s / 12.3s

💡 RECOMMENDATIONS:
   ✅ System handles 20 concurrent users well
   ✅ Caching is effective (fast GET responses)
   ⚠️  Consider optimizing ranking for >10 candidates
   ✅ Ready for production deployment

╚══════════════════════════════════════════════════════════╝
```

---

## Next Steps

1. **Run baseline test** with current system
2. **Document results** in a spreadsheet
3. **Identify bottlenecks** from metrics
4. **Optimize** problem areas
5. **Re-test** to verify improvements
6. **Set performance budgets** for future development

---

## Troubleshooting

### "Cannot connect to API"
- Ensure backend is running on port 8000
- Check firewall settings
- Verify API_URL in test scripts

### "No resume files found"
- Add PDF/DOCX files to `./data/uploads/`
- Check file permissions
- Verify file paths

### "Timeout errors"
- Increase timeout in test scripts
- Check UltraSafe API status
- Verify network connection

### "Memory errors"
- Reduce concurrent users
- Clear cache between tests
- Restart backend

---

## Advanced: CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/load-test.yml
name: Load Test
on: [push]
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start backend
        run: python -m uvicorn app.main:app --port 8000 &
      - name: Run load test
        run: python load_test.py
      - name: Check performance
        run: |
          if [ $UPLOAD_TIME -gt 5 ]; then
            echo "Upload time exceeded threshold"
            exit 1
          fi
```

---

## Questions?

For issues or questions about load testing:
1. Check logs in `./logs/`
2. Review Locust web UI charts
3. Monitor system resources (CPU, RAM)
4. Test with smaller loads first

Happy load testing! 🚀
