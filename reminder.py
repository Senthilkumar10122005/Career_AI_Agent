import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import sys

# Import required libraries
try:
    from supabase import create_client
    from groq import Groq
except ImportError as e:
    print(f"❌ Missing required library: {e}")
    print("Run: pip install supabase groq postgrest")
    sys.exit(1)

# ============================================================================
# CONFIGURATION & VALIDATION
# ============================================================================

print("=" * 70)
print("🚀 Daily Career Reminder Script")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Get environment variables
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Validate environment variables
print("\n🔍 Validating Environment Variables...")

missing_vars = []
if not SENDER_EMAIL:
    missing_vars.append("SENDER_EMAIL")
if not APP_PASSWORD:
    missing_vars.append("APP_PASSWORD")
if not SUPABASE_URL:
    missing_vars.append("SUPABASE_URL")
if not SUPABASE_KEY:
    missing_vars.append("SUPABASE_KEY")
if not GROQ_API_KEY:
    missing_vars.append("GROQ_API_KEY")

if missing_vars:
    print(f"❌ ERROR: Missing environment variables: {', '.join(missing_vars)}")
    print("\nMake sure these secrets are set in GitHub:")
    for var in missing_vars:
        print(f"  - {var}")
    sys.exit(1)

# Validate URL format
if not SUPABASE_URL.startswith("http"):
    print(f"❌ ERROR: Invalid SUPABASE_URL format: {SUPABASE_URL}")
    print("URL must start with https://")
    sys.exit(1)

print(f"✅ SENDER_EMAIL: {SENDER_EMAIL}")
print(f"✅ APP_PASSWORD: {'*' * 8} (hidden)")
print(f"✅ SUPABASE_URL: {SUPABASE_URL[:40]}...")
print(f"✅ SUPABASE_KEY: {'*' * 8}... (hidden)")
print(f"✅ GROQ_API_KEY: {'*' * 8}... (hidden)")

# Initialize clients
print("\n🔧 Initializing Clients...")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Supabase: {e}")
    sys.exit(1)

try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq AI client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Groq: {e}")
    sys.exit(1)

# ============================================================================
# AI CONTENT GENERATION
# ============================================================================

def generate_daily_tip(goal_name, topic):
    """Generate AI-powered learning tip using Groq"""
    try:
        prompt = f"""You are a professional career coach. Generate a motivational and practical learning tip for someone studying "{goal_name}".

Today's topic: {topic}

Provide:
1. One specific, actionable tip (2-3 sentences)
2. One practical example or exercise they can do today
3. Keep it encouraging and professional

Format your response as:
TIP: [your tip here]
EXERCISE: [practical exercise here]"""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Failed to generate AI tip: {e}")
        return f"TIP: Focus on understanding {topic} through hands-on practice.\nEXERCISE: Spend 30 minutes building a small project using {topic}."

# ============================================================================
# EMAIL SENDING
# ============================================================================

def send_daily_reminder(email, username, goal_name, day_number, topic, total_days):
    """Send beautifully formatted daily learning reminder with AI-generated content"""
    try:
        print(f"\n📧 Preparing email for {email}...")
        
        # Generate AI-powered tip
        print(f"🤖 Generating AI learning tip...")
        ai_content = generate_daily_tip(goal_name, topic)
        
        # Parse AI content
        tip_text = ""
        exercise_text = ""
        for line in ai_content.split('\n'):
            if line.startswith('TIP:'):
                tip_text = line.replace('TIP:', '').strip()
            elif line.startswith('EXERCISE:'):
                exercise_text = line.replace('EXERCISE:', '').strip()
        
        msg = EmailMessage()
        msg['Subject'] = f"🎯 Day {day_number}/{total_days}: {goal_name}"
        msg['From'] = f"Career AI Agent <{SENDER_EMAIL}>"
        msg['To'] = email

        progress_percentage = int((day_number / total_days) * 100)

        html_content = f"""
        <html>
            <body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f4f7f9;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7f9; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                                
                                <!-- Header -->
                                <tr style="background: linear-gradient(135deg, #667eea, #764ba2);">
                                    <td style="padding: 40px 30px; text-align: center;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 28px;">📚 Daily Learning Module</h1>
                                        <p style="color: #e0f0ff; margin: 10px 0 0 0; font-size: 14px;">Career AI Agent</p>
                                        <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 12px;">Hello, {username}! 👋</p>
                                    </td>
                                </tr>
                                
                                <!-- Progress Bar -->
                                <tr>
                                    <td style="padding: 30px 30px 0 30px;">
                                        <div style="background: #f0f0f0; border-radius: 10px; height: 10px; overflow: hidden;">
                                            <div style="background: linear-gradient(90deg, #667eea, #764ba2); width: {progress_percentage}%; height: 10px;"></div>
                                        </div>
                                        <p style="text-align: center; color: #666; font-size: 13px; margin: 10px 0 0 0; font-weight: 600;">
                                            Day {day_number} of {total_days} • {progress_percentage}% Complete 🎯
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- Main Content -->
                                <tr>
                                    <td style="padding: 30px 40px; color: #333333;">
                                        <h2 style="color: #667eea; margin-top: 0; font-size: 22px;">🎯 {goal_name}</h2>
                                        
                                        <!-- Today's Topic -->
                                        <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-left: 4px solid #667eea; padding: 20px; margin: 20px 0; border-radius: 8px;">
                                            <h3 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">📖 Today's Focus</h3>
                                            <p style="margin: 0; font-size: 16px; color: #495057; line-height: 1.6; font-weight: 600;">
                                                {topic}
                                            </p>
                                        </div>
                                        
                                        <!-- AI-Generated Tip -->
                                        <div style="background: linear-gradient(135deg, #e8f4f8, #d4e9f0); border-left: 4px solid #17a2b8; padding: 20px; margin: 20px 0; border-radius: 8px;">
                                            <h3 style="margin: 0 0 10px 0; color: #0c5460; font-size: 16px;">💡 AI Coach Tip</h3>
                                            <p style="margin: 0; font-size: 14px; color: #0c5460; line-height: 1.7;">
                                                {tip_text if tip_text else 'Focus on understanding the core concepts before moving to advanced topics.'}
                                            </p>
                                        </div>
                                        
                                        <!-- Practical Exercise -->
                                        {f'''
                                        <div style="background: linear-gradient(135deg, #fff3cd, #ffeaa7); border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0; border-radius: 8px;">
                                            <h3 style="margin: 0 0 10px 0; color: #856404; font-size: 16px;">🎯 Today's Exercise</h3>
                                            <p style="margin: 0; font-size: 14px; color: #856404; line-height: 1.7;">
                                                {exercise_text}
                                            </p>
                                        </div>
                                        ''' if exercise_text else ''}
                                        
                                        <!-- Action Checklist -->
                                        <div style="margin: 25px 0;">
                                            <h3 style="color: #333; font-size: 16px; margin-bottom: 15px;">✅ Today's Checklist:</h3>
                                            <ul style="color: #555; line-height: 2; padding-left: 20px; margin: 0;">
                                                <li>Complete 30-45 minutes of focused learning</li>
                                                <li>Practice with hands-on examples</li>
                                                <li>Take notes on key concepts</li>
                                                <li>Review and apply what you learned</li>
                                            </ul>
                                        </div>
                                        
                                        <!-- Motivation Box -->
                                        <div style="background: linear-gradient(135deg, #d4edda, #c3e6cb); border: 1px solid #28a745; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                                            <p style="margin: 0; color: #155724; font-weight: 600; font-size: 15px;">
                                                🌟 "Progress, not perfection. Keep going!" 🌟
                                            </p>
                                        </div>
                                        
                                        <!-- CTA Button -->
                                        <div style="text-align: center; margin: 30px 0 20px 0;">
                                            <a href="https://roadmap.sh" style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 35px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);">
                                                📚 View Learning Resources
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr style="background: #f8f9fa;">
                                    <td style="padding: 20px 30px; text-align: center; color: #6c757d; font-size: 13px;">
                                        <p style="margin: 0 0 10px 0; font-weight: 600;">You're doing great! Keep up the momentum! 🚀</p>
                                        <p style="margin: 0; font-size: 12px;">
                                            Automated reminder from Career AI Agent<br>
                                            Track your progress at <a href="#" style="color: #667eea;">Career Dashboard</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        msg.set_content("Daily Learning Reminder - Please view in HTML-enabled email client")
        msg.add_alternative(html_content, subtype='html')
        
        print(f"📤 Sending email via SMTP...")
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        
        print(f"✅ Email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to send daily reminders to all active learners"""
    
    try:
        # Fetch all active goals with user email
        print("\n📊 Fetching active learning goals from database...")
        
        # Query to get goals with user emails
        response = supabase.table("goals").select(
            "id, username, goal_name, start_date, days, syllabus, users!inner(email)"
        ).eq("is_active", 1).execute()
        
        active_goals = response.data
        
        if not active_goals:
            print("ℹ️  No active goals found. No emails to send.")
            return
        
        print(f"✅ Found {len(active_goals)} active learning journey(s)")
        
        emails_sent = 0
        emails_failed = 0
        
        for goal in active_goals:
            print(f"\n{'─' * 70}")
            print(f"👤 User: {goal['username']}")
            print(f"🎯 Goal: {goal['goal_name']}")
            
            # Calculate which day of the journey
            start_date = datetime.strptime(goal['start_date'], '%Y-%m-%d')
            days_elapsed = (datetime.now() - start_date).days
            current_day = days_elapsed + 1
            total_days = goal['days']
            
            print(f"📅 Day {current_day} of {total_days}")
            
            # Check if journey is complete
            if current_day > total_days:
                print(f"✓ Journey completed! ({current_day - 1} days elapsed)")
                continue
            
            # Parse syllabus to get today's topic
            syllabus = goal.get('syllabus', '')
            if not syllabus:
                print("⚠️  No syllabus found, skipping...")
                continue
            
            topics = [t.strip() for t in syllabus.split(';') if t.strip()]
            
            if current_day <= len(topics):
                today_topic = topics[current_day - 1]
            else:
                today_topic = f"Review and Practice: {goal['goal_name']}"
            
            print(f"📚 Today's Topic: {today_topic}")
            
            # Get user email from the joined users table
            user_email = goal.get('users', {}).get('email')
            if not user_email:
                print("⚠️  No email found for user, skipping...")
                emails_failed += 1
                continue
            
            print(f"📧 Recipient: {user_email}")
            
            # Send email
            if send_daily_reminder(
                user_email,
                goal['username'],
                goal['goal_name'], 
                current_day, 
                today_topic, 
                total_days
            ):
                emails_sent += 1
            else:
                emails_failed += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 EXECUTION SUMMARY")
        print("=" * 70)
        print(f"✅ Emails sent successfully: {emails_sent}")
        print(f"❌ Emails failed: {emails_failed}")
        print(f"📈 Total active goals: {len(active_goals)}")
        print(f"📅 Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        if emails_failed > 0:
            print(f"\n⚠️  Warning: {emails_failed} email(s) failed to send")
            sys.exit(1)
        else:
            print("\n✅ All emails sent successfully!")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: Script failed with exception:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()