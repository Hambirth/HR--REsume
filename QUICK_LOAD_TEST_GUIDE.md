# 🚀 Quick Load Test Guide - 5 Minutes

## Step 1: Start Backend (if not running)
```bash
python -m uvicorn app.main:app --reload --port 8000
```

## Step 2: Choose Your Test Method

### Option A: Simple Test (Easiest)
```bash
python load_test.py
```
**Time:** 2-3 minutes  
**Output:** Console report with metrics

### Option B: Locust Web UI (Best Visualization)
```bash
locust -f locustfile.py --host=http://127.0.0.1:8000
```
Then open: **http://localhost:8089**
- Set users: 10
- Spawn rate: 2
- Click "Start"

### Option C: One-Click Launcher
```bash
run_load_test.bat
```
Choose option 1 or 2

---

## What to Look For

### ✅ Good Performance
- Upload time: < 3 seconds
- GET requests: < 0.5 seconds
- Ranking: < 10 seconds
- Success rate: > 95%

### ❌ Poor Performance
- Upload time: > 5 seconds
- GET requests: > 1 second
- Ranking: > 20 seconds
- Success rate: < 90%

---

## Quick Metrics

### Test 1: Upload 5 Resumes
**Expected:** 2-3 seconds each, 100% success

### Test 2: 10 GET Requests
**Expected:** < 0.1 seconds each, 100% success

### Test 3: Ranking
**Expected:** 5-10 seconds, 100% success

---

## Common Issues

### "Cannot connect to API"
→ Start backend first

### "No resume files found"
→ Add PDFs to `./data/uploads/`

### "Timeout errors"
→ UltraSafe API might be slow, wait and retry

---

## Report to Team

Use this template:

> "Load test results:
> - ✅ Handles [X] concurrent uploads
> - ✅ Average upload time: [X.X] seconds
> - ✅ API response time: [X.X] seconds
> - ✅ Success rate: [X]%
> - System is ready for [X] concurrent users"

---

## Need More Details?

Read: `LOAD_TESTING.md` (full guide)
