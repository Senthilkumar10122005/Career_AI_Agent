import os
import streamlit as st
import pandas as pd
import pypdf
import io
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
import smtplib
from email.message import EmailMessage
import time
from supabase import create_client 

# Import your custom modules
import db # Updated import
import scraper
import ai_engine

# ============================================================================
# CONFIGURATION & INITIALIZATION
# ============================================================================

try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Credentials missing in .streamlit/secrets.toml")
    st.stop()

# System Prompt Initialization
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """
You are an expert AI Career Coach acting like a mini ChatGPT.
You help users with:
- Resume optimization
- Job description matching
- Skill gap analysis
- Interview preparation
- Career guidance

Rules:
- Be concise but insightful
- Use bullet points where helpful
- Give actionable advice
- Base answers strictly on Resume + Job Description when available
- Ask follow-up questions only if useful
"""

# Session State Initialization
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Login"
if 'page' not in st.session_state:
    st.session_state['page'] = "Dashboard"
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'ai_scratchpad' not in st.session_state:
    st.session_state['ai_scratchpad'] = ""
if 'last_analysis' not in st.session_state:
    st.session_state['last_analysis'] = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Page Configuration
try:
    img = Image.open("logo.png")
    st.set_page_config(page_title="Career AI Agent", page_icon=img, layout="wide")
except:
    st.set_page_config(page_title="Career AI Agent", layout="wide")

# ============================================================================
# CUSTOM CSS STYLING (ENHANCED)
# ============================================================================

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Font */
        * {
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar Branding */
        [data-testid="stSidebarNav"]::before {
            content: "Career AI";
            margin-left: 20px;
            margin-top: 20px;
            font-size: 30px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Modern Card Design */
        .modern-card {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(102, 126, 234, 0.1);
            margin-bottom: 20px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .modern-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(102, 126, 234, 0.15);
        }
        
        /* Section Headers */
        .section-header {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .section-subheader {
            font-size: 0.95rem;
            color: #6c757d;
            margin-bottom: 25px;
        }
        
        /* Job Cards */
        .job-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .job-card:hover {
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
            transform: translateX(5px);
        }
        
        .company-name {
            font-size: 1.3rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 5px;
        }
        
        .job-role {
            font-size: 1rem;
            font-weight: 500;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #667eea;
        }
        
        /* AI Scratchpad */
        .ai-scratchpad-header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            padding: 20px;
            border-radius: 15px 15px 0 0;
            color: white;
        }
        
        .ai-scratchpad-body {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 20px;
            border-radius: 0 0 15px 15px;
            max-height: 300px;
            overflow-y: auto;
            font-size: 14px;
            color: #374151;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }
        
        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* Progress Bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: 600;
            font-size: 1.05rem;
        }
        
        /* Divider Enhancement */
        hr {
            margin: 30px 0;
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent, #667eea, transparent);
        }
        
        /* Status Badge */
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .badge-saved { background: #e0e7ff; color: #3730a3; }
        .badge-applied { background: #dbeafe; color: #1e40af; }
        .badge-interview { background: #fef3c7; color: #92400e; }
        .badge-offer { background: #d1fae5; color: #065f46; }
        .badge-rejected { background: #fee2e2; color: #991b1b; }
        .badge-tailored { background: #e9d5ff; color: #6b21a8; }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def send_instant_guide(recipient_email, course_name):
    """Send professional email guide for course enrollment"""
    try:
        EMAIL_ADDR = st.secrets["EMAIL_USER"]
        EMAIL_PASS = st.secrets["EMAIL_PASS"]

        msg = EmailMessage()
        msg['Subject'] = f"🚀 Your {course_name} Learning Blueprint"
        msg['From'] = f"AI Career Agent <{EMAIL_ADDR}>"
        msg['To'] = recipient_email

        html_content = f"""
        <html>
            <body style="margin: 0; padding: 0; font-family: 'Inter', sans-serif; background-color: #f4f7f9;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7f9; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                                <tr style="background: linear-gradient(135deg, #667eea, #764ba2);">
                                    <td style="padding: 40px 20px; text-align: center;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Career AI Agent</h1>
                                        <p style="color: #e0f0ff; margin: 10px 0 0 0;">Personalized Learning Path</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 40px 30px; color: #333333;">
                                        <h2 style="color: #667eea; margin-top: 0;">Target: {course_name}</h2>
                                        <p>Hello,</p>
                                        <p>You requested a curated learning guide. Here is your <b>{course_name}</b> starter kit:</p>
                                        <div style="background-color: #f8f9fa; border-left: 4px solid #667eea; padding: 20px; margin: 25px 0;">
                                            <p style="margin: 0 0 10px 0;"><b>📍 Step 1:</b> Follow the <a href="https://roadmap.sh" style="color: #667eea;">Skill Roadmap</a></p>
                                            <p style="margin: 0 0 10px 0;"><b>📺 Step 2:</b> Watch Video Modules in your Dashboard.</p>
                                            <p style="margin: 0;"><b>📊 Step 3:</b> Update Resume via AI Chat.</p>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        msg.set_content("HTML Email")
        msg.add_alternative(html_content, subtype='html')
        
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(EMAIL_ADDR, EMAIL_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Mail failed: {e}")
        return False

def get_status_badge(status):
    """Returns styled HTML badge for job status"""
    status_classes = {
        "Saved": "badge-saved",
        "Applied": "badge-applied",
        "Interviewing": "badge-interview",
        "Interview": "badge-interview",
        "Offer": "badge-offer",
        "Rejected": "badge-rejected",
        "Tailored": "badge-tailored"
    }
    badge_class = status_classes.get(status, "badge-saved")
    return f'<span class="status-badge {badge_class}">{status}</span>'

def initialize_system():
    """Initialize database and default user"""
    db.init_db() 
    db.update_tables()  # Run migrations
    user_data = db.verify_user("senthil33", "Senthil111327@#")
    if not user_data:
        db.create_user("senthil33", "Senthil111327@#", email="senthilmohan111327@gmail.com")

initialize_system()

# Persistent Login via URL params
if "user" in st.query_params:
    if not st.session_state.get('logged_in'):
        st.session_state['logged_in'] = True
        st.session_state['username'] = st.query_params["user"]
        st.session_state['role'] = st.query_params.get("role", "user")

# ============================================================================
# AUTHENTICATION SCREEN
# ============================================================================

if not st.session_state.get('logged_in'):
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🛡️ AI Career Agent</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6c757d; font-size: 1.1rem;'>Secure Access Portal</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Clean tab-based authentication
    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])
    
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h3 style='text-align: center;'>Sign In</h3>", unsafe_allow_html=True)
            st.caption("Enter your credentials to access your dashboard.")
            
            u = st.text_input("Username", placeholder="e.g. hardikpandya33", key="login_user")
            p = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass")
            
            if st.button("Sign In", use_container_width=True, type="primary", key="login_btn"):
                user_data = db.verify_user(u, p)
                if user_data:
                    st.session_state.update({'logged_in': True, 'username': user_data[0], 'role': user_data[1]})
                    st.query_params.update({"user": user_data[0], "role": user_data[1]})
                    st.success(f"Welcome back, {user_data[0]}!")
                    time.sleep(1)
                    st.rerun()
                else: 
                    st.error("❌ Invalid Username or Password. Please try again.")

    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<h3 style='text-align: center;'>Create Account</h3>", unsafe_allow_html=True)
            st.caption("Join the AI Career Agent to track your goals and optimize your resume.")
            
            new_u = st.text_input("Choose Username", placeholder="Pick a unique name", key="reg_user")
            new_p = st.text_input("Choose Password", type="password", placeholder="Strong password", key="reg_pass")
            new_e = st.text_input("Email (Required for Daily Goals)", placeholder="email@example.com", key="reg_email")
            
            if st.button("Create My Account 🚀", use_container_width=True, type="primary", key="reg_btn"):
                if new_u and new_p and new_e:
                    success, msg = db.create_user(new_u, new_p, email=new_e)
                    if success:
                        st.balloons()
                        st.success("Account created successfully! Please login.")
                        time.sleep(2)
                        st.rerun()
                    else: 
                        st.error(f"⚠️ {msg}")
                else: 
                    st.warning("⚠️ Please fill in all required fields (Username, Password, and Email).")

    st.stop()

# ============================================================================
# SIDEBAR NAVIGATION (Protected)
# ============================================================================

page = st.session_state.get('page', 'Dashboard')

if 'username' in st.session_state and st.session_state['username']:
    with st.sidebar:
        # User Profile Header with Stats
        user_role = str(st.session_state.get('role', 'User')).upper()
        badge_color = "#FF4A4B" if user_role == "ADMIN" else "#667eea"
        
        # Get user statistics
        user_stats = db.get_user_stats(st.session_state['username'])

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 15px; margin-bottom: 20px;">
                <h2 style="margin:0; color: white; font-size: 22px;">👤 {st.session_state['username']}</h2>
                <div style="margin-top: 10px;">
                    <span style="color: #e0f0ff; font-size: 14px;">Access Level: </span>
                    <span style="background: {badge_color}; color: white; 
                                 padding: 4px 12px; border-radius: 20px; 
                                 font-size: 13px; font-weight: 600;">
                        {user_role}
                    </span>
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #e0f0ff; font-size: 13px;">🎯 Active Goals</span>
                        <span style="color: white; font-weight: 600; font-size: 13px;">{user_stats.get('active_goals', 0)}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #e0f0ff; font-size: 13px;">📝 Applications</span>
                        <span style="color: white; font-weight: 600; font-size: 13px;">{user_stats.get('total_applications', 0)}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Navigation Menu
        user_role_lower = str(st.session_state.get('role', 'user')).lower()
        
        menu = {
            "🏠 Dashboard": "Dashboard",
            "🔬 AI Research Lab": "AI Lab",
            "🎓 Learning Hub": "In-Demand Courses",
            "🎯 Goal Tracker": "Goal Tracker"
        }
        
        if user_role_lower == "admin":
            menu["🛡️ Admin Center"] = "Admin Tools"

        st.markdown("<p style='font-size: 0.85rem; color: #6c757d; margin-bottom: 10px;'>NAVIGATE</p>", unsafe_allow_html=True)
        
        for label, page_name in menu.items():
            if st.button(label, use_container_width=True, key=f"nav_{page_name}"):
                st.session_state['page'] = page_name
                st.rerun()

        st.divider()

        # Quick Actions
        if st.button("🚪 Log Out", type="primary", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================

if page == "Dashboard":
    st.markdown("<h1 class='section-header'>🚀 Career Command Center</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-subheader'>Your personalized career intelligence dashboard</p>", unsafe_allow_html=True)
    
    # Fetch saved jobs
    try:
        response = supabase.table("job_applications").select("*").execute()
        saved_jobs_data = response.data
    except Exception as e:
        st.error(f"Database sync error: {e}")
        saved_jobs_data = []
    
    total_saved = len(saved_jobs_data) if saved_jobs_data else 0
    
    # Top Metrics - Enhanced with new database features
    user_stats = db.get_user_stats(st.session_state['username'])
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Saved Jobs", user_stats.get('total_applications', 0), delta="Active")
    with m2:
        applied_count = user_stats.get('applied_jobs', 0)
        st.metric("Applied", applied_count, delta=f"{applied_count}/{total_saved}")
    with m3:
        st.metric("Learning Goals", user_stats.get('active_goals', 0), delta="In Progress")
    with m4:
        st.metric("AI Status", "Online", delta="Live")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================================================
    # SECTION 1: SKILL GAP ANALYSIS
    # ========================================================================
    
    st.markdown("<h2 class='section-header'>📊 Skill Gap Analysis</h2>", unsafe_allow_html=True)
    
    if total_saved > 0:
        latest_job = saved_jobs_data[-1]
        
        st.markdown(f"""
            <div class="modern-card">
                <p style="margin: 0; font-size: 0.9rem; color: #6c757d;">Target Position</p>
                <h3 style="margin: 5px 0 0 0; font-size: 1.3rem; color: #1a1a1a;">
                    {latest_job.get('role', 'N/A')} at {latest_job.get('company', 'N/A')}
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("🤖 AI analyzing skill requirements..."):
            req_skills = ai_engine.extract_dynamic_skills(latest_job.get('description', ''))
            user_resume = st.session_state.get('resume_text', "").lower()
            
            # Prepare chart data
            chart_data = []
            for skill in req_skills:
                if skill.lower() in user_resume:
                    chart_data.append({"Skill": skill, "Level": 100, "Status": "Proficient"})
                else:
                    chart_data.append({"Skill": skill, "Level": 20, "Status": "Learning Required"})
            
            df_skills = pd.DataFrame(chart_data)
            
            # Enhanced Plotly Chart
            fig = go.Figure()
            
            # Add bars with custom colors
            colors = ['#10b981' if level == 100 else '#ef4444' for level in df_skills['Level']]
            
            fig.add_trace(go.Bar(
                x=df_skills['Skill'],
                y=df_skills['Level'],
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(255, 255, 255, 0.5)', width=2)
                ),
                text=df_skills['Level'],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Proficiency: %{y}%<extra></extra>'
            ))
            
            fig.update_layout(
                height=450,
                margin=dict(l=20, r=20, t=40, b=100),
                xaxis=dict(
                    tickangle=-45,
                    title="",
                    showgrid=False
                ),
                yaxis=dict(
                    range=[0, 110],
                    title="Proficiency Level (%)",
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.05)'
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', size=12),
                showlegend=False,
                title=dict(
                    text="<b>Your Skill Match vs Job Requirements</b>",
                    font=dict(size=16, color='#1a1a1a'),
                    x=0.5,
                    xanchor='center'
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show missing skills
            missing_skills = [s for s in req_skills if s.lower() not in user_resume]
            if missing_skills:
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fef3c7, #fcd34d); 
                                padding: 15px; border-radius: 10px; 
                                border-left: 4px solid #f59e0b;">
                        <p style="margin: 0; font-weight: 600; color: #92400e;">
                            💡 <strong>Focus Areas:</strong> {', '.join(missing_skills)}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="modern-card" style="text-align: center; padding: 40px;">
                <h3 style="color: #6c757d;">📭 No Jobs Saved Yet</h3>
                <p style="color: #adb5bd;">Head to the AI Research Lab to start analyzing job postings!</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # ========================================================================
    # SECTION 2: LIVE JOB DISCOVERY
    # ========================================================================
    
    st.markdown("<h2 class='section-header'>🌍 Live Job Discovery</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subheader'>Search real-time opportunities worldwide</p>", unsafe_allow_html=True)
    
    with st.container():
        
        
        col_l, col_c, col_s = st.columns([2, 1.5, 1])
        
        with col_l:
            loc = st.text_input("🌆 Target Location", value="Chennai", placeholder="City or State", key="job_location")
        with col_c:
            coun = st.selectbox(
                "🌐 Country", 
                [("India", "in"), ("USA", "us"), ("UK", "gb"), ("Canada", "ca"), ("Australia", "au")],
                format_func=lambda x: x[0],
                key="job_country"
            )
        with col_s:
            st.markdown("<br>", unsafe_allow_html=True)
            search_trigger = st.button("🔍 Search", use_container_width=True, type="primary", key="job_search")
    

    if search_trigger:
        with st.spinner("🔎 Scanning job markets..."):
            live_feed = scraper.fetch_live_job_feed(loc, coun[1])
            
            if live_feed:
                st.markdown(f"<p style='color: #10b981; font-weight: 600;'>✅ Found {len(live_feed)} opportunities</p>", unsafe_allow_html=True)
                
                for idx, job in enumerate(live_feed):
                    st.markdown(f"""
                        <div class="job-card">
                            <div class="company-name">{job.get('company', {}).get('display_name', 'Company')}</div>
                            <div class="job-role">{job.get('title', 'Job Title')}</div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([4, 1, 1])
                    
                    with c1:
                        location_info = job.get('location', {}).get('display_name', 'Location not specified')
                        st.caption(f"📍 {location_info}")
                    
                    with c2:
                        st.link_button("🌐 View", job.get('redirect_url', '#'), use_container_width=True)
                    
                    with c3:
                        if st.button("💾 Save", key=f"feed_{job.get('id')}_{idx}", use_container_width=True):
                            try:
                                new_job = {
                                    "company": job.get('company', {}).get('display_name', 'Company'),
                                    "role": job.get('title', 'Job Role'),
                                    "url": job.get('redirect_url', ''),
                                    "description": job.get('description', 'Scraped from live feed'),
                                    "status": "Saved"
                                }
                                supabase.table("job_applications").insert(new_job).execute()
                                st.toast(f"✅ Saved {new_job['role']}!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Save failed: {e}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No jobs found for this search. Try different keywords or location.")

# ============================================================================
# PAGE 2: AI RESEARCH LAB
# ============================================================================

elif page == "AI Lab":
    st.markdown("<h1 class='section-header'>🔬 AI Research Lab</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-subheader'>Deep intelligence extraction from job postings</p>", unsafe_allow_html=True)
    
    tab_ai, tab_manual, tab_board = st.tabs(["✨ AI Intelligence", "📝 Manual Entry", "📋 Career Board"])
    
    # ========================================================================
    # TAB 1: AI URL SCRAPER
    # ========================================================================
    
    with tab_ai:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        
        target_url = st.text_input(
            "🔗 Job Posting URL", 
            key="lab_url_input", 
            placeholder="Paste LinkedIn, Indeed, or company career page link"
        )
        
        if st.button("🪄 Run Deep Analysis", use_container_width=True, type="primary", key="ai_analyze"):
            if target_url:
                with st.spinner("🤖 AI is reading and analyzing..."):
                    scraped = scraper.scrape_job_details(target_url)
                    if scraped:
                        st.session_state['ai_scratchpad'] = ai_engine.analyze_job_with_ai(scraped)
                        metadata = ai_engine.extract_metadata(scraped)
                        st.session_state['extracted_info'] = metadata
                        st.toast(f"✅ Captured: {metadata['company']}!", icon="🪄")
                        st.rerun()
                    else:
                        st.error("❌ Could not extract data from URL. Please check the link.")
            else:
                st.warning("Please enter a URL first.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Digital Scratchpad
        if st.session_state.get('ai_scratchpad'):
            st.markdown("""
                <div class="ai-scratchpad-header">
                    <h3 style='margin:0; font-size:16px;'>💎 AI Professional Breakdown</h3>
                    <p style='margin:5px 0 0 0; font-size:12px; opacity:0.9;'>Review before saving to dashboard</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"<div class='ai-scratchpad-body'>{st.session_state['ai_scratchpad']}</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_clear = st.columns(2)
            
            with col_save:
                if st.button("📥 Save to Dashboard", use_container_width=True, type="primary", key="save_scratchpad"):
                    info = st.session_state.get('extracted_info', {"company": "New Company", "role": "Job Role"})
                    
                    payload = {
                        "company": info['company'],
                        "role": info['role'],
                        "description": st.session_state['ai_scratchpad'],
                        "status": "Saved",
                        "url": target_url
                    }
                    
                    try:
                        supabase.table("job_applications").insert(payload).execute()
                        st.toast(f"✅ Saved {info['company']} to Dashboard!")
                        st.session_state['ai_scratchpad'] = ""
                        st.rerun()
                    except Exception as e:
                        st.error(f"Save failed: {e}")
                        
            with col_clear:
                if st.button("🗑️ Discard", use_container_width=True, key="clear_scratchpad"):
                    st.session_state['ai_scratchpad'] = ""
                    st.rerun()
    
    # ========================================================================
    # TAB 2: MANUAL JOB ENTRY
    # ========================================================================
    
    with tab_manual:
        st.markdown("<h3 style='margin-bottom: 20px;'>➕ Add Job Manually</h3>", unsafe_allow_html=True)
        
        with st.form("manual_job_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                company = st.text_input("Company Name*", placeholder="e.g. Google")
                role = st.text_input("Job Role*", placeholder="e.g. Frontend Developer")
            with col2:
                status = st.selectbox("Status", ["Saved", "Applied", "Interviewing", "Offer", "Rejected"])
                job_url = st.text_input("Job URL", placeholder="https://...")

            job_desc = st.text_area("Job Description*", placeholder="Paste requirements here...", height=150)
            submit_job = st.form_submit_button("💼 Save to Career Board", use_container_width=True, type="primary")

        if submit_job:
            if company and role and job_desc:
                new_job = {
                    "company": company,
                    "role": role,
                    "status": status,
                    "url": job_url,
                    "description": job_desc
                }
                try:
                    result = supabase.table("job_applications").insert(new_job).execute()
                    if result.data:
                        st.balloons()
                        st.success(f"🎯 Saved {role} at {company}!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save: {e}")
            else:
                st.warning("⚠️ Please fill in all required fields.")
    
    # ========================================================================
    # TAB 3: CAREER BOARD (Resume Tailoring) - ENHANCED WITH NEW DB FEATURES
    # ========================================================================
    
    with tab_board:
        st.markdown("<h3 style='margin-bottom: 20px;'>🎯 Resume Tailoring Station</h3>", unsafe_allow_html=True)
        
        # Fetch saved jobs
        try:
            response = supabase.table("job_applications").select("*").execute()
            saved_jobs_data = response.data
        except Exception as e:
            st.error(f"Database error: {e}")
            saved_jobs_data = []
        
        if saved_jobs_data:
            # Dashboard Metrics - Enhanced
            user_stats = db.get_user_stats(st.session_state['username'])
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Saved", user_stats.get('total_applications', 0))
            m2.metric("Applied", user_stats.get('applied_jobs', 0))
            tailored_count = sum(1 for j in saved_jobs_data if j.get('status') == 'Tailored')
            m3.metric("Tailored", tailored_count)
            m4.metric("Weekly Goal", "10 Apps")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Status Filter
            col_filter, col_search = st.columns([1, 3])
            with col_filter:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Saved", "Applied", "Tailored", "Interviewing", "Offer", "Rejected"],
                    key="status_filter"
                )
            
            # Filter jobs
            filtered_jobs = saved_jobs_data
            if status_filter != "All":
                filtered_jobs = [j for j in saved_jobs_data if j.get('status') == status_filter]
            
            # Job Cards with enhanced status display
            for job in filtered_jobs:
                st.markdown(f"""
                    <div class="job-card">
                        <div class="company-name">{job.get('company', 'Unknown')}</div>
                        <div class="job-role">{job.get('role', 'Position')}</div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 1])
                
                with c1:
                    current_status = job.get('status', 'Saved')
                    st.markdown(get_status_badge(current_status), unsafe_allow_html=True)

                with c2:
                    new_status = st.selectbox(
                        "Update Status",
                        ["Saved", "Applied", "Tailored", "Interviewing", "Offer", "Rejected"],
                        index=["Saved", "Applied", "Tailored", "Interviewing", "Offer", "Rejected"].index(current_status) if current_status in ["Saved", "Applied", "Tailored", "Interviewing", "Offer", "Rejected"] else 0,
                        key=f"status_{job['id']}",
                        label_visibility="collapsed"
                    )
                    if new_status != current_status:
                        if db.update_job_status(job['id'], new_status):
                            supabase.table("job_applications").update({"status": new_status}).eq("id", job['id']).execute()
                            st.toast(f"Status updated to {new_status}!")
                            time.sleep(0.5)
                            st.rerun()
                
                with c3:
                    with st.expander("📄"):
                        st.write(job.get('description', 'No description'))
                
                with c4:
                    if st.button("🎯", key=f"tailor_{job['id']}", help="Tailor Resume"):
                        st.session_state['active_job'] = job
                        st.toast(f"Loading {job['company']}...")
                        st.rerun()

                with c5:
                    if st.button("🗑️", key=f"del_{job['id']}", help="Remove"):
                        supabase.table("job_applications").delete().eq("id", job['id']).execute()
                        if st.session_state.get('active_job', {}).get('id') == job['id']:
                            st.session_state['active_job'] = None
                        st.toast("Deleted!")
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Resume Uploader Section
            if st.session_state.get('active_job'):
                current_job = st.session_state['active_job']
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"<h3>🛠️ Tailoring for: <span style='color: #667eea;'>{current_job['company']}</span></h3>", unsafe_allow_html=True)
                
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                
                res_file = st.file_uploader("Upload Resume (PDF)", type="pdf", key="resume_uploader")
                
                if res_file:
                    st.caption(f"✅ File loaded: {res_file.name}")
                    
                    if st.button("🚀 Run AI Matcher", use_container_width=True, type="primary", key="run_matcher"):
                        with st.spinner("🤖 Analyzing skill gaps..."):
                            pdf_reader = pypdf.PdfReader(res_file)
                            resume_content = "".join([p.extract_text() for p in pdf_reader.pages])
                            st.session_state['resume_text'] = resume_content
                            
                            target_jd_text = current_job.get('description', '')
                            
                            analysis = ai_engine.match_resume_to_job(resume_content, target_jd_text)
                            st.session_state['last_analysis'] = analysis
                            
                            # Update status to Tailored
                            db.update_job_status(current_job['id'], "Tailored")
                            supabase.table("job_applications").update({"status": "Tailored"}).eq("id", current_job['id']).execute()
                            st.toast("✅ Analysis complete!")
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # AI Analysis Display
            if st.session_state.get('last_analysis'):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<h3>📊 AI Matching Report</h3>", unsafe_allow_html=True)
                
                st.markdown(f"""
                    <div class="modern-card">
                        {st.session_state['last_analysis']}
                    </div>
                """, unsafe_allow_html=True)
                
                # AI Career Mentor Chat
                st.markdown("<h3>💬 Career AI Mentor</h3>", unsafe_allow_html=True)
                
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                chat_query = st.chat_input("Ask about resume improvements or request a LaTeX boost...")

                if chat_query:
                    with st.chat_message("user"):
                        st.markdown(chat_query)
                    st.session_state.messages.append({"role": "user", "content": chat_query})

                    with st.chat_message("assistant"):
                        is_boost_req = any(w in chat_query.lower() for w in ["resume", "boost", "fix", "latex"])
                        
                        if is_boost_req:
                            with st.spinner("🖋️ Crafting LaTeX resume..."):
                                target_jd_text = st.session_state['active_job'].get('description', '')
                                response = ai_engine.generate_latex_resume(
                                    st.session_state.get('resume_text', ''), 
                                    target_jd_text
                                )
                                st.markdown("### ✅ LLM Boost Applied")
                                st.code(response, language='latex')
                        else:
                            target_jd_text = st.session_state['active_job'].get('description', '')
                            response = ai_engine.career_mentor_chat(chat_query, context_data=target_jd_text)
                            st.markdown(response)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response})
        
        else:
            st.markdown("""
                <div class="modern-card" style="text-align: center; padding: 40px;">
                    <h3>📭 No Saved Jobs</h3>
                    <p>Use the AI Intelligence tab to start analyzing opportunities!</p>
                </div>
            """, unsafe_allow_html=True)

# ============================================================================
# PAGE 3: LEARNING HUB (IN-DEMAND COURSES)
# ============================================================================

elif page == "In-Demand Courses":
    st.markdown("<h1 class='section-header'>🎓 Professional Learning Hub</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-subheader'>Curated courses with instant email delivery</p>", unsafe_allow_html=True)
    
    course_data = {
        "Python & AI": {
            "Coursera": "https://www.coursera.org/learn/python-for-everybody", 
            "YouTube": "https://youtu.be/m67-bOpOoPU?si=lvJ8otsfB9zak52J"
        },
        "Data Science": {
            "Coursera": "https://www.coursera.org/learn/data-science", 
            "YouTube": "https://www.youtube.com/watch?v=ua-CiDNNj30"
        },
        "Cloud Computing": {
            "Coursera": "https://www.coursera.org/learn/cloud-computing", 
            "YouTube": "https://www.youtube.com/watch?v=SOTamCETW04"
        },
        "Web Development": {
            "Coursera": "https://www.coursera.org/learn/web-design-for-everybody", 
            "YouTube": "https://www.youtube.com/watch?v=kDyJN7Y5DyU"
        },
        "Machine Learning": {
            "Coursera": "https://www.coursera.org/learn/machine-learning", 
            "YouTube": "https://www.youtube.com/watch?v=PeMlggy_ftU"
        },
        "Cybersecurity": {
            "Coursera": "https://www.coursera.org/learn/cybersecurity-fundamentals", 
            "YouTube": "https://www.youtube.com/watch?v=jVO06FyIjKY"
        },
        "DevOps": {
            "Coursera": "https://www.coursera.org/learn/devops-and-software-engineering", 
            "YouTube": "https://www.youtube.com/watch?v=j5Zsa_eOXeY"
        },
        "Data Engineering": {
            "Coursera": "https://www.coursera.org/learn/data-engineering", 
            "YouTube": "https://www.youtube.com/watch?v=M3P-63PBOE4"
        },
    }
    
    # Course Grid
    for course, links in course_data.items():
       
        
        st.markdown(f"<h3 style='margin-bottom: 15px;'>📖 {course}</h3>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.link_button("🎓 Coursera", links["Coursera"], use_container_width=True)
        
        with c2:
            st.link_button("📺 YouTube", links["YouTube"], use_container_width=True)
        
        with c3:
            if st.button(f"📧 Email Guide", key=f"email_{course}", use_container_width=True):
                user_email = db.get_user_email(st.session_state['username'])
                if user_email:
                    with st.spinner("Sending..."):
                        if send_instant_guide(user_email, course):
                            st.toast(f"✅ Guide sent to {user_email}!", icon="📧")
                        else:
                            st.error("Email failed")
                else:
                    st.error("Email not found")
        
        # Start Learning Journey Button
        if st.button(f"🚀 Start {course} Journey", key=f"start_{course}", use_container_width=True, type="primary"):
            default_syllabus = f"Introduction to {course};Basic Concepts;Intermediate Tools;Advanced Project;Final Review"
            db.add_goal(st.session_state['username'], f"GUIDE: {course}", 5, default_syllabus)
            st.balloons()
            st.toast(f"Journey started for {course}!", icon="🎯")
            time.sleep(2)
            st.rerun()
        

# ============================================================================
# PAGE 4: GOAL TRACKER
# ============================================================================

elif page == "Goal Tracker":
    st.markdown("<h1 class='section-header'>🎯 Learning Journey Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-subheader'>AI-powered roadmaps with daily email modules</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="modern-card" style="background: linear-gradient(135deg, #fef3c7, #fcd34d);">
            <p style="margin: 0; color: #92400e; font-size: 1rem;">
                📬 <strong>Daily Learning:</strong> Pick a subject and receive AI-generated modules 
                every morning at 8:00 AM IST in your inbox.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Goal Creation Form
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("<h3>🚀 Start New Journey</h3>", unsafe_allow_html=True)
    
    with st.form("goal_form"):
        g_name = st.text_input("Subject to Master", placeholder="e.g. Python for DevOps, Cloud Architecture")
        g_days = st.number_input("Duration (Days)", min_value=5, max_value=90, value=30)
        
        if st.form_submit_button("Generate Roadmap 🪄", use_container_width=True, type="primary"):
            if g_name:
                with st.spinner(f"🤖 Architecting your {g_days}-day syllabus..."):
                    syllabus = ai_engine.generate_roadmap(g_name, g_days)
                    db.add_goal(st.session_state['username'], g_name, g_days, syllabus)
                    st.snow()
                    st.balloons()
                    st.toast(f"Journey created for {g_name}!", icon="✅")
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Please enter a subject.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Active Journeys
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3>📚 Your Active Journeys</h3>", unsafe_allow_html=True)
    
    active_goals = db.get_user_goals(st.session_state['username'])
    
    if not active_goals:
        st.markdown("""
            <div class="modern-card" style="text-align: center; padding: 40px;">
                <h3>📭 No Active Journeys</h3>
                <p>Create one above to start your learning path!</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for g in active_goals:
            goal_id, title, start_date, total_days, is_active, syllabus = g
            
            # Calculate progress
            start_dt = datetime.strptime(str(start_date), '%Y-%m-%d')
            days_passed = (datetime.now() - start_dt).days
            current_day = days_passed + 1
            progress_pct = min(max(current_day / total_days, 0.0), 1.0)
            
            display_title = title.replace("GUIDE: ", "")
            
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            
            # Header
            col_title, col_archive, col_del = st.columns([4, 1, 1])
            with col_title:
                st.markdown(f"<h4 style='margin: 0;'>📅 {display_title}</h4>", unsafe_allow_html=True)
                st.caption(f"Day {min(current_day, total_days)} of {total_days}")
            with col_archive:
                if st.button("📦", key=f"archive_{goal_id}", help="Archive Journey"):
                    if db.deactivate_goal(goal_id):
                        st.toast("Journey archived")
                        st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{goal_id}", help="Delete Journey"):
                    if db.delete_goal_by_id(goal_id):
                        st.toast("Journey removed")
                        st.rerun()
            
            # Progress Bar
            st.progress(progress_pct, text=f"Progress: {int(progress_pct * 100)}%")
            
            # Syllabus
            if syllabus:
                with st.expander("📖 View Full Syllabus"):
                    raw_topics = syllabus.split(';')
                    clean_topics = [t.strip() for t in raw_topics if t.strip() and "Not specified" not in t]
                    
                    for i, topic in enumerate(clean_topics):
                        day_num = i + 1
                        
                        if day_num < current_day:
                            st.markdown(f"✅ <span style='color:gray;'>Day {day_num}: {topic}</span>", unsafe_allow_html=True)
                        elif day_num == current_day:
                            st.markdown(f"🎯 **Day {day_num}: {topic}** <span style='color:#667eea;'>(TODAY)</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"⚪ Day {day_num}: {topic}")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# PAGE 5: ADMIN TOOLS (ENHANCED)
# ============================================================================

elif page == "Admin Tools":
    if 'role' in st.session_state and st.session_state['role'].lower() == "admin":
        st.markdown("<h1 class='section-header'>🛡️ Admin Command Center</h1>", unsafe_allow_html=True)
        
        # Metrics
        all_users = db.get_all_users()
        total_users = len(all_users) if all_users else 0
        all_goals = db.get_all_active_goals_global()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Users", total_users)
        m2.metric("Active Goals", len(all_goals) if all_goals else 0)
        m3.metric("System Status", "Live", delta="Active")
        m4.metric("DB Provider", "Supabase")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # User Management
        st.markdown("<h3>👥 User Directory</h3>", unsafe_allow_html=True)
        
        if all_users:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            
            df = pd.DataFrame(all_users, columns=["Username", "Role", "Email"])
            
            col_search, col_export = st.columns([3, 1])
            with col_search:
                search = st.text_input("🔍 Search users", placeholder="Type username or email...", key="user_search")
            with col_export:
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    "📥 Export CSV",
                    df.to_csv(index=False),
                    "users.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            if search:
                df = df[df['Username'].str.contains(search, case=False) | 
                       df['Email'].str.contains(search, case=False)]
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No users registered yet.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # All Goals Overview
        st.markdown("<h3>🎯 All Learning Journeys</h3>", unsafe_allow_html=True)
        
        if all_goals:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            goals_df = pd.DataFrame(all_goals, columns=["Username", "Goal", "Start Date", "Days", "Syllabus", "Email"])
            goals_df = goals_df.drop(columns=["Syllabus"])  # Remove syllabus for cleaner view
            st.dataframe(goals_df, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No active goals in the system.")
        
        # Danger Zone
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3>⚠️ Danger Zone</h3>", unsafe_allow_html=True)
        
        with st.expander("🗑️ Delete User Permanently"):
            st.error("⚠️ **WARNING**: This action cannot be undone. All user data (goals, applications) will be permanently deleted due to CASCADE constraints.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_select, col_confirm = st.columns([2, 1])
            
            with col_select:
                if all_users:
                    usernames = [u[0] for u in all_users if u[0] != "senthil33"]  # Exclude admin
                    user_to_del = st.selectbox(
                        "Select user to delete",
                        [""] + usernames,
                        key="admin_del_select"
                    )
            
            with col_confirm:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Delete User", type="primary", use_container_width=True, key="confirm_delete"):
                    if user_to_del and user_to_del != "":
                        if user_to_del == "senthil33":
                            st.error("❌ Cannot delete primary admin")
                        else:
                            with st.spinner(f"Deleting {user_to_del}..."):
                                if db.delete_user(user_to_del):
                                    st.success(f"✅ User '{user_to_del}' and all associated data deleted successfully!")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete user. Check logs for details.")
                    else:
                        st.warning("Please select a user first.")
    else:
        st.error("🚫 Access Denied")
        st.info("You need admin privileges to access this page.")