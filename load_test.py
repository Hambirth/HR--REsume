"""
Load Testing Script for HR Screening System

Tests:
1. Concurrent resume uploads
2. API endpoint performance
3. Ranking under load
4. System resource usage

Usage:
    python load_test.py
"""

import asyncio
import time
import httpx
import statistics
from pathlib import Path
from typing import List, Dict
import json

API_URL = "http://127.0.0.1:8000/api/v1"

class LoadTester:
    def __init__(self):
        self.results = {
            "upload": [],
            "ranking": [],
            "get_candidates": [],
            "create_job": []
        }
    
    async def test_health_check(self):
        """Test if API is running."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{API_URL}/health")
                if response.status_code == 200:
                    print("✅ API is running")
                    return True
                else:
                    print(f"❌ API returned status {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Cannot connect to API: {e}")
                print("Make sure backend is running: python -m uvicorn app.main:app --reload --port 8000")
                return False
    
    async def upload_resume(self, file_path: str, client: httpx.AsyncClient) -> Dict:
        """Upload a single resume and measure time."""
        start = time.time()
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/pdf')}
                response = await client.post(
                    f"{API_URL}/candidates/upload",
                    files=files
                )
            
            elapsed = time.time() - start
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "time": elapsed,
                    "file": Path(file_path).name,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "time": elapsed,
                    "file": Path(file_path).name,
                    "error": f"Status {response.status_code}"
                }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "success": False,
                "time": elapsed,
                "file": Path(file_path).name,
                "error": str(e)
            }
    
    async def test_concurrent_uploads(self, num_concurrent: int = 20):
        """Test uploading multiple resumes concurrently."""
        print(f"\n{'='*60}")
        print(f"TEST 1: Concurrent Resume Uploads ({num_concurrent} files)")
        print(f"{'='*60}")
        
        # Find test resume files
        upload_dir = Path("./data/uploads")
        resume_files = list(upload_dir.glob("*.pdf")) + list(upload_dir.glob("*.docx"))
        
        if not resume_files:
            print("❌ No resume files found in ./data/uploads/")
            print("Please add some PDF or DOCX files to test with")
            return
        
        # Use available files (repeat if needed)
        test_files = []
        for i in range(num_concurrent):
            test_files.append(str(resume_files[i % len(resume_files)]))
        
        print(f"📁 Found {len(resume_files)} resume files")
        print(f"🚀 Uploading {num_concurrent} resumes concurrently...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            start_time = time.time()
            
            # Upload all concurrently
            tasks = [self.upload_resume(file, client) for file in test_files]
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"\n📊 RESULTS:")
        print(f"   Total uploads: {len(results)}")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   ⚡ Avg time per upload: {statistics.mean([r['time'] for r in results]):.2f}s")
        print(f"   🚀 Throughput: {len(results)/total_time:.2f} uploads/second")
        
        if successful:
            times = [r['time'] for r in successful]
            print(f"\n   📈 Upload Time Stats:")
            print(f"      Min: {min(times):.2f}s")
            print(f"      Max: {max(times):.2f}s")
            print(f"      Median: {statistics.median(times):.2f}s")
        
        if failed:
            print(f"\n   ❌ Failed uploads:")
            for r in failed:
                print(f"      {r['file']}: {r['error']}")
        
        self.results["upload"] = results
        return results
    
    async def test_get_candidates(self, num_requests: int = 10):
        """Test GET /candidates endpoint under load."""
        print(f"\n{'='*60}")
        print(f"TEST 2: GET Candidates Endpoint ({num_requests} requests)")
        print(f"{'='*60}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            start_time = time.time()
            
            async def get_candidates():
                start = time.time()
                response = await client.get(f"{API_URL}/candidates")
                elapsed = time.time() - start
                return {
                    "success": response.status_code == 200,
                    "time": elapsed,
                    "count": len(response.json()) if response.status_code == 200 else 0
                }
            
            tasks = [get_candidates() for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        times = [r['time'] for r in successful]
        
        print(f"\n📊 RESULTS:")
        print(f"   Total requests: {len(results)}")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   ⚡ Avg response time: {statistics.mean(times):.3f}s")
        print(f"   🚀 Throughput: {len(results)/total_time:.2f} requests/second")
        print(f"   📈 Response Time Stats:")
        print(f"      Min: {min(times):.3f}s")
        print(f"      Max: {max(times):.3f}s")
        print(f"      Median: {statistics.median(times):.3f}s")
        
        if successful:
            print(f"   📦 Candidates returned: {successful[0]['count']}")
        
        self.results["get_candidates"] = results
        return results
    
    async def test_create_job(self, num_jobs: int = 5):
        """Test creating multiple jobs concurrently."""
        print(f"\n{'='*60}")
        print(f"TEST 3: Create Job Endpoint ({num_jobs} jobs)")
        print(f"{'='*60}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async def create_job(index: int):
                start = time.time()
                job_data = {
                    "title": f"Test Job {index}",
                    "description": f"Test job description for load testing {index}",
                    "required_skills": ["Python", "JavaScript", "React"],
                    "required_experience_years": 3,
                    "required_education": "Bachelor's"
                }
                
                try:
                    response = await client.post(
                        f"{API_URL}/jobs",
                        json=job_data
                    )
                    elapsed = time.time() - start
                    return {
                        "success": response.status_code == 200,
                        "time": elapsed,
                        "job_id": response.json().get("id") if response.status_code == 200 else None
                    }
                except Exception as e:
                    elapsed = time.time() - start
                    return {
                        "success": False,
                        "time": elapsed,
                        "error": str(e)
                    }
            
            start_time = time.time()
            tasks = [create_job(i) for i in range(num_jobs)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        times = [r['time'] for r in results]
        
        print(f"\n📊 RESULTS:")
        print(f"   Total jobs: {len(results)}")
        print(f"   ✅ Created: {len(successful)}")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   ⚡ Avg creation time: {statistics.mean(times):.3f}s")
        print(f"   🚀 Throughput: {len(results)/total_time:.2f} jobs/second")
        
        self.results["create_job"] = results
        return results
    
    async def test_ranking_under_load(self, num_concurrent: int = 3):
        """Test ranking endpoint with concurrent requests."""
        print(f"\n{'='*60}")
        print(f"TEST 4: Ranking Under Load ({num_concurrent} concurrent rankings)")
        print(f"{'='*60}")
        
        # First, get a job ID
        async with httpx.AsyncClient(timeout=90.0) as client:
            jobs_response = await client.get(f"{API_URL}/jobs")
            if jobs_response.status_code != 200 or not jobs_response.json():
                print("❌ No jobs found. Creating a test job first...")
                await self.test_create_job(1)
                jobs_response = await client.get(f"{API_URL}/jobs")
            
            jobs = jobs_response.json()
            if not jobs:
                print("❌ Cannot test ranking without jobs")
                return
            
            job_id = jobs[0]["id"]
            print(f"📋 Using job: {jobs[0]['title']} ({job_id})")
            
            async def rank_candidates():
                start = time.time()
                try:
                    response = await client.get(
                        f"{API_URL}/rankings/{job_id}",
                        params={"top_k": 10}
                    )
                    elapsed = time.time() - start
                    return {
                        "success": response.status_code == 200,
                        "time": elapsed,
                        "candidates": len(response.json()) if response.status_code == 200 else 0
                    }
                except Exception as e:
                    elapsed = time.time() - start
                    return {
                        "success": False,
                        "time": elapsed,
                        "error": str(e)
                    }
            
            start_time = time.time()
            tasks = [rank_candidates() for _ in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        times = [r['time'] for r in successful] if successful else [0]
        
        print(f"\n📊 RESULTS:")
        print(f"   Total ranking requests: {len(results)}")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        if successful:
            print(f"   ⚡ Avg ranking time: {statistics.mean(times):.2f}s")
            print(f"   📈 Ranking Time Stats:")
            print(f"      Min: {min(times):.2f}s")
            print(f"      Max: {max(times):.2f}s")
            print(f"      Median: {statistics.median(times):.2f}s")
            print(f"   👥 Candidates ranked: {successful[0]['candidates']}")
        
        self.results["ranking"] = results
        return results
    
    def generate_report(self):
        """Generate final load test report."""
        print(f"\n{'='*60}")
        print("📋 LOAD TEST SUMMARY REPORT")
        print(f"{'='*60}")
        
        # Upload summary
        if self.results["upload"]:
            uploads = self.results["upload"]
            successful = [r for r in uploads if r["success"]]
            print(f"\n📤 RESUME UPLOADS:")
            print(f"   Success Rate: {len(successful)}/{len(uploads)} ({len(successful)/len(uploads)*100:.1f}%)")
            if successful:
                times = [r['time'] for r in successful]
                print(f"   Avg Time: {statistics.mean(times):.2f}s")
                print(f"   Max Concurrent: {len(uploads)} uploads")
        
        # GET candidates summary
        if self.results["get_candidates"]:
            gets = self.results["get_candidates"]
            successful = [r for r in gets if r["success"]]
            times = [r['time'] for r in successful]
            print(f"\n📥 GET CANDIDATES:")
            print(f"   Success Rate: {len(successful)}/{len(gets)} ({len(successful)/len(gets)*100:.1f}%)")
            print(f"   Avg Response: {statistics.mean(times):.3f}s")
        
        # Ranking summary
        if self.results["ranking"]:
            rankings = self.results["ranking"]
            successful = [r for r in rankings if r["success"]]
            if successful:
                times = [r['time'] for r in successful]
                print(f"\n🎯 RANKING:")
                print(f"   Success Rate: {len(successful)}/{len(rankings)} ({len(successful)/len(rankings)*100:.1f}%)")
                print(f"   Avg Time: {statistics.mean(times):.2f}s")
        
        print(f"\n{'='*60}")
        print("✅ Load testing complete!")
        print(f"{'='*60}\n")

async def main():
    """Run all load tests."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         HR SCREENING SYSTEM - LOAD TESTING              ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    tester = LoadTester()
    
    # Check if API is running
    if not await tester.test_health_check():
        return
    
    print("\n🚀 Starting load tests...\n")
    
    # Run tests with higher loads
    await tester.test_concurrent_uploads(num_concurrent=100)  # Test 100 concurrent uploads
    await asyncio.sleep(2)  # Brief pause between tests
    
    await tester.test_get_candidates(num_requests=200)  # Test 200 GET requests
    await asyncio.sleep(1)
    
    await tester.test_create_job(num_jobs=10)  # Test 10 job creations
    await asyncio.sleep(1)
    
    await tester.test_ranking_under_load(num_concurrent=3)  # Test 3 concurrent rankings (within limit)
    
    # Generate final report
    tester.generate_report()

if __name__ == "__main__":
    asyncio.run(main())
