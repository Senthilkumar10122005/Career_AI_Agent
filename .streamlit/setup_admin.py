import psycopg2
import os
import streamlit as st

# 1. Get the cloud connection string
# If running locally, make sure your .streamlit/secrets.toml is correct
DB_URL = "postgresql://postgres.kkcklkchlcmmnnetdrkd:Senthil111327%40%23@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

def make_me_admin():
    try:
        conn = psycopg2.connect(DB_URL)
        c = conn.cursor()

        # Check if the user exists
        c.execute("SELECT username FROM users WHERE username='senthil33'")
        user = c.fetchone()

        if not user:
            # Create the admin from scratch
            c.execute("INSERT INTO users (username, password, role, email) VALUES (%s, %s, %s, %s)", 
                      ("senthil33", "Senthil111327@#", "admin", "admin@example.com"))
            print("✅ Admin user 'senthil33' created in Supabase!")
        else:
            # If the user already exists (because you registered), just upgrade the role
            c.execute("UPDATE users SET role='admin' WHERE username='senthil33'")
            print("✅ User 'senthil33' found. Role upgraded to ADMIN in Supabase!")

        conn.commit()
        c.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")

if __name__ == "__main__":
    make_me_admin()