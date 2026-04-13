"""Simple HR Resume Screening Dashboard."""

import os
import streamlit as st
import requests
import pandas as pd

API_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="HR Screening", page_icon="📄", layout="wide")

st.title("📄 HR Resume Screening")
st.write("Upload resumes, create jobs, and find the best candidates.")

# Check API connection
try:
    health = requests.get(f"{API_URL}/health", timeout=3)
    api_ok = health.status_code == 200
except:
    api_ok = False

if not api_ok:
    st.error("⚠️ API not running. Start it with: `python run_api.py`")
    st.stop()

st.success("✅ API Connected")

# Simple tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload Resumes", "📋 Create Job", "🔍 Find Matches"])

# ===================== TAB 1: Upload Resumes =====================
with tab1:
    st.header("Upload Resumes")
    st.info("💡 **Tip:** Hold Ctrl (or Cmd on Mac) to select multiple files at once!")
    
    files = st.file_uploader(
        "Select multiple PDF or DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="You can select multiple files by holding Ctrl/Cmd while clicking"
    )
    
    if files:
        st.write(f"**{len(files)} file(s) selected**")
        
        if st.button(f"📤 Upload {len(files)} Resume(s)", type="primary"):
            progress = st.progress(0)
            results = []
            
            for i, f in enumerate(files):
                try:
                    res = requests.post(
                        f"{API_URL}/candidates/upload",
                        files={"file": (f.name, f.getvalue())}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        results.append(("success", f"{data.get('name', f.name)} - {len(data.get('skills', []))} skills"))
                    else:
                        results.append(("error", f"{f.name} failed"))
                except Exception as e:
                    results.append(("error", f"{f.name}: {e}"))
                
                progress.progress((i + 1) / len(files))
            
            # Show results
            for status, msg in results:
                if status == "success":
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
            
            st.rerun()
    
    # Show uploaded candidates
    st.subheader("Uploaded Candidates")
    try:
        res = requests.get(f"{API_URL}/candidates")
        if res.status_code == 200:
            candidates = res.json()
            if candidates:
                for c in candidates:
                    name = c.get('name') or 'Unknown'
                    email = c.get('email') or 'N/A'
                    skills = c.get('skills', [])
                    skills_str = ', '.join(skills[:8]) if skills else 'No skills found'
                    if len(skills) > 8:
                        skills_str += f" (+{len(skills)-8} more)"
                    
                    with st.container():
                        st.write(f"**{name}** | {email}")
                        st.caption(f"🛠️ Skills: {skills_str}")
                        st.divider()
            else:
                st.info("No candidates yet. Upload some resumes!")
    except:
        pass

# ===================== TAB 2: Create Job =====================
with tab2:
    st.header("Create a Job")
    
    title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
    description = st.text_area("Description", placeholder="Describe the role...")
    skills = st.text_input("Required Skills (comma separated)", placeholder="Python, AWS, Docker")
    experience = st.number_input("Min Experience (years)", min_value=0, value=2)
    
    if st.button("Create Job", type="primary"):
        if title and description:
            job_data = {
                "title": title,
                "description": description,
                "required_skills": [s.strip() for s in skills.split(",") if s.strip()],
                "preferred_skills": [],
                "min_experience_years": experience
            }
            try:
                res = requests.post(f"{API_URL}/jobs", json=job_data)
                if res.status_code == 200:
                    st.success(f"✅ Job '{title}' created!")
                else:
                    st.error("Failed to create job")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please fill in title and description")
    
    # Show jobs
    st.subheader("Your Jobs")
    try:
        res = requests.get(f"{API_URL}/jobs")
        if res.status_code == 200:
            jobs = res.json()
            if jobs:
                for j in jobs:
                    st.write(f"• **{j.get('title')}** - {', '.join(j.get('required_skills', [])[:5])}")
            else:
                st.info("No jobs yet. Create one above!")
    except:
        pass

# ===================== TAB 3: Find Matches =====================
with tab3:
    st.header("Find Best Candidates")
    
    # Get jobs for selection
    try:
        res = requests.get(f"{API_URL}/jobs")
        jobs = res.json() if res.status_code == 200 else []
    except:
        jobs = []
    
    if not jobs:
        st.warning("Create a job first in the 'Create Job' tab")
    else:
        job_names = {j['title']: j['id'] for j in jobs}
        selected = st.selectbox("Select Job", list(job_names.keys()))
        job_id = job_names[selected]
        
        if st.button("🔍 Find Matching Candidates", type="primary"):
            with st.spinner("Analyzing candidates..."):
                try:
                    res = requests.get(f"{API_URL}/rankings/{job_id}?top_k=10")
                    if res.status_code == 200:
                        data = res.json()
                        rankings = data.get("rankings", [])
                        
                        if rankings:
                            st.subheader(f"Top Candidates for {selected}")
                            
                            for r in rankings:
                                score = r.get('overall_score', 0)
                                name = r.get('candidate_name', 'Unknown')
                                rec = r.get('recommendation', '').replace('_', ' ').title()
                                
                                # Color based on score
                                if score >= 70:
                                    color = "🟢"
                                elif score >= 50:
                                    color = "🟡"
                                else:
                                    color = "🔴"
                                
                                st.write(f"{color} **#{r['rank']} {name}** - Score: {score:.0f}/100 - {rec}")
                        else:
                            st.info("No matching candidates found. Upload more resumes!")
                    else:
                        st.error("Error getting rankings")
                except Exception as e:
                    st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.caption("HR Resume Screening Pipeline | API Docs: http://localhost:8000/docs")
