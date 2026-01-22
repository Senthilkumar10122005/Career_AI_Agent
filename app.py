import streamlit as st
import pandas as pd
import pypdf
import io
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import plotly.express as px
import smtplib
from email.message import EmailMessage
import time
# Import your custom modules
import db
import scraper
import ai_engine

    
    # --- 1. INITIALIZATION & PERSISTENCE ---
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Login" 


try:
    img = Image.open("logo.png")
    st.set_page_config(page_title="Career AI Agent", page_icon=img, layout="wide")
except:
    st.set_page_config(page_title="Career AI Agent", layout="wide")

# Custom Styles (Your Original CSS)
st.markdown("""
    <style>
        [data-testid="stSidebarNav"]::before {
            content: "Career AI";
            margin-left: 20px;
            margin-top: 20px;
            font-size: 30px;
            font-weight: bold;
            color: #007bff;
        }
    </style>
""", unsafe_allow_html=True)

# NEW FEATURE: Professional Instant Email Function
def send_instant_guide(recipient_email, course_name):
    try:
        EMAIL_ADDR = st.secrets["EMAIL_USER"]
        EMAIL_PASS = st.secrets["EMAIL_PASS"]

        msg = EmailMessage()
        msg['Subject'] = f"🚀 Your {course_name} Learning Blueprint"
        msg['From'] = f"AI Career Agent <{EMAIL_ADDR}>"
        msg['To'] = recipient_email

        html_content = f"""
        <html>
            <body style="margin: 0; padding: 0; font-family: sans-serif; background-color: #f4f7f9;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7f9; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                                <tr style="background: linear-gradient(135deg, #007bff, #00d4ff);">
                                    <td style="padding: 40px 20px; text-align: center;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">Career AI Agent</h1>
                                        <p style="color: #e0f0ff; margin: 10px 0 0 0;">Personalized Learning Path</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 40px 30px; color: #333333;">
                                        <h2 style="color: #007bff; margin-top: 0;">Target: {course_name}</h2>
                                        <p>Hello,</p>
                                        <p>You requested a curated learning guide. Here is your <b>{course_name}</b> starter kit:</p>
                                        <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 20px; margin: 25px 0;">
                                            <p style="margin: 0 0 10px 0;"><b>📍 Step 1:</b> Follow the <a href="https://roadmap.sh">Skill Roadmap</a></p>
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
       # Use Port 587 with STARTTLS (Better for local machines)
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls() # Secure the connection
            smtp.ehlo()
            smtp.login(EMAIL_ADDR, EMAIL_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Mail failed: {e}")
        return False

# Persistent Login logic (Your Original)
if "user" in st.query_params:
    if not st.session_state.get('logged_in'):
        st.session_state['logged_in'] = True
        st.session_state['username'] = st.query_params["user"]
        st.session_state['role'] = st.query_params.get("role", "user")

def initialize_system():
    db.init_db() 
    user_data = db.verify_user("senthil33", "Senthil111327@#")
    if not user_data:
        db.create_user("senthil33", "Senthil111327@#", email="senthilmohan111327@gmail.com")

initialize_system()

# State Management (Your Original)
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'ai_scratchpad' not in st.session_state: st.session_state['ai_scratchpad'] = ""
if 'last_analysis' not in st.session_state: st.session_state['last_analysis'] = None


# --- 2. AUTHENTICATION UI (ENHANCED) ---

if not st.session_state.get('logged_in'):
    st.title("🛡️ AI Career Agent: Secure Access")
    

    auth_choice = st.radio(
        "Welcome! Please identify yourself:", 
        ["Login", "Register"], 
        key="auth_mode", # This key links directly to st.session_state["auth_mode"]
        horizontal=True,
        help="New users should select 'Register' to create an account."
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if auth_choice == "Login":
            st.subheader("🔑 Sign In")
            st.caption("Enter your credentials to access your dashboard.")
            
            u = st.text_input("Username", placeholder="e.g. hardikpandya33")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            
            if st.button("Sign In", use_container_width=True, type="primary"):
                user_data = db.verify_user(u, p)
                if user_data:
                    st.session_state.update({'logged_in': True, 'username': user_data[0], 'role': user_data[1]})
                    st.query_params.update({"user": user_data[0], "role": user_data[1]})
                    st.success(f"Welcome back, {user_data[0]}!")
                    st.rerun()
                else: 
                    st.error("❌ Invalid Username or Password. Please try again.")
            
            st.info("💡 New here? Select 'Register' above to get started.")

        else:
            st.subheader("🆕 Create Account")
            st.caption("Join the AI Career Agent to track your goals and optimize your resume.")
            
            new_u = st.text_input("Choose Username", placeholder="Pick a unique name")
            new_p = st.text_input("Choose Password", type="password", placeholder="Strong password")
            new_e = st.text_input("Email (Required for Daily Goals)", placeholder="email@example.com")
            new_ph = st.text_input("Phone (Optional)", placeholder="+91 XXXX XXX XXX")
            
            if st.button("Create My Account 🚀", use_container_width=True, type="primary"):
                if new_u and new_p and new_e:
                    success, msg = db.create_user(new_u, new_p, email=new_e)
                    if success:
                        st.toast("Account created successfully!")
                        # This works now because st.rerun() will reload the script 
                        # and use the "Login" value we just set.
                        st.session_state["auth_mode"] = "Login"
                        st.rerun()
                    else: 
                        st.error(f"⚠️ {msg}")
                else: 
                    st.warning("⚠️ Please fill in all required fields (Username, Password, and Email).")
            
            if st.button("Already have an account? Login here", use_container_width=False):
                st.session_state["auth_mode"] = "Login"
                st.rerun()

    st.stop()

# --- 3. SIDEBAR (Your Original) ---
with st.sidebar:
    st.title(f"👤 {st.session_state['username']}")
    user_role = str(st.session_state.get('role', 'user')).lower()
    if user_role == "admin":
        st.success("🛡️ Access Level: ADMIN")
        with st.expander("🛠️ Admin Tools", expanded=False):
            if st.button("👥 View All Users", use_container_width=True):
                all_users = db.get_all_users()
                st.dataframe(pd.DataFrame(all_users, columns=["Username", "Role", "Email"]))
            st.divider()
            user_to_del = st.text_input("Enter Username to Delete")
            if st.button("🗑️ Permanent Delete User", type="primary"):
                if user_to_del and user_to_del != "senthil33":
                    db.delete_user(user_to_del)
                    st.warning(f"User '{user_to_del}' deleted.")
                else: st.error("Cannot delete primary admin.")
    else:
        st.caption(f"Access Level: {user_role.upper()}")
    
    st.divider()
    page = st.radio("📍 Navigation", ["Dashboard & Jobs", "In-Demand Courses", "Goal Tracker (Emails)"], index=0)
    st.divider()

    if st.button("🚪 Log Out", type="primary", use_container_width=True):
        st.session_state.clear(); st.query_params.clear(); st.rerun()

    st.subheader("📝 Manual Save Job")
    with st.expander("Enter JD Details"):
        m_comp = st.text_input("Company Name")
        m_role = st.text_input("Job Role")
        m_url = st.text_input("Job URL")
        m_desc = st.text_area("Full Job Description")
        if st.button("💾 Save to Dashboard"):
            if m_comp and m_role and m_desc:
                db.add_job(m_comp, m_role, m_url, m_desc, st.session_state['username'])
                st.success("Saved Successfully!"); st.rerun()
            else: st.warning("Please fill required fields.")

    st.divider()
    st.subheader("✨ AI URL Analyzer")
    target_url = st.text_input("Paste URL to Scrape", key="url_input")
    if st.button("🪄 Run AI Analysis", use_container_width=True):
        with st.spinner("Analyzing..."):
            scraped_text = scraper.scrape_job_details(target_url)
            if scraped_text:
                analysis_res = ai_engine.analyze_job_with_ai(scraped_text)
                st.session_state['ai_scratchpad'] = analysis_res
                st.success("Analysis Complete!")
            else: st.error("Failed to scrape.")

    if st.session_state['ai_scratchpad']:
        st.info(f"**AI Scratchpad:**\n\n{st.session_state['ai_scratchpad']}")

# --- 4. DASHBOARD & JOBS (Your Original + Heatmap) ---
if page == "Dashboard & Jobs":
    st.title("🚀 AI Career Command Center")
    saved_jobs_data = db.fetch_jobs(st.session_state['username'])
    total_saved = len(saved_jobs_data) if saved_jobs_data else 0
    
    m1, m2, m3 = st.columns(3)
    with m1: st.metric(label="Total Saved Jobs", value=total_saved)
    with m2: st.metric(label="Market Readiness", value="Dynamic Analysis", delta="Live")
    with m3: st.metric(label="Active Learning Goals", value=len(db.get_user_goals(st.session_state['username'])))

    st.divider()

    # --- THE MOBILE-OPTIMIZED SKILL GAP CHART ---
    if total_saved > 0:
        latest_job = saved_jobs_data[-1] 
        st.subheader(f"📊 Skill Gap Analysis")
        st.caption(f"Target: {latest_job[2]}") # Role Name
        
        with st.spinner("AI analyzing requirements..."):
            req_skills = ai_engine.extract_dynamic_skills(latest_job[4])
            user_resume = st.session_state.get('resume_text', "").lower()
            
            chart_data = [{"Skill": s, "Level": 100 if s.lower() in user_resume else 20} for s in req_skills]
            df_skills = pd.DataFrame(chart_data)
            
            # Enhanced Plotly Layout for Responsiveness
            fig = px.bar(
                df_skills, 
                x='Skill', 
                y='Level', 
                color='Level', 
                color_continuous_scale='RdYlGn', 
                range_y=[0, 100],
                text='Level'
            )

            fig.update_layout(
                autosize=True,
                margin=dict(l=20, r=20, t=20, b=100),
                height=450,
                xaxis_tickangle=-45,
                showlegend=False,
                coloraxis_showscale=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'responsive': True})
            
            # Mobile-Friendly Skill List
            missing_skills = [s for s in req_skills if s.lower() not in user_resume]
            if missing_skills:
                st.warning(f"💡 **Focus on:** {', '.join(missing_skills)}")
    else:
        st.info("👋 Welcome! Search and 'Select' a job below to see analysis.")

    st.divider()
    st.header("🌍 Live Global Job Discovery")
    col_l, col_c, col_s = st.columns([2, 1, 1])
    with col_l: loc = st.text_input("Target City/State", value="Chennai")
    with col_c: coun = st.selectbox("Country Code", [("India", "in"), ("USA", "us"), ("UK", "gb")], format_func=lambda x: x[0])
    with col_s: 
        st.write("##"); search_trigger = st.button("🔍 Search Live Jobs", use_container_width=True)

    if search_trigger: st.cache_data.clear()

    with st.expander("Current Vacancies", expanded=True):
        live_feed = scraper.fetch_live_job_feed(loc, coun[1])
        if live_feed:
            for job in live_feed:
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{job.get('title')}**")
                    st.caption(f"🏢 {job.get('company', {}).get('display_name')} | 📍 {job.get('location', {}).get('display_name')}")
                with c2: st.link_button("🌐 View Site", job.get('redirect_url'))
                with c3:
                    if st.button("🪄 Select", key=f"feed_{job.get('id')}"):
                        db.add_job(job.get('company', {}).get('display_name'), job.get('title'), job.get('redirect_url'), job.get('description', 'Scraped'), st.session_state['username'])
                        st.toast(f"Saved {job.get('title')}!"); st.rerun()
                st.divider()

    st.markdown("---")
    st.header("🎯 Phase 2: Resume Tailoring & AI Matching")
    if saved_jobs_data:
        df_saved = pd.DataFrame(saved_jobs_data, columns=["ID", "Company", "Role", "URL", "Desc", "Status", "Date", "Applied", "User"])
        st.subheader("📋 Your Saved Applications")
        st.dataframe(df_saved[["Company", "Role", "Status", "Date"]], use_container_width=True, hide_index=True)

        col_left, col_right = st.columns(2)
        with col_left:
            job_map = {f"{row['Company']} - {row['Role']}": row['Desc'] for _, row in df_saved.iterrows()}
            selected_job_key = st.selectbox("Select from saved jobs:", list(job_map.keys()))
            target_jd_text = job_map[selected_job_key]
        with col_right:
            res_file = st.file_uploader("Upload Resume (PDF only)", type="pdf")

        if res_file and st.button("🚀 Analyze Matching Gaps"):
            pdf_reader = pypdf.PdfReader(res_file)
            resume_content = "".join([page.extract_text() for page in pdf_reader.pages])
            st.session_state['last_analysis'] = ai_engine.match_resume_to_job(resume_content, target_jd_text)
            st.session_state['resume_text'] = resume_content

    if 'last_analysis' in st.session_state:
        st.divider(); st.subheader("🤖 AI Career Coach")
        st.info(f"📊 **Initial Match Report:**\n\n{st.session_state['last_analysis']}")
        if "messages" not in st.session_state: st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]): st.markdown(message["content"])

        chat_query = st.chat_input("Ask about the job...")
        if chat_query:
            with st.chat_message("user"): st.markdown(chat_query)
            st.session_state.messages.append({"role": "user", "content": chat_query})
            with st.chat_message("assistant"):
                is_resume_request = any(word in chat_query.lower() for word in ["resume", "update", "cv"])
                if is_resume_request:
                    prompt = f"RESUME: {st.session_state['resume_text']}\nJD: {target_jd_text}\nTASK: Rewrite resume sections."
                    response = ai_engine.analyze_job_with_ai(prompt)
                    st.session_state['optimized_resume'] = response
                else:
                    prompt = f"JD: {target_jd_text}\nQUESTION: {chat_query}"
                    response = ai_engine.analyze_job_with_ai(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

        if 'optimized_resume' in st.session_state:
            def generate_pdf(text_content):
                pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
                clean_text = text_content.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 8, txt=clean_text)
                return pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download Updated Resume", data=generate_pdf(st.session_state['optimized_resume']), file_name="Resume.pdf", mime="application/pdf")

# --- 5. PAGE LOGIC: IN-DEMAND COURSES (With Immediate Mail) ---
elif page == "In-Demand Courses":
    st.title("📚 Professional Skills Hub")
    st.write("Find world-class courses and get email reminders for your learning.")
    course_data = {
        "Python & AI": {"Coursera": "https://www.coursera.org/learn/python-for-everybody", "YouTube": "https://youtu.be/m67-bOpOoPU?si=lvJ8otsfB9zak52J"},
        "Data Science": {"Coursera": "https://www.coursera.org/learn/data-science", "YouTube": "https://www.youtube.com/watch?v=ua-CiDNNj30"},
        "Cloud Computing": {"Coursera": "https://www.coursera.org/learn/cloud-computing", "YouTube": "https://www.youtube.com/watch?v=SOTamCETW04"},
        "Web Development": {"Coursera": "https://www.coursera.org/learn/web-design-for-everybody", "YouTube": "https://www.youtube.com/watch?v=kDyJN7Y5DyU"},
        "Machine Learning": {"Coursera": "https://www.coursera.org/learn/machine-learning", "YouTube": "https://www.youtube.com/watch?v=PeMlggy_ftU"},
        "Cybersecurity": {"Coursera": "https://www.coursera.org/learn/cybersecurity-fundamentals", "YouTube": "https://www.youtube.com/watch?v=jVO06FyIjKY"},
        "DevOps": {"Coursera": "https://www.coursera.org/learn/devops-and-software-engineering", "YouTube": "https://www.youtube.com/watch?v=j5Zsa_eOXeY"},
        "Data Engineering": {"Coursera": "https://www.coursera.org/learn/data-engineering", "YouTube": "https://www.youtube.com/watch?v=M3P-63PBOE4"},
    }
    for course, links in course_data.items():
        with st.expander(f"📖 {course}"):
            c1, c2, c3 = st.columns(3)
            with c1: st.link_button("🎓 Coursera", links["Coursera"], use_container_width=True)
            with c2: st.link_button("📺 YouTube", links["YouTube"], use_container_width=True)
       
            with c3: 
                if st.button(f"Email me {course} guide", key=f"btn_{course}"):
                    with st.spinner("AI preparing your guide..."):
                        # Get user email
                        user_email = db.get_user_email(st.session_state['username'])
                        if user_email:
                            if send_instant_guide(user_email, course):
                                clean_role = f"{course} Specialist" 
                                clean_skills = f"{course}, Syllabus Creation, Mastery"
                            if st.button(f"You Selected {course}", key=f"course_{course}"):
   
                           # You can also use ai_engine.generate_roadmap(course, 30) here if you want AI syllabus
                               default_syllabus = f"Introduction to {course};Basic Concepts;Intermediate Tools;Advanced Project;Final Review"
    
    # 2. Call add_goal with ALL 4 required arguments
                               db.add_goal(
                                            st.session_state['username'], 
                                            f"GUIDE: {course}", 
                                            30,               # The 'days' argument
                                            default_syllabus  # The missing 'syllabus' argument that caused the error
                                        )
                            # 4. OPTIONAL: Use toast for better mobile feedback
                            st.toast(f"Success! Check {user_email} for your roadmap.", icon="🚀")
                            st.balloons()

                            # 5. WAIT A MOMENT OR RERUN
                            # If you want the user to see the success message clearly before the page jumps:
                            import time
                            time.sleep(2) 
                            st.rerun()
                        else: 
                            st.error("Email not found in database.")
# --- 6. PAGE LOGIC: GOAL TRACKER (ENHANCED) ---
elif page == "Goal Tracker (Emails)":
    st.title("🎯 AI-Powered Learning Journey")
    st.markdown("""
        <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff;'>
            Pick a subject, and our AI will architect a custom roadmap for you. 
            <b>Every morning at 8:00 AM IST</b>, you'll receive a module with AI-generated notes in your inbox.
        </div>
    """, unsafe_allow_html=True)

    # --- GOAL CREATION FORM ---
    with st.form("goal_form"):
        st.subheader("Start a New Journey")
        g_name = st.text_input("What subject do you want to master?", placeholder="e.g. Python for DevOps, Cloud Architecture")
        g_days = st.number_input("Duration (Days)", min_value=5, max_value=90, value=30)
        
        if st.form_submit_button("Generate My Roadmap 🚀"):
            if g_name:
                with st.spinner(f"🪄 AI is architecting your {g_days}-day syllabus..."):
                    # 1. Generate Syllabus
                    syllabus = ai_engine.generate_roadmap(g_name, g_days)
                    
                    # 2. Store in Supabase
                    db.add_goal(st.session_state['username'], g_name, g_days, syllabus)
                    
                    # 3. ENHANCEMENT: Visual Celebrations
                    st.snow() # The snow effect you wanted!
                    st.balloons()
                    st.toast(f"Success! Journey for {g_name} started.", icon="✅")
                    
                st.success(f"Roadmap Created! First module arrives tomorrow at 8:00 AM.")
                time.sleep(2) 
                st.rerun() 
            else:
                st.error("Please enter a subject.")

    st.divider()
    st.subheader("Your Active Journeys")
    
    active_goals = db.get_user_goals(st.session_state['username'])

    if not active_goals:
        st.info("You don't have any active journeys yet. Create one above to start learning!")
    else:
        for g in active_goals:
            # g structure: (id, goal_name, start_date, days, is_active, syllabus)
            goal_id, title, start_date, total_days, is_active, syllabus = g
            
            # 1. CALCULATE PROGRESS
            # We assume start_date is stored as 'YYYY-MM-DD'
            start_dt = datetime.strptime(str(start_date), '%Y-%m-%d')
            days_passed = (datetime.now() - start_dt).days
            current_day = days_passed + 1 # Day 1 starts today
            
            # Progress percentage
            progress_pct = min(max(current_day / total_days, 0.0), 1.0)
            
            display_title = title.replace("GUIDE: ", "")
            
            with st.expander(f"📅 {display_title} (Day {min(current_day, total_days)} of {total_days})"):
                
                # 2. PROGRESS BAR
                st.write(f"**Overall Progress: {int(progress_pct * 100)}%**")
                st.progress(progress_pct)
                
                # DELETE BUTTON
                if st.button("🗑️ Stop Journey", key=f"del_{goal_id}"):
                    if db.delete_goal_by_id(goal_id):
                        st.toast("Journey removed.")
                        st.rerun()

                if syllabus:
                    st.markdown("---")
                    raw_topics = syllabus.split(';')
                    clean_topics = [t.strip() for t in raw_topics if t.strip() and "Not specified" not in t]

                    for i, topic in enumerate(clean_topics):
                        day_num = i + 1
                        
                        # 3. VISUAL STATUS LOGIC
                        if day_num < current_day:
                            # Past Days
                            st.markdown(f"✅ <span style='color:gray; text-decoration:line-through;'>Day {day_num}: {topic}</span>", unsafe_allow_html=True)
                        elif day_num == current_day:
                            # Current Day
                            st.markdown(f"🎯 **Day {day_num}: {topic}** <span style='color:#007bff; font-weight:bold;'>(TODAY)</span>", unsafe_allow_html=True)
                        else:
                            # Future Days
                            st.markdown(f"⚪ Day {day_num}: {topic}")