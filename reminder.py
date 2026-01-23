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

    # 2. Fetch Active Goals (1 = Active)
    response = supabase.table("goals").select("*, users(email)").eq("is_active", 1).execute()
    goals = response.data

    print(f"🔍 Found {len(goals)} active goals.")

    for goal in goals:
        try:
            user_data = goal.get('users')
            if not user_data: continue
            
            user_email = user_data['email']
            goal_name = goal.get('goal_name', 'Career Goal')
            syllabus_text = goal.get('syllabus', '')
            
            if not syllabus_text: continue
                
            syllabus_list = syllabus_text.split(';')
            total_days = int(goal.get('duration', 1))
            
            start_date = datetime.strptime(goal['start_date'], '%Y-%m-%d')
            current_day = (datetime.now() - start_date).days + 1

            if 1 <= current_day <= total_days:
                topic = syllabus_list[current_day-1] if current_day <= len(syllabus_list) else "Review"
                
                # --- AI Note Generation ---
                prompt = f"Provide 3 concise study points for Day {current_day} of {goal_name}. Topic: {topic}."
                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                raw_notes = completion.choices[0].message.content
                
                # FIX: Move replace outside the f-string to avoid SyntaxError
                formatted_notes = raw_notes.replace('\n', '<br>')

                # --- Email Construction ---
                msg = EmailMessage()
                msg['Subject'] = f"☀️ Day {current_day}: {topic}"
                msg['From'] = f"Career AI Agent <{email_user}>"
                msg['To'] = user_email
                
                html_body = f"""
                <div style="font-family: sans-serif; border: 2px solid #6366f1; padding: 20px; border-radius: 10px; max-width: 600px;">
                    <h2 style="color: #6366f1;">Day {current_day}: {topic}</h2>
                    <p>Your learning module for <b>{goal_name}</b>:</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #6366f1;">
                        {formatted_notes}
                    </div>
                </div>
                """
                msg.add_alternative(html_body, subtype='html')

                # --- Send ---
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_user, email_pass)
                    smtp.send_message(msg)
                print(f"✅ Mail sent to {user_email}")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    send_daily_reminders()