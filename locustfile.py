"""
Locust Load Testing Configuration for HR Screening System

Run with:
    locust -f locustfile.py --host=http://127.0.0.1:8000

Then open: http://localhost:8089
"""

from locust import HttpUser, task, between, events
from pathlib import Path
import random
import json

class HRScreeningUser(HttpUser):
    """Simulates a user interacting with the HR Screening system."""
    
    # Wait 1-3 seconds between tasks (simulates real user behavior)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.job_ids = []
        self.candidate_ids = []
        
        # Check API health
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(3)  # Weight: 3 (runs 3x more often than other tasks)
    def get_candidates(self):
        """GET /api/v1/candidates - Most common operation."""
        with self.client.get("/api/v1/candidates", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.candidate_ids = [c["id"] for c in data]
                response.success()
            else:
                response.failure(f"Failed to get candidates: {response.status_code}")
    
    @task(2)  # Weight: 2
    def get_jobs(self):
        """GET /api/v1/jobs."""
        with self.client.get("/api/v1/jobs", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.job_ids = [j["id"] for j in data]
                response.success()
            else:
                response.failure(f"Failed to get jobs: {response.status_code}")
    
    @task(1)  # Weight: 1 (less frequent - expensive operation)
    def create_job(self):
        """POST /api/v1/jobs - Create a new job."""
        job_data = {
            "title": f"Load Test Job {random.randint(1000, 9999)}",
            "description": "This is a load test job description for performance testing.",
            "required_skills": random.sample(
                ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes"],
                k=random.randint(3, 5)
            ),
            "required_experience_years": random.choice([2, 3, 5, 7]),
            "required_education": random.choice(["Bachelor's", "Master's", "PhD"])
        }
        
        with self.client.post(
            "/api/v1/jobs",
            json=job_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                job_id = response.json().get("id")
                if job_id:
                    self.job_ids.append(job_id)
                response.success()
            else:
                response.failure(f"Failed to create job: {response.status_code}")
    
    @task(1)  # Weight: 1 (expensive - ranking operation)
    def rank_candidates(self):
        """GET /api/v1/rankings/{job_id} - Rank candidates for a job."""
        if not self.job_ids:
            # Create a job first if none exist
            self.create_job()
            return
        
        job_id = random.choice(self.job_ids)
        
        with self.client.get(
            f"/api/v1/rankings/{job_id}",
            params={"top_k": 10},
            catch_response=True,
            timeout=60  # Ranking can take longer
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to rank candidates: {response.status_code}")


class StressTestUser(HttpUser):
    """Aggressive stress testing - pushes system to limits."""
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    
    @task
    def rapid_fire_get_candidates(self):
        """Rapid GET requests to test caching and performance."""
        self.client.get("/api/v1/candidates")
    
    @task
    def rapid_fire_get_jobs(self):
        """Rapid GET requests for jobs."""
        self.client.get("/api/v1/jobs")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║         HR SCREENING SYSTEM - LOCUST LOAD TEST          ║
    ╚══════════════════════════════════════════════════════════╝
    
    📊 Test Configuration:
       - Normal Users: Simulate realistic user behavior
       - Stress Users: Rapid-fire requests to test limits
    
    🎯 What's Being Tested:
       - GET /candidates (most frequent)
       - GET /jobs
       - POST /jobs (job creation)
       - GET /rankings/{job_id} (expensive operation)
    
    📈 Monitor:
       - Response times
       - Failure rates
       - Requests per second
       - System resource usage
    
    🌐 Open http://localhost:8089 to view results
    """)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              LOAD TEST COMPLETED                        ║
    ╚══════════════════════════════════════════════════════════╝
    
    📊 Check the Locust web UI for detailed results
    """)
