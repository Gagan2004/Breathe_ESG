import psycopg2
import os

DATABASE_URL = "postgresql://postgres.uqhptrdflapgiozzsdeb:1y0ntu63CRu0xP4l@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"

def validate():
    try:
        print("Connecting to Supabase Database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # 1. Verify Tables Exist
        required_tables = [
            'ingestion_organization',
            'ingestion_user',
            'ingestion_ingestionjob',
            'ingestion_rawrecord',
            'ingestion_normalizedactivity',
            'ingestion_audittrail',
            'authtoken_token'
        ]
        
        print("\n--- Verifying Database Schema (Tables) ---")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        existing_tables = [r[0] for r in cur.fetchall()]
        
        all_passed = True
        for table in required_tables:
            if table in existing_tables:
                print(f"[PASS] Table '{table}' exists.")
            else:
                print(f"[FAIL] Table '{table}' is MISSING!")
                all_passed = False

        # 2. Verify Seed Data
        print("\n--- Verifying Seeded Data ---")
        
        # Check Organization
        cur.execute("SELECT COUNT(*) FROM ingestion_organization WHERE name = 'Acme Corporation';")
        org_count = cur.fetchone()[0]
        if org_count > 0:
            print("[PASS] Organization 'Acme Corporation' seeded successfully.")
        else:
            print("[FAIL] Organization 'Acme Corporation' is missing.")
            all_passed = False
            
        # Check Users
        users_to_check = ['analyst', 'manager', 'admin']
        for u in users_to_check:
            cur.execute("SELECT COUNT(*) FROM ingestion_user WHERE username = %s;", (u,))
            user_count = cur.fetchone()[0]
            if user_count > 0:
                print(f"[PASS] User '{u}' seeded successfully.")
            else:
                print(f"[FAIL] User '{u}' is missing.")
                all_passed = False
                
        # Check Tokens
        cur.execute("""
            SELECT u.username, t.key 
            FROM authtoken_token t
            JOIN ingestion_user u ON t.user_id = u.id;
        """)
        tokens = cur.fetchall()
        print(f"[INFO] Found {len(tokens)} API tokens in database:")
        for username, key in tokens:
            print(f"       - User '{username}': Token '{key[:8]}...'")
            
        if all_passed:
            print("\nVerification Status: SUCCESS. The database meets all schema and seed data requirements.")
        else:
            print("\nVerification Status: FAILED. Please check the errors above.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print("Validation failed with error:")
        print(e)

if __name__ == "__main__":
    validate()
