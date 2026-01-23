import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from supabase import create_client
from groq import Groq 

def send_daily_reminders():
    # 1. Get Secrets
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    email_user = os.environ.get("SENDER_EMAIL")
    email_pass = os.environ.get("APP_PASSWORD")
    groq_key = os.environ.get("GROQ_API_KEY")

    supabase = create_client(url, key)
    groq_client = Groq(api_key=groq_key)

    # 2. Fetch Active Goals (using 1 for True as per your DB image)
    response = supabase.table("goals").select("*, users(email)").eq("is_active", 1).execute()
    goals = response.data

    print(f"🔍 Found {len(goals)} active goals to process.")

    for goal in goals:
        try:
            # Safer way to get user email from the joined 'users' table
            user_data = goal.get('users')
            if not user_data or 'email' not in user_data:
                print(f"⚠️ Skipping: No email found for goal ID {goal.get('id')}")
                continue
            
            user_email = user_data['email']
            goal_name = goal.get('goal_name', 'Your Goal')
            
            if not goal.get('syllabus'):
                print(f"⚠️ Skipping {goal_name}: No syllabus content.")
                continue
                
            syllabus_list = goal['syllabus'].split(';')
            total_days = int(goal.get('duration', 1))
            
            # Date calculation
            start_date = datetime.strptime(goal['start_date'], '%Y-%m-%d')
            current_day = (datetime.now() - start_date).days + 1

            if 1 <= current_day <= total_days:
                # Get topic safely
                topic = syllabus_list[current_day-1] if current_day <= len(syllabus_list) else "Final Review"
                
                # --- AI Note Generation ---
                prompt = f"Provide 3 concise study points and 1 'Pro Tip' for Day {current_day} of learning {goal_name}. Topic: {topic}."
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                notes = completion.choices[0].message.content

                # --- Email Construction ---
                msg = EmailMessage()
                msg['Subject'] = f"☀️ Day {current_day}: {topic}"
                msg['From'] = f"Career AI Agent <{email_user}>"
                msg['To'] = user_email
                
                html_body = f"""
                <div style="font-family: sans-serif; border: 2px solid #6366f1; padding: 20px; border-radius: 10px; max-width: 600px;">
                    <h2 style="color: #6366f1;">Day {current_day}: {topic}</h2>
                    <p>Module for <b>{goal_name}</b>:</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #6366f1;">
                        {notes.replace('\n', '<br>')}
                    </div>
                    <p style="margin-top:20px; font-size: 0.8em; color: #666;">
                        Progress: {int((current_day/total_days)*100)}%
                    </p>
                </div>
                """
                msg.add_alternative(html_body, subtype='html')

                # --- Send Email ---
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_user, email_pass)
                    smtp.send_message(msg)
                print(f"✅ Successfully sent mail to {user_email}")
        
        except Exception as e:
            print(f"❌ Error during processing: {str(e)}")

if __name__ == "__main__":
    send_daily_reminders()