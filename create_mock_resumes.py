"""Generate mock resumes for testing."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os

def create_resume(filename, data):
    """Create a PDF resume."""
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    name_style = ParagraphStyle('Name', parent=styles['Heading1'], fontSize=18, spaceAfter=6)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, spaceBefore=12, spaceAfter=6)
    normal = styles['Normal']
    
    story = []
    
    # Name and contact
    story.append(Paragraph(data['name'], name_style))
    story.append(Paragraph(f"{data['email']} | {data['phone']} | {data['location']}", normal))
    story.append(Spacer(1, 12))
    
    # Summary
    story.append(Paragraph("SUMMARY", section_style))
    story.append(Paragraph(data['summary'], normal))
    
    # Skills
    story.append(Paragraph("SKILLS", section_style))
    story.append(Paragraph(", ".join(data['skills']), normal))
    
    # Experience
    story.append(Paragraph("EXPERIENCE", section_style))
    for exp in data['experience']:
        story.append(Paragraph(f"<b>{exp['title']}</b> at {exp['company']} ({exp['dates']})", normal))
        story.append(Paragraph(exp['description'], normal))
        story.append(Spacer(1, 6))
    
    # Education
    story.append(Paragraph("EDUCATION", section_style))
    for edu in data['education']:
        story.append(Paragraph(f"<b>{edu['degree']}</b> - {edu['school']} ({edu['year']})", normal))
    
    doc.build(story)
    print(f"Created: {filename}")

# Mock resume data
resumes = [
    {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "+1-555-123-4567",
        "location": "San Francisco, CA",
        "summary": "Senior Software Engineer with 6+ years of experience in full-stack development. Expert in Python, React, and cloud technologies. Passionate about building scalable systems and mentoring junior developers.",
        "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "Git", "CI/CD", "Agile", "REST API", "GraphQL"],
        "experience": [
            {"title": "Senior Software Engineer", "company": "TechCorp Inc", "dates": "2021 - Present", "description": "Lead development of microservices architecture serving 1M+ users. Implemented CI/CD pipelines reducing deployment time by 60%."},
            {"title": "Software Engineer", "company": "StartupXYZ", "dates": "2018 - 2021", "description": "Built React frontend and Node.js backend for e-commerce platform. Integrated payment systems and analytics."}
        ],
        "education": [{"degree": "B.S. Computer Science", "school": "Stanford University", "year": "2018"}]
    },
    {
        "name": "Michael Chen",
        "email": "michael.chen@gmail.com",
        "phone": "+1-555-987-6543",
        "location": "New York, NY",
        "summary": "Data Scientist with 4 years of experience in machine learning and analytics. Skilled in building predictive models and extracting insights from large datasets. Strong background in statistics and deep learning.",
        "skills": ["Python", "R", "TensorFlow", "PyTorch", "Scikit-learn", "SQL", "Pandas", "NumPy", "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Spark", "Tableau"],
        "experience": [
            {"title": "Data Scientist", "company": "Analytics Pro", "dates": "2022 - Present", "description": "Developed ML models for customer churn prediction achieving 92% accuracy. Built NLP pipelines for sentiment analysis."},
            {"title": "Junior Data Analyst", "company": "DataCo", "dates": "2020 - 2022", "description": "Created dashboards and reports for executive team. Performed A/B testing and statistical analysis."}
        ],
        "education": [{"degree": "M.S. Data Science", "school": "Columbia University", "year": "2020"}]
    },
    {
        "name": "Emily Rodriguez",
        "email": "emily.rodriguez@outlook.com",
        "phone": "+1-555-456-7890",
        "location": "Austin, TX",
        "summary": "DevOps Engineer with 5 years of experience in cloud infrastructure and automation. Expert in AWS, Terraform, and container orchestration. Focused on reliability, security, and cost optimization.",
        "skills": ["AWS", "Azure", "GCP", "Terraform", "Ansible", "Docker", "Kubernetes", "Jenkins", "GitHub Actions", "Linux", "Bash", "Python", "Monitoring", "Security"],
        "experience": [
            {"title": "Senior DevOps Engineer", "company": "CloudScale", "dates": "2021 - Present", "description": "Managed infrastructure for 500+ microservices on AWS. Reduced cloud costs by 40% through optimization."},
            {"title": "DevOps Engineer", "company": "WebServices Inc", "dates": "2019 - 2021", "description": "Implemented Kubernetes clusters and automated deployments. Set up monitoring with Prometheus and Grafana."}
        ],
        "education": [{"degree": "B.S. Information Technology", "school": "UT Austin", "year": "2019"}]
    }
]

# Create output directory
output_dir = "mock_resumes"
os.makedirs(output_dir, exist_ok=True)

# Generate resumes
for i, data in enumerate(resumes, 1):
    filename = os.path.join(output_dir, f"{data['name'].replace(' ', '_')}_Resume.pdf")
    create_resume(filename, data)

print(f"\n✅ Created 3 mock resumes in '{output_dir}/' folder")
print("Files:")
for f in os.listdir(output_dir):
    print(f"  - {f}")
