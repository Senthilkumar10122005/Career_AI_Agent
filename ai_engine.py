import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MODEL = "llama-3.3-70b-versatile"
BACKUP_MODEL = "llama-3.1-70b-versatile"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clean_json_response(text):
    """
    Cleans and extracts JSON from AI responses that might contain
    markdown formatting or extra text.
    """
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Try to find JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return text.strip()

def safe_api_call(prompt, model=DEFAULT_MODEL, max_tokens=2000, temperature=0.3):
    """
    Centralized API call function with error handling and retry logic.
    
    Args:
        prompt: The prompt to send to the AI
        model: Model to use (default: llama-3.3-70b-versatile)
        max_tokens: Maximum tokens in response
        temperature: Creativity level (0.0-1.0)
    
    Returns:
        str: AI response text or error message
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    except Exception as e:
        # Try backup model if primary fails
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=BACKUP_MODEL,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except:
            return f"ERROR: API call failed - {str(e)}"

# ============================================================================
# METADATA EXTRACTION
# ============================================================================

def extract_metadata(scraped_text):
    """
    Extracts company name and job role from scraped job posting text.
    
    Enhanced with:
    - Better prompt engineering
    - Fallback mechanisms
    - More reliable JSON parsing
    
    Args:
        scraped_text: Raw text from job posting
    
    Returns:
        dict: {"company": str, "role": str}
    """
    prompt = f"""You are a precise information extraction system.

TASK:
Extract the company name and job title from the text below.

RULES:
1. Use ONLY information explicitly stated in the text
2. Preserve original capitalization and spelling
3. If multiple companies mentioned, choose the hiring company
4. If multiple roles mentioned, choose the primary position
5. Return null if information is not found
6. DO NOT make assumptions or guesses

OUTPUT FORMAT:
Return ONLY valid JSON with no markdown, no explanations:
{{
  "company": "Company Name",
  "role": "Job Title"
}}

TEXT:
{scraped_text[:2000]}

JSON OUTPUT:"""

    try:
        response = safe_api_call(prompt, temperature=0.1)
        
        # Clean and parse JSON
        clean_response = clean_json_response(response)
        metadata = json.loads(clean_response)
        
        # Validate response
        if not isinstance(metadata, dict):
            raise ValueError("Invalid response format")
        
        # Ensure required keys exist
        if "company" not in metadata or "role" not in metadata:
            raise KeyError("Missing required fields")
        
        # Handle null/None values
        return {
            "company": metadata.get("company") or "Company Not Found",
            "role": metadata.get("role") or "Role Not Specified"
        }
    
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Metadata extraction error: {e}")
        # Fallback: Try simple regex extraction
        company = "Unknown Company"
        role = "Position"
        
        # Look for common patterns
        company_patterns = [
            r'(?:at|@|for)\s+([A-Z][A-Za-z0-9\s&,.]+?)(?:\s+is|\s+seeks|\s+looking)',
            r'Company:\s*([A-Z][A-Za-z0-9\s&,.]+)',
            r'^([A-Z][A-Za-z0-9\s&,.]{2,30})\s+(?:is hiring|seeks|looking)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, scraped_text[:500])
            if match:
                company = match.group(1).strip()
                break
        
        return {"company": company, "role": role}

# ============================================================================
# JOB ANALYSIS
# ============================================================================

def analyze_job_with_ai(raw_text):
    """
    Analyzes job posting and extracts key information.
    
    Enhanced with:
    - Error detection for broken links
    - Structured output format
    - Better skill extraction
    
    Args:
        raw_text: Raw scraped text from job posting
    
    Returns:
        str: Formatted analysis or error message
    """
    # Check for error pages first
    error_indicators = ["404", "not found", "page not found", "access denied", "forbidden"]
    if any(indicator in raw_text.lower() for indicator in error_indicators):
        return "❌ ERROR: The provided link appears to be broken, inaccessible, or password-protected."
    
    prompt = f"""You are an expert recruiter analyzing a job posting.

TASK:
Analyze the job posting below and extract key information.

INSTRUCTIONS:
1. Identify the company name
2. Identify the job title/role
3. List the TOP 8 required skills (technical and soft skills)
4. Identify experience level required
5. Note any standout benefits or perks

OUTPUT FORMAT:
Use this exact structure with clear formatting:

🏢 **COMPANY:** [Company Name]

💼 **ROLE:** [Job Title]

🎯 **REQUIRED SKILLS:**
• [Skill 1]
• [Skill 2]
• [Skill 3]
• [Skill 4]
• [Skill 5]
• [Skill 6]
• [Skill 7]
• [Skill 8]

📊 **EXPERIENCE LEVEL:** [Entry/Mid/Senior]

✨ **KEY HIGHLIGHTS:**
• [Highlight 1]
• [Highlight 2]
• [Highlight 3]

JOB POSTING TEXT:
{raw_text[:3000]}

ANALYSIS:"""

    response = safe_api_call(prompt, max_tokens=1500, temperature=0.3)
    
    # Add fallback if response is too short
    if len(response) < 100:
        return f"⚠️ Limited information extracted. Here's what was found:\n\n{response}"
    
    return response

# ============================================================================
# RESUME TO JOB MATCHING
# ============================================================================

def match_resume_to_job(resume_text, job_description):
    """
    Compares resume against job description and provides detailed analysis.
    
    Enhanced with:
    - Percentage-based scoring
    - Specific skill gap identification
    - Actionable recommendations
    
    Args:
        resume_text: Full resume text
        job_description: Job posting text
    
    Returns:
        str: Detailed matching analysis
    """
    prompt = f"""You are an expert ATS (Applicant Tracking System) and Career Coach.

TASK:
Analyze how well this RESUME matches the JOB DESCRIPTION.

ANALYSIS REQUIREMENTS:
1. Calculate a realistic match percentage (0-100%)
2. Identify skills that align well
3. Identify critical missing skills
4. Provide specific, actionable improvement steps

OUTPUT FORMAT:
Use this exact structure:

📊 **OVERALL MATCH SCORE:** [X]%

✅ **STRONG MATCHES:**
• [Matching skill/experience 1]
• [Matching skill/experience 2]
• [Matching skill/experience 3]
• [Matching skill/experience 4]

❌ **CRITICAL GAPS:**
• [Missing skill/credential 1]
• [Missing skill/credential 2]
• [Missing skill/credential 3]
• [Missing skill/credential 4]

🎯 **IMPROVEMENT STRATEGY:**
1. [Specific action item 1]
2. [Specific action item 2]
3. [Specific action item 3]
4. [Specific action item 4]

💡 **RESUME ENHANCEMENT TIPS:**
• [Tip 1: What to add/emphasize]
• [Tip 2: What to reword]
• [Tip 3: What keywords to include]

---

RESUME:
{resume_text[:2500]}

---

JOB DESCRIPTION:
{job_description[:2500]}

---

ANALYSIS:"""

    return safe_api_call(prompt, max_tokens=2000, temperature=0.4)

# ============================================================================
# SKILL GAP ANALYSIS
# ============================================================================

def extract_dynamic_skills(job_description):
    """
    Extracts the most important skills from a job description.
    
    Enhanced with:
    - More reliable extraction
    - Fallback mechanisms
    - Validation of output
    
    Args:
        job_description: Job posting text
    
    Returns:
        list: List of 6-8 key skills
    """
    prompt = f"""You are a skill extraction expert.

TASK:
Extract the TOP 8 most important skills required for this job.

RULES:
1. Include both technical skills (e.g., Python, AWS) and soft skills (e.g., Communication)
2. Use exact terminology from the job posting when possible
3. Prioritize skills mentioned multiple times or in requirements section
4. Return ONLY the skill names, nothing else
5. Separate skills with commas
6. No numbering, no bullets, no explanations

EXAMPLE OUTPUT:
Python, JavaScript, React, AWS, Docker, Communication, Problem Solving, Team Leadership

JOB DESCRIPTION:
{job_description[:2000]}

SKILLS:"""

    try:
        response = safe_api_call(prompt, temperature=0.2, max_tokens=200)
        
        # Clean response
        response = response.strip()
        
        # Remove common formatting issues
        response = re.sub(r'^\d+[\.\)]\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^[•\-\*]\s*', '', response, flags=re.MULTILINE)
        response = response.replace('\n', ',')
        
        # Split and clean
        skills = [s.strip() for s in response.split(',') if s.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen and len(skill) > 1:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        # Return top 8 skills
        result = unique_skills[:8]
        
        # Fallback if less than 3 skills extracted
        if len(result) < 3:
            return [
                "Communication",
                "Problem Solving",
                "Teamwork",
                "Technical Skills",
                "Project Management",
                "Analytical Thinking"
            ]
        
        return result
    
    except Exception as e:
        print(f"Skill extraction error: {e}")
        return [
            "Communication",
            "Problem Solving",
            "Teamwork",
            "Technical Skills",
            "Project Management",
            "Analytical Thinking"
        ]

def analyze_skill_gap(resume_text, job_description):
    """
    Analyzes the gap between resume skills and job requirements.
    
    Enhanced with:
    - Dynamic skill extraction
    - Weighted matching
    - More accurate detection
    
    Args:
        resume_text: Full resume text
        job_description: Job posting text
    
    Returns:
        dict: Skill name -> proficiency level (0-100)
    """
    # Extract required skills from job
    required_skills = extract_dynamic_skills(job_description)
    
    # Analyze each skill
    analysis = {}
    resume_lower = resume_text.lower()
    
    for skill in required_skills:
        skill_lower = skill.lower()
        
        # Check for exact match
        if skill_lower in resume_lower:
            # Check frequency (more mentions = higher proficiency)
            count = resume_lower.count(skill_lower)
            if count >= 3:
                analysis[skill] = 100
            elif count == 2:
                analysis[skill] = 75
            else:
                analysis[skill] = 50
        else:
            # Check for partial matches or synonyms
            # For example, "JS" might match "JavaScript"
            if any(word in resume_lower for word in skill_lower.split()):
                analysis[skill] = 30
            else:
                analysis[skill] = 0
    
    return analysis

# ============================================================================
# LEARNING ROADMAP GENERATION
# ============================================================================

def generate_roadmap(subject, days=30):
    """
    Generates a comprehensive learning roadmap for a given subject.
    
    Enhanced with:
    - Day-by-day breakdown
    - Progressive difficulty
    - Practical projects
    - Better formatting
    
    Args:
        subject: Subject/skill to learn
        days: Duration of learning path (default: 30)
    
    Returns:
        str: Semicolon-separated list of daily topics
    """
    prompt = f"""You are an expert curriculum designer and educator.

TASK:
Create a comprehensive {days}-day learning roadmap for: {subject}

REQUIREMENTS:
1. Start with fundamentals and progress to advanced topics
2. Include practical projects every 5-7 days
3. Each day should have ONE clear learning objective
4. Topics should build upon previous days
5. Balance theory with hands-on practice

OUTPUT FORMAT:
Return ONLY a semicolon-separated list of topics. Each topic should be concise (3-8 words).
Format: Day 1 topic;Day 2 topic;Day 3 topic;...

EXAMPLE (for Python - 7 days):
Introduction to Python and Setup;Variables and Data Types;Control Flow and Loops;Functions and Modules;File Handling and Exceptions;Object-Oriented Programming Basics;Mini Project - Build a Calculator

DO NOT include:
- Day numbers in the output
- Explanations
- Bullet points
- Numbering
- Any other text

{days}-DAY ROADMAP FOR {subject.upper()}:"""

    try:
        response = safe_api_call(prompt, temperature=0.6, max_tokens=1500)
        
        # Clean the response
        response = response.strip()
        
        # Remove common formatting issues
        response = re.sub(r'Day \d+:\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'^\d+[\.\)]\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^[•\-\*]\s*', '', response, flags=re.MULTILINE)
        
        # Convert newlines to semicolons if present
        if '\n' in response and ';' not in response:
            response = response.replace('\n', ';')
        
        # Split into topics
        topics = [t.strip() for t in response.split(';') if t.strip()]
        
        # Ensure we have the right number of topics
        if len(topics) < days:
            # Pad with review days if needed
            while len(topics) < days:
                topics.append(f"Review and Practice - Day {len(topics) + 1}")
        elif len(topics) > days:
            # Trim to exact number
            topics = topics[:days]
        
        # Rejoin with semicolons
        result = ';'.join(topics)
        
        # Validation: ensure we got meaningful content
        if len(result) < 50:  # Too short, probably failed
            raise ValueError("Roadmap generation produced insufficient content")
        
        return result
    
    except Exception as e:
        print(f"Roadmap generation error: {e}")
        
        # Fallback: Generate basic roadmap
        basic_topics = [
            f"Introduction to {subject}",
            f"Core Concepts of {subject}",
            f"Fundamental Principles",
            f"Intermediate Techniques",
            f"Hands-on Practice Session",
            f"Advanced Topics Introduction",
            f"Real-world Applications",
            f"Best Practices and Patterns",
            f"Problem Solving Exercises",
            f"Mini Project - Part 1",
            f"Mini Project - Part 2",
            f"Code Review and Optimization",
            f"Testing and Debugging",
            f"Performance Optimization",
            f"Security Considerations",
            f"Advanced Features Deep Dive",
            f"Industry Standards and Tools",
            f"Version Control and Collaboration",
            f"Deployment and Production",
            f"Monitoring and Maintenance",
            f"Final Project - Planning",
            f"Final Project - Development 1",
            f"Final Project - Development 2",
            f"Final Project - Testing",
            f"Final Project - Deployment",
            f"Portfolio Building",
            f"Interview Preparation",
            f"Continuous Learning Resources",
            f"Community and Networking",
            f"Career Path Exploration"
        ]
        
        # Return appropriate number of topics
        return ';'.join(basic_topics[:days])

# ============================================================================
# LATEX RESUME GENERATION
# ============================================================================

def generate_latex_resume(resume_text, job_description):
    """
    Converts resume to professional LaTeX format tailored to job.
    
    Enhanced with:
    - ATS optimization
    - Error correction
    - Professional formatting
    - Keyword integration
    
    Args:
        resume_text: Original resume text
        job_description: Target job posting
    
    Returns:
        str: Complete LaTeX document code
    """
    prompt = f"""You are a professional Resume Writer and LaTeX expert.

TASK:
Transform this RESUME into a professional, ATS-optimized LaTeX document tailored for the TARGET JOB.

CRITICAL REQUIREMENTS:

1. STRUCTURE:
   - Use \\documentclass{{article}} or {{moderncv}}
   - Include proper sections: Contact, Summary, Experience, Education, Skills, Projects
   - Use \\section{{}}, \\subsection{{}}, \\itemize for organization
   
2. FORMATTING:
   - Dates must be right-aligned using \\hfill
   - Bold important text with \\textbf{{}}
   - Use consistent spacing and indentation
   - Single column layout for ATS compatibility

3. CONTENT OPTIMIZATION:
   - Fix ALL spelling, grammar, and formatting errors
   - Integrate relevant keywords from job description naturally
   - Use action verbs (Developed, Implemented, Led, etc.)
   - Quantify achievements with numbers and metrics
   - Keep bullet points concise (1-2 lines each)

4. ATS COMPLIANCE:
   - Use standard fonts (Times, Helvetica, etc.)
   - Avoid tables, text boxes, headers/footers
   - Use standard section names
   - No graphics or special characters

5. PROFESSIONAL TONE:
   - Third person, achievement-focused
   - No personal pronouns
   - Confident but not arrogant

OUTPUT:
Return ONLY the complete LaTeX code. Start with \\documentclass and end with \\end{{document}}.
NO explanations, NO markdown, NO conversational text.

---

ORIGINAL RESUME:
{resume_text[:2500]}

---

TARGET JOB:
{job_description[:1500]}

---

LATEX CODE:"""

    response = safe_api_call(prompt, max_tokens=3000, temperature=0.3)
    
    # Ensure response starts with \documentclass
    if not response.strip().startswith('\\documentclass'):
        # Try to extract LaTeX code if wrapped in markdown
        latex_match = re.search(r'\\documentclass.*?\\end\{document\}', response, re.DOTALL)
        if latex_match:
            response = latex_match.group(0)
        else:
            # Fallback: add document structure
            response = f"\\documentclass{{article}}\n\\begin{{document}}\n{response}\n\\end{{document}}"
    
    return response

# ============================================================================
# CAREER MENTOR CHAT
# ============================================================================

def career_mentor_chat(user_query, context_data=""):
    """
    Provides friendly, expert career advice with personality.
    
    Enhanced with:
    - Contextual awareness
    - Actionable advice
    - Encouraging tone
    - Structured responses
    
    Args:
        user_query: User's question
        context_data: Resume/job context for better answers
    
    Returns:
        str: Mentor's response
    """
    prompt = f"""You are Sarah, a friendly and experienced Career Mentor with 15 years in tech recruiting and career coaching.

YOUR PERSONALITY:
- Warm, encouraging, and supportive
- Honest but tactful
- Uses examples and analogies
- Celebrates user's strengths while addressing weaknesses
- Like a knowledgeable friend giving advice

CONTEXT ABOUT USER:
{context_data[:1000] if context_data else "No context provided"}

USER'S QUESTION:
{user_query}

YOUR TASK:
Answer the user's question with:
1. Direct, actionable advice
2. Specific examples when helpful
3. Encouraging tone
4. Clear structure (use bullet points, bold text for readability)
5. Follow-up questions if needed to help better

RESPONSE GUIDELINES:
- Keep it conversational but professional
- Use emojis sparingly (1-2 max) for warmth
- Be honest about challenges but always provide solutions
- If discussing jobs, weigh pros and cons
- If discussing courses, explain career impact
- If correcting misconceptions, be gentle

YOUR RESPONSE:"""

    return safe_api_call(prompt, max_tokens=1200, temperature=0.7)

# ============================================================================
# BATCH PROCESSING (FOR FUTURE USE)
# ============================================================================

def batch_analyze_jobs(job_list):
    """
    Analyzes multiple jobs at once for comparison.
    
    Args:
        job_list: List of job descriptions
    
    Returns:
        list: Analysis for each job
    """
    results = []
    for idx, job in enumerate(job_list):
        print(f"Analyzing job {idx + 1}/{len(job_list)}...")
        analysis = analyze_job_with_ai(job)
        results.append(analysis)
    return results

# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def validate_api_connection():
    """
    Tests if API is working correctly.
    
    Returns:
        bool: True if API is working
    """
    try:
        test_prompt = "Reply with: API is working correctly"
        response = safe_api_call(test_prompt, max_tokens=50)
        return "working" in response.lower()
    except:
        return False

if __name__ == "__main__":
    # Test the API connection
    print("Testing AI Engine...")
    
    if validate_api_connection():
        print("✅ API Connection: Working")
        
        # Test roadmap generation
        print("\n📚 Testing Roadmap Generation...")
        roadmap = generate_roadmap("Python Programming", 7)
        topics = roadmap.split(';')
        print(f"Generated {len(topics)} topics:")
        for i, topic in enumerate(topics, 1):
            print(f"  Day {i}: {topic}")
    else:
        print("❌ API Connection: Failed")
        print("Check your GROQ_API_KEY in .env file")