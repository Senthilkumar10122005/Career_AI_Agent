import psycopg2
import smtplib
from datetime import datetime
from email.message import EmailMessage
import os

def send_reminders():
    # 1. Get Credentials and DB URL from GitHub Secrets
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL") 
    APP_PASSWORD = os.environ.get("APP_PASSWORD")
    DB_URL = os.environ.get("SUPABASE_DB_URL")

    if not all([SENDER_EMAIL, APP_PASSWORD, DB_URL]):
        print("❌ Error: Missing environment variables (SENDER_EMAIL, APP_PASSWORD, or SUPABASE_DB_URL).")
        return

    try:
        # 2. Connect to Supabase
        conn = psycopg2.connect(DB_URL)
        c = conn.cursor()
        
        # 3. Get active goals (Note: Using %s for PostgreSQL instead of ?)
        c.execute('''SELECT users.email, goals.goal_name, goals.start_date, goals.duration, goals.id 
                     FROM goals JOIN users ON goals.username = users.username 
                     WHERE goals.is_active = 1''')
        
        active_goals = c.fetchall()
        today = datetime.now().date()

        # 4. Loop through users and send emails
        for email, g_name, start_dt, duration, g_id in active_goals:
            try:
                # Convert string date from DB to Python date object
                start_date = datetime.strptime(start_dt, "%Y-%m-%d").date()
                day_count = (today - start_date).days + 1

                if 1 <= day_count <= duration:
                    # Create the email
                    msg = EmailMessage()
                    msg.set_content(f"Good Morning!\n\nToday is Day {day_count} of your '{g_name}' challenge. Keep studying!\n\n- Your Career Guidance Team")
                    msg['Subject'] = f"🚀 Day {day_count}: Your Daily Learning Goal"
                    
                    # This adds the professional sender name
                    msg['From'] = f"Career Guidance <{SENDER_EMAIL}>"
                    msg['To'] = email

                    # Send the email via Gmail SMTP
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(SENDER_EMAIL, APP_PASSWORD)
                        smtp.send_message(msg)
                    print(f"✅ Reminder sent to {email} for Day {day_count}")
                
                elif day_count > duration:
                    # Deactivate goal once finished
                    c.execute("UPDATE goals SET is_active = 0 WHERE id = %s", (g_id,))
                    conn.commit()
                    print(f"🏁 Goal '{g_name}' completed for {email}. Deactivated.")
            
            except Exception as e:
                print(f"⚠️ Error processing goal for {email}: {e}")

        conn.close()

    except Exception as e:
        print(f"❌ Database Connection Error: {e}")

if __name__ == "__main__":
    send_reminders()