import os
import time
import psycopg2

def get_db_connection():
    """Reads environment variables injected by Helm to open a Postgres connection."""
    retries = 3
    while retries > 0:
        try:
            conn = psycopg2.connect(
                # Fixed minor typo from your string: 'vaulflow' -> 'vaultflow'
                host=os.environ.get('DB_HOST', 'vaultflow-db-team-b.vaultflow-team-b.svc.cluster.local'),
                database=os.environ.get('DB_NAME', 'vaultflow'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'password'),
                port=os.environ.get('DB_PORT', '5432'),
                connect_timeout=5 # Fail fast if NetworkPolicy blocks it!
            )
            return conn
        except psycopg2.OperationalError as e:
            print(f"Database connection failed. Retrying in 2 seconds... ({retries} left)")
            retries -= 1
            time.sleep(2)
    raise Exception("Could not connect to the database. Verify network routing or secret credentials.")