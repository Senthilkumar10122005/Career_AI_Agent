import sqlite3
import psycopg2
import streamlit as st
from datetime import datetime
import os

# Get the Connection String
DB_URL = st.secrets.get("SUPABASE_DB_URL") or os.environ.get("SUPABASE_DB_URL")


def get_connection():
    if not DB_URL:
        raise ValueError("SUPABASE_DB_URL is missing! Check your secrets.toml.")
    return psycopg2.connect(DB_URL)

def init_db():
    """Initializes all tables in the Supabase PostgreSQL database."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT, email TEXT)''')
    
    # 2. Goals Table (Updated to include new columns from the start)
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id SERIAL PRIMARY KEY, 
                  username TEXT, 
                  goal_name TEXT, 
                  start_date TEXT, 
                  days INTEGER DEFAULT 30, 
                  syllabus TEXT,
                  is_active INTEGER DEFAULT 1)''')
    
    # 3. Applications Table
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id SERIAL PRIMARY KEY, 
                  company TEXT NOT NULL, 
                  role TEXT NOT NULL, 
                  url TEXT, 
                  description TEXT, 
                  status TEXT DEFAULT 'To Apply', 
                  date TEXT, 
                  applied INTEGER DEFAULT 0, 
                  username TEXT)''')
    
    conn.commit()
    c.close()
    conn.close()
    print("✅ Supabase Database initialized successfully.")

def create_user(username, password, email="user@example.com"):
    """Registers a new user with email for reminders."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role, email) VALUES (%s, %s, %s, %s)", 
                  (username, password, "user", email))
        conn.commit()
        return True, "Success"
    except Exception as e:
        return False, str(e)
    finally:
        c.close()
        conn.close()

def verify_user(username, password):
    """Verifies login and returns (username, role)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, role FROM users WHERE username=%s AND password=%s", 
              (username, password))
    user = c.fetchone()
    c.close()
    conn.close()
    return user

def add_job(company, role, job_url, job_description, username):
    """Adds a new job linked to a specific user."""
    conn = get_connection()
    c = conn.cursor()
    date_added = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''
        INSERT INTO applications (company, role, url, description, date, username)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (company, role, job_url, job_description, date_added, username))
    
    conn.commit()
    c.close()
    conn.close()

def fetch_jobs(username):
    """Fetches jobs for the specific logged-in user."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM applications WHERE username=%s", (username,))
    data = c.fetchall()
    c.close()
    conn.close()
    return data

# --- GOAL TRACKING FUNCTIONS (FIXED) ---

def add_goal(username, goal_name, days, syllabus):
    """Adds a goal. Uses 'is_active' to match your fetch logic."""
    conn = get_connection()
    c = conn.cursor()
    query = """
        INSERT INTO goals (username, goal_name, start_date, days, syllabus, is_active) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    c.execute(query, (username, goal_name, datetime.now().date(), days, syllabus, 1))
    conn.commit()
    c.close()
    conn.close()

def get_user_goals(username):
    """Fetches active goals for the user. Uses 'days' as the duration alias."""
    conn = get_connection()
    c = conn.cursor()
    # Check for 'days' column to ensure compatibility
    c.execute("SELECT id, goal_name, start_date, days, is_active, syllabus FROM goals WHERE username=%s AND is_active=1", (username,))
    data = c.fetchall()
    c.close()
    conn.close()
    return data

# --- ADMIN SPECIAL FUNCTIONS ---

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, role, email FROM users")
    data = c.fetchall() 
    c.close()
    conn.close()
    return data

def get_user_email(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE username = %s", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def delete_user(username):
    try:
        # Step 1: Delete all linked goals first (Fixes foreign key error)
        supabase.table("goals").delete().eq("username", username).execute()
        
        # Step 2: Delete the actual user
        supabase.table("users").delete().eq("username", username).execute()
        
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False
    

def update_tables():
    """Safety function to add missing columns to your live database."""
    try:
        conn = get_connection()
        c = conn.cursor()
        # Add the missing columns needed for your new features
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS days INTEGER DEFAULT 30;")
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS syllabus TEXT;")
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1;")
        conn.commit()
        c.close()
        conn.close()
        print("✅ Database columns updated!")
    except Exception as e:
        print(f"❌ Migration Error: {e}")

def get_all_active_goals_global():
    import sqlite3
    conn = sqlite3.connect('career_agent.db')
    c = conn.cursor()
    # Join goals with users to get the email address automatically
    c.execute('''SELECT g.username, g.goal_name, g.start_date, g.days, g.syllabus, u.email 
                 FROM goals g 
                 JOIN users u ON g.username = u.username''')
    data = c.fetchall()
    conn.close()
    return data

def delete_goal_by_id(goal_id):
    """Permanently removes a specific goal journey."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM goals WHERE id=%s", (goal_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting goal: {e}")
        return False
    finally:
        c.close()
        conn.close()

if __name__ == "__main__":
    init_db()
    update_tables()
