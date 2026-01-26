import os
import sys
import smtplib
from email.message import EmailMessage
from datetime import datetime
from supabase import create_client
from groq import Groq

def validate_environment():
    """Validate all required environment variables are present and correctly formatted."""
    required_vars = {
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_KEY': 'Supabase anon/service key',
        'SENDER_EMAIL': 'Gmail sender address',
        'APP_PASSWORD': 'Gmail app password',
        'GROQ_API_KEY': 'Groq API key'
    }
    
    missing = []
    invalid = []
    
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if not value:
            missing.append(f"{var} ({description})")
        elif var == 'SUPABASE_URL':
            # Strip whitespace and validate URL format
            value = value.strip()
            if not value.startswith('https://'):
                invalid.append(f"{var}: Must start with 'https://' (got: '{value[:30]}...')")
    
    if missing:
        print(f"❌ Missing environment variables:")
        for m in missing:
            print(f"   - {m}")
        return False
    
    if invalid:
        print(f"❌ Invalid environment variables:")
        for i in invalid:
            print(f"   - {i}")
        return False
    
    print("✅ All environment variables validated")
    return True


def initialize_clients():
    """Initialize Supabase and Groq clients with error handling."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    
    try:
        print(f"🔌 Connecting to Supabase...")
        print(f"   URL: {url[:30]}...{url[-10:] if len(url) > 40 else ''}")
        
        supabase = create_client(url, key)
        
        # Test connection
        test_response = supabase.table("goals").select("id").limit(1).execute()
        print(f"✅ Supabase connected successfully")
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print(f"   URL type: {type(url)}")
        print(f"   URL length: {len(url)}")
        raise
    
    try:
        print(f"🤖 Initializing Groq client...")
        groq_client = Groq(api_key=groq_key)
        print(f"✅ Groq client initialized")
        
    except Exception as e:
        print(f"❌ Groq initialization failed: {e}")
        raise
    
    return supabase, groq_client


def generate_ai_notes(groq_client, goal_name, topic, current_day):
    """Generate study notes using Groq AI."""
    try:
        prompt = f"""Generate 3 concise, actionable study points for Day {current_day} of learning {goal_name}.
Topic: {topic}

Format as:
1. [First point]
2. [Second point]
3. [Third point]

Keep each point under 30 words and focused on practical learning."""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        raw_notes = completion.choices[0].message.content
        return raw_notes
        
    except Exception as e:
        print(f"⚠️ AI generation failed, using fallback: {e}")
        return f"1. Study the fundamentals of {topic}\n2. Practice with examples\n3. Review key concepts"


def send_email(user_email, goal_name, current_day, topic, notes):
    """Send formatted email with study reminder."""
    email_user = os.environ.get("SENDER_EMAIL").strip()
    email_pass = os.environ.get("APP_PASSWORD").strip()
    
    # Format notes for HTML (escape backslashes outside f-string)
    formatted_notes = notes.replace('\n', '<br>')
    
    msg = EmailMessage()
    msg['Subject'] = f"☀️ Day {current_day}: {topic}"
    msg['From'] = f"Career AI Agent <{email_user}>"
    msg['To'] = user_email
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 20px; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 30px 20px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 600;">
                    Day {current_day} Study Guide
                </h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px 20px;">
                <h2 style="color: #1f2937; margin: 0 0 10px 0; font-size: 20px;">
                    📚 {topic}
                </h2>
                
                <p style="color: #6b7280; margin: 0 0 20px 0; font-size: 14px;">
                    Your learning module for <strong style="color: #6366f1;">{goal_name}</strong>
                </p>
                
                <!-- Notes Box -->
                <div style="background: #f9fafb; padding: 20px; border-radius: 8px; border-left: 4px solid #6366f1; margin: 20px 0;">
                    <div style="color: #374151; line-height: 1.6; font-size: 15px;">
                        {formatted_notes}
                    </div>
                </div>
                
                <!-- Footer Message -->
                <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 13px; margin: 0; text-align: center;">
                        💪 Keep pushing towards your goals!<br>
                        <span style="color: #d1d5db;">Automated reminder from Career AI Agent</span>
                    </p>
                </div>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    msg.set_content("Please view this email in an HTML-compatible client.")
    msg.add_alternative(html_body, subtype='html')
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(email_user, email_pass)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"   ❌ Email send failed: {e}")
        return False


def send_daily_reminders():
    """Main function to process and send daily reminders."""
    print("\n" + "="*60)
    print("🚀 DAILY CAREER REMINDER SERVICE")
    print("="*60)
    print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    # Step 1: Validate Environment
    if not validate_environment():
        print("\n❌ Validation failed. Please check your GitHub Secrets.")
        sys.exit(1)
    
    # Step 2: Initialize Clients
    try:
        supabase, groq_client = initialize_clients()
    except Exception as e:
        print(f"\n❌ Client initialization failed: {e}")
        sys.exit(1)
    
    # Step 3: Fetch Active Goals
    print(f"\n📊 Fetching active goals from database...")
    try:
        response = supabase.table("goals").select("*, users(email)").eq("is_active", 1).execute()
        goals = response.data
        print(f"✅ Found {len(goals)} active goal(s)")
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        sys.exit(1)
    
    if not goals:
        print("ℹ️ No active goals found. Exiting.")
        return
    
    # Step 4: Process Each Goal
    print(f"\n📧 Processing goals and sending emails...\n")
    
    success_count = 0
    error_count = 0
    
    for idx, goal in enumerate(goals, 1):
        goal_id = goal.get('id', 'unknown')
        print(f"[{idx}/{len(goals)}] Processing Goal ID: {goal_id}")
        
        try:
            # Extract user email
            user_data = goal.get('users')
            if not user_data or not user_data.get('email'):
                print(f"   ⚠️ Skipping: No user email linked")
                error_count += 1
                continue
            
            user_email = user_data['email']
            goal_name = goal.get('goal_name', 'Career Goal')
            syllabus_text = goal.get('syllabus', '')
            
            if not syllabus_text:
                print(f"   ⚠️ Skipping: Empty syllabus")
                error_count += 1
                continue
            
            # Parse syllabus and calculate current day
            syllabus_list = [s.strip() for s in syllabus_text.split(';') if s.strip()]
            total_days = int(goal.get('duration', 1))
            
            start_date_str = goal.get('start_date')
            if not start_date_str:
                print(f"   ⚠️ Skipping: No start date")
                error_count += 1
                continue
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            current_day = (datetime.now() - start_date).days + 1
            
            # Check if within active period
            if current_day < 1:
                print(f"   ⏳ Not started yet (starts in {abs(current_day - 1)} days)")
                continue
            elif current_day > total_days:
                print(f"   ✅ Completed (ended {current_day - total_days} days ago)")
                continue
            
            # Get today's topic
            if current_day <= len(syllabus_list):
                topic = syllabus_list[current_day - 1]
            else:
                topic = f"Review Day {current_day - len(syllabus_list)}"
            
            print(f"   📅 Day {current_day}/{total_days}: {topic}")
            print(f"   👤 Recipient: {user_email}")
            
            # Generate AI notes
            notes = generate_ai_notes(groq_client, goal_name, topic, current_day)
            
            # Send email
            if send_email(user_email, goal_name, current_day, topic, notes):
                print(f"   ✅ Email sent successfully")
                success_count += 1
            else:
                error_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            error_count += 1
        
        print()  # Blank line between goals
    
    # Final Summary
    print("="*60)
    print(f"📊 SUMMARY")
    print("="*60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📧 Total processed: {len(goals)}")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        send_daily_reminders()
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)