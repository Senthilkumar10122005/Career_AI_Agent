import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from supabase import create_client
from groq import Groq 

def send_daily_reminders():
    # 1. Get Secrets from GitHub Environment
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    email_user = os.environ.get("SENDER_EMAIL")
    email_pass = os.environ.get("APP_PASSWORD")
    groq_key = os.environ.get("GROQ_API_KEY")

    supabase = create_client(url, key)
    groq_client = Groq(api_key=groq_key)

    # 2. Fetch Active Goals 
    # Fix: Ensure we match your table column names exactly
    response = supabase.table("goals").select("*, users(email)").eq("is_active", 1).execute()
    goals = response.data

    for goal in goals:
        try:
            user_email = goal['users']['email']
            # FIX: Changed 'title' to 'goal_name' to match your DB image
            goal_name = goal['goal_name']
            
            # Check if syllabus exists to prevent crash
            if not goal.get('syllabus'):
                print(f"⚠️ Skipping {goal_name}: No syllabus found.")
                continue
                
            syllabus = goal['syllabus'].split(';')
            
            # FIX: Changed 'total_days' to 'duration' to match your DB image
            total_days = int(goal['duration'])
            
            # Calculate current day based on start_date
            start_date = datetime.strptime(goal['start_date'], '%Y-%m-%d')
            current_day = (datetime.now() - start_date).days + 1

            if 1 <= current_day <= total_days:
                topic = syllabus[current_day-1] if current_day <= len(syllabus) else "Final Review"
                
                # --- Generate AI Study Notes ---
                prompt = f"Provide 3 concise study points and 1 'Pro Tip' for Day {current_day} of learning {goal_name}. Topic: {topic}."
                
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                notes = completion.choices[0].message.content

                # --- 3. Send Professional Email ---
                msg = EmailMessage()
                msg['Subject'] = f"☀️ Day {current_day}: {topic}"
                msg['From'] = f"Career AI Agent <{email_user}>"
                msg['To'] = user_email
                
                html = f"""
                <div style="font-family: sans-serif; border: 2px solid #6366f1; padding: 20px; border-radius: 10px; max-width: 600px;">
                    <h2 style="color: #6366f1; margin-top: 0;">Day {current_day}: {topic}</h2>
                    <p>Your daily module for <b>{goal_name}</b> is ready:</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #6366f1;">
                        {notes.replace('\n', '<br>')}
                    </div>
                    <p style="margin-top:20px; font-size: 0.9em; color: #666;">
                        Progress: {int((current_day/total_days)*100)}% complete
                    </p>
                </div>
                """
                msg.add_alternative(html, subtype='html')

                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_user, email_pass)
                    smtp.send_message(msg)
                print(f"✅ Sent Day {current_day} to {user_email}")
        
        except Exception as e:
            print(f"❌ Error processing goal: {e}")

if __name__ == "__main__":
    send_daily_reminders()