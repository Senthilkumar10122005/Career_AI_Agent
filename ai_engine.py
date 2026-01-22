import os
from pyexpat import model
from groq import Groq
from dotenv import load_dotenv

# Load your API Key from a .env file
load_dotenv()
# Replace 'YOUR_GROQ_API_KEY' with your actual key if not using .env
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyze_job_with_ai(raw_text):
    prompt = f"""
    You are an expert recruiter. Read the following text.
    
    CRITICAL INSTRUCTIONS:
    - If the text says "404 Not Found", "Page Not Found", or "Access Denied", respond ONLY with: "ERROR: The link provided is broken or blocked."
    - Otherwise, extract:
      Company: [Name]
      Role: [Title]
      Skills: [List]

    Text:
    {raw_text}
    """
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile", # This is a very fast, high-quality open-source model
    )

    return chat_completion.choices[0].message.content
def match_resume_to_job(resume_text, job_description):
    """
    Acts as the 'Evaluation' module.
    Calculates match score and identifies missing skills.
    """
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and Career Coach.
    Compare the RESUME and JOB DESCRIPTION below.
    
    Return your response in this format:
    1. MATCH SCORE: [0-100%]
    2. KEY MATCHES: [What skills align?]
    3. CRITICAL GAPS: [What credentials/skills are missing?]
    4. ACTION PLAN: [How should the user edit the resume to win this job?]

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def analyze_skill_gap(resume_text, job_description):
    """
    Analyzes the gap between resume and job description.
    Returns a dictionary of skills and their status.
    """
    # In a real 2026 app, this would be a prompt to Gemini
    # For now, let's simulate the AI logic:
    required_skills = ["Python", "Streamlit", "PostgreSQL", "Machine Learning", "Docker", "AWS"]
    
    # Simple logic: check if the word exists in the resume
    analysis = {}
    for skill in required_skills:
        if skill.lower() in resume_text.lower():
            analysis[skill] = 1 # Skill present
        else:
            analysis[skill] = 0 # Skill missing
            
    return analysis

def generate_roadmap(subject, days=30):
    prompt = f"""
    Create a {days}-day learning syllabus for {subject}.
    Return ONLY a list of topics separated by semicolons. 
    Example: Day 1: Basics; Day 2: Variables; Day 3: Loops...
    Do not include any other text.
    """
    response = analyze_job_with_ai(prompt) # Uses your existing LangChain setup
    return response

def extract_dynamic_skills(job_description):
    """Uses Gemini to extract specific skills from any job description."""
    prompt = f"""
    Extract exactly the top 6 professional skills or tools required in this job description.
    Return only the skill names separated by commas.
    Job Description: {job_description}
    """
    try:
        # Calling your Gemini model
        response = model.generate_content(prompt)
        # Convert "Photoshop, Illustrator, Figma" -> ["Photoshop", "Illustrator", "Figma"]
        skills_list = [s.strip() for s in response.text.split(",")]
        return skills_list[:6] # Ensure only 6
    except:
        # Fallback if API fails
        return ["Communication", "Teamwork", "Problem Solving", "Software", "Project Management", "Detail Oriented"]
    
    