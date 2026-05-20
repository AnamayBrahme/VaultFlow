import os
import time
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# ── Database Connection Helper ──────────────────────────────────────────
def get_db_connection():
    """Reads environment variables injected by Helm to open a Postgres connection."""
    retries = 3
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                database=os.environ.get('DB_NAME', 'vaulflow'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'password'),
                port=os.environ.get('DB_PORT', '5432')
            )
            return conn
        except psycopg2.OperationalError as e:
            print(f"Database connection failed. Retrying in 2 seconds... ({retries} left)")
            retries -= 1
            time.sleep(2)
    raise Exception("Could not connect to the database. Verify network routing or secret credentials.")

# ── Health ────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    try:
        # Verify the database is actually reachable during health checks
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1;')
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "service": "vaultflow-api", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# ── Secrets ───────────────────────────────────────────────────────────────
@app.route("/secrets", methods=["POST"])
def create_secret():
    data = request.get_json()
    if not data or "key" not in data or "value" not in data:
        return jsonify({"error": "key and value are required"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO secrets (secret_key, secret_value) VALUES (%s, %s)
            ON CONFLICT (secret_key) DO UPDATE SET secret_value = EXCLUDED.secret_value;
            """,
            (data["key"], data["value"])
        )
        conn.commit() # ◄ THIS SAYS: Write this permanently to disk!
        cur.close()
        conn.close()
        return jsonify({"message": "secret stored", "key": data["key"]}), 201
    except Exception as e:
        return jsonify({"error": "Database write error", "detail": str(e)}), 500

@app.route("/secrets", methods=["GET"])
def list_secrets():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch all structural columns from the database table
        cur.execute("SELECT id, secret_key, secret_value, created_at FROM secrets;")
        rows = cur.fetchall()
        
        # 2. Map row tuples into structured dictionary objects matching your UI layout
        secrets_list = []
        for row in rows:
            secrets_list.append({
                "id": row[0],
                "secret_key": row[1],
                "secret_value": row[2],
                # Format timestamps into clean text blocks if your API outputs them
                "created_at": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None
            })
            
        cur.close()
        conn.close()
        
        # 3. Return the fully populated objects list along with the calculated count
        return jsonify({
            "secrets": secrets_list, 
            "count": len(secrets_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Database read error", 
            "detail": str(e)
        }), 500

@app.route("/secrets/<key>", methods=["DELETE"])
def delete_secret(key):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM secrets WHERE secret_key = %s;", (key,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "key not found"}), 404
            
        cur.execute("DELETE FROM secrets WHERE secret_key = %s;", (key,))
        conn.commit() # ◄ ALSO NEEDED HERE: Save the deletion permanently!
        cur.close()
        conn.close()
        return jsonify({"message": "secret deleted", "key": key}), 200
    except Exception as e:
        return jsonify({"error": "Database delete error", "detail": str(e)}), 500

# ── Run ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)