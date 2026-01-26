import os
import sys
import smtplib
from email.message import EmailMessage
from datetime import datetime
from supabase import create_client
from groq import Groq

def validate_environment():
    """Validate all required environment variables are present."""
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SENDER_EMAIL', 'APP_PASSWORD', 'GROQ_API_KEY']
    
    missing = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value or not value.strip():
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ All environment variables validated")
    return True


def send_daily_reminders():
    print("\n" + "="*60)
    print("🚀 DAILY CAREER REMINDER SERVICE")
    print("="*60)
    print(f"⏰ Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Validate Environment
    if not validate_environment():
        sys.exit(1)
    
    # Get credentials
    url = os.environ.get("SUPABASE_URL").strip()
    key = os.environ.get("SUPABASE_KEY").strip()
    email_user = os.environ.get("SENDER_EMAIL").strip()
    email_pass = os.environ.get("APP_PASSWORD").strip()
    groq_key = os.environ.get("GROQ_API_KEY").strip()

    # Initialize clients
    try:
        print("🔌 Connecting to Supabase...")
        supabase = create_client(url, key)
        groq_client = Groq(api_key=groq_key)
        print("✅ Clients initialized\n")
    except Exception as e:
        print(f"❌ Failed to initialize clients: {e}")
        sys.exit(1)

    # Fetch Active Goals (WITHOUT join - we'll query users separately)
    print("📊 Fetching active goals...")
    try:
        response = supabase.table("goals").select("*").eq("is_active", 1).execute()
        goals = response.data
        print(f"✅ Found {len(goals)} active goal(s)\n")
    except Exception as e:
        print(f"❌ Database Query Failed: {e}")
        sys.exit(1)

    if not goals:
        print("ℹ️ No active goals found. Exiting.")
        return

    # Process each goal
    success_count = 0
    error_count = 0

    for idx, goal in enumerate(goals, 1):
        goal_id = goal.get('id', 'unknown')
        print(f"[{idx}/{len(goals)}] Processing Goal ID: {goal_id}")
        
        try:
            # Get user_id from goal
            user_id = goal.get('user_id')
            if not user_id:
                print(f"   ⚠️ Skipping: No user_id in goal")
                error_count += 1
                continue
            
            # Fetch user email separately
            try:
                user_response = supabase.table("users").select("email").eq("id", user_id).execute()
                if not user_response.data:
                    print(f"   ⚠️ Skipping: User {user_id} not found")
                    error_count += 1
                    continue
                user_email = user_response.data[0]['email']
            except Exception as e:
                print(f"   ⚠️ Skipping: Failed to fetch user email: {e}")
                error_count += 1
                continue
            
            # Extract goal details
            goal_name = goal.get('goal_name', 'Career Goal')
            syllabus_text = goal.get('syllabus', '')
            
            if not syllabus_text:
                print(f"   ⚠️ Skipping: Empty syllabus")
                error_count += 1
                continue
            
            # Parse syllabus
            syllabus_list = [s.strip() for s in syllabus_text.split(';') if s.strip()]
            total_days = int(goal.get('duration', 1))
            
            # Calculate current day
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
            try:
                prompt = f"""Generate 3 concise, actionable study points for Day {current_day} of learning {goal_name}.
Topic: {topic}

Format as:
1. [First point]
2. [Second point]
3. [Third point]

Keep each point under 30 words."""

                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                raw_notes = completion.choices[0].message.content
                print(f"   ✅ AI notes generated")
            except Exception as e:
                print(f"   ⚠️ AI generation failed, using fallback: {e}")
                raw_notes = f"1. Study the fundamentals of {topic}\n2. Practice with examples\n3. Review key concepts"
            
            # Format notes for HTML
            formatted_notes = raw_notes.replace('\n', '<br>')
            
            # Construct email
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
            
            # Send email
            try:
                with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as smtp:
                    smtp.starttls()
                    smtp.login(email_user, email_pass)
                    smtp.send_message(msg)
                print(f"   ✅ Email sent successfully\n")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Email send failed: {e}\n")
                error_count += 1
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")
            error_count += 1

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