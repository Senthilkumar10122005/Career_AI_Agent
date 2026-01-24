import sqlite3
import psycopg2
from psycopg2 import sql
import streamlit as st
from datetime import datetime
import os

# Get the Connection String
DB_URL = st.secrets.get("SUPABASE_DB_URL") or os.environ.get("SUPABASE_DB_URL")

def get_connection():
    """Returns a PostgreSQL connection with proper error handling."""
    if not DB_URL:
        raise ValueError("SUPABASE_DB_URL is missing! Check your secrets.toml.")
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}")

def init_db():
    """Initializes all tables in the Supabase PostgreSQL database."""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # 1. Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 2. Goals Table (with foreign key constraint)
        c.execute('''CREATE TABLE IF NOT EXISTS goals (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            goal_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            days INTEGER DEFAULT 30,
            syllabus TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        )''')
        
        # 3. Applications Table (with foreign key constraint)
        c.execute('''CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            url TEXT,
            description TEXT,
            status TEXT DEFAULT 'To Apply',
            date TEXT,
            applied INTEGER DEFAULT 0,
            username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        )''')
        
        # Create indexes for better query performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_goals_username ON goals(username)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_goals_active ON goals(is_active)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_applications_username ON applications(username)')
        
        conn.commit()
        print("✅ Supabase Database initialized successfully.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Database initialization error: {e}")
        raise
    finally:
        c.close()
        conn.close()

def create_user(username, password, email="user@example.com"):
    """Registers a new user with email for reminders."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, password, role, email) VALUES (%s, %s, %s, %s)",
            (username, password, "user", email)
        )
        conn.commit()
        return True, "Success"
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "Username already exists"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        c.close()
        conn.close()

def verify_user(username, password):
    """Verifies login and returns (username, role)."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT username, role FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = c.fetchone()
        return user
    finally:
        c.close()
        conn.close()

def add_job(company, role, job_url, job_description, username):
    """Adds a new job linked to a specific user."""
    conn = get_connection()
    c = conn.cursor()
    try:
        date_added = datetime.now().strftime("%Y-%m-%d")
        c.execute('''
            INSERT INTO applications (company, role, url, description, date, username)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (company, role, job_url, job_description, date_added, username))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to add job: {e}")
    finally:
        c.close()
        conn.close()

def fetch_jobs(username):
    """Fetches jobs for the specific logged-in user."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "SELECT * FROM applications WHERE username=%s ORDER BY date DESC",
            (username,)
        )
        data = c.fetchall()
        return data
    finally:
        c.close()
        conn.close()

# --- GOAL TRACKING FUNCTIONS ---

def add_goal(username, goal_name, days, syllabus):
    """Adds a goal. Uses 'is_active' to match your fetch logic."""
    conn = get_connection()
    c = conn.cursor()
    try:
        query = """
            INSERT INTO goals (username, goal_name, start_date, days, syllabus, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        c.execute(query, (username, goal_name, datetime.now().date(), days, syllabus, 1))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to add goal: {e}")
    finally:
        c.close()
        conn.close()

def get_user_goals(username):
    """Fetches active goals for the user. Uses 'days' as the duration alias."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            """SELECT id, goal_name, start_date, days, is_active, syllabus 
               FROM goals 
               WHERE username=%s AND is_active=1
               ORDER BY start_date DESC""",
            (username,)
        )
        data = c.fetchall()
        return data
    finally:
        c.close()
        conn.close()

def get_all_active_goals_global():
    """Fetches all active goals with user email information."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Join goals with users to get the email address automatically
        c.execute('''
            SELECT g.username, g.goal_name, g.start_date, g.days, g.syllabus, u.email
            FROM goals g
            JOIN users u ON g.username = u.username
            WHERE g.is_active = 1
            ORDER BY g.start_date DESC
        ''')
        data = c.fetchall()
        return data
    finally:
        c.close()
        conn.close()

def delete_goal_by_id(goal_id):
    """Permanently removes a specific goal journey."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM goals WHERE id=%s", (goal_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error deleting goal: {e}")
        return False
    finally:
        c.close()
        conn.close()

# --- ADMIN SPECIAL FUNCTIONS ---

def get_all_users():
    """Fetches all users with their information."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT username, role, email FROM users ORDER BY username")
        data = c.fetchall()
        return data
    finally:
        c.close()
        conn.close()

def get_user_email(username):
    """Retrieves email for a specific user."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT email FROM users WHERE username = %s", (username,))
        result = c.fetchone()
        return result[0] if result else None
    finally:
        c.close()
        conn.close()

def delete_user(username):
    """
    Deletes a user and all their related data (goals, applications).
    Fixed to work properly with PostgreSQL and foreign key constraints.
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        # Method 1: If you have CASCADE constraints (recommended), just delete the user
        # The database will automatically delete related records
        c.execute("DELETE FROM users WHERE username = %s", (username,))
        
        # Method 2: If CASCADE is not set up, manually delete related records first
        # Uncomment these lines if CASCADE constraints are not working
        # c.execute("DELETE FROM goals WHERE username = %s", (username,))
        # c.execute("DELETE FROM applications WHERE username = %s", (username,))
        # c.execute("DELETE FROM users WHERE username = %s", (username,))
        
        conn.commit()
        deleted_rows = c.rowcount
        
        if deleted_rows > 0:
            print(f"✅ Successfully deleted user: {username}")
            return True
        else:
            print(f"⚠️ User not found: {username}")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Database Error while deleting user: {e}")
        return False
    finally:
        c.close()
        conn.close()

def update_tables():
    """Safety function to add missing columns to your live database."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Add the missing columns needed for your features
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS days INTEGER DEFAULT 30")
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS syllabus TEXT")
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        c.execute("ALTER TABLE goals ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        c.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        conn.commit()
        print("✅ Database columns updated!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration Error: {e}")
    finally:
        c.close()
        conn.close()

def update_job_status(job_id, new_status):
    """Updates the status of a job application."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "UPDATE applications SET status = %s WHERE id = %s",
            (new_status, job_id)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating job status: {e}")
        return False
    finally:
        c.close()
        conn.close()

def mark_job_applied(job_id):
    """Marks a job as applied."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "UPDATE applications SET applied = 1, status = 'Applied' WHERE id = %s",
            (job_id,)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error marking job as applied: {e}")
        return False
    finally:
        c.close()
        conn.close()

def deactivate_goal(goal_id):
    """Marks a goal as inactive instead of deleting it (soft delete)."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE goals SET is_active = 0 WHERE id = %s", (goal_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error deactivating goal: {e}")
        return False
    finally:
        c.close()
        conn.close()

def get_user_stats(username):
    """Gets statistics for a specific user."""
    conn = get_connection()
    c = conn.cursor()
    try:
        stats = {}
        
        # Count active goals
        c.execute("SELECT COUNT(*) FROM goals WHERE username = %s AND is_active = 1", (username,))
        stats['active_goals'] = c.fetchone()[0]
        
        # Count total applications
        c.execute("SELECT COUNT(*) FROM applications WHERE username = %s", (username,))
        stats['total_applications'] = c.fetchone()[0]
        
        # Count applied jobs
        c.execute("SELECT COUNT(*) FROM applications WHERE username = %s AND applied = 1", (username,))
        stats['applied_jobs'] = c.fetchone()[0]
        
        return stats
    finally:
        c.close()
        conn.close()

if __name__ == "__main__":
    init_db()
    update_tables()