import os
import time
from flask import Flask, request, jsonify, render_template
from prometheus_flask_exporter import PrometheusMetrics

# Import our shared database layer and blueprints
from database import get_db_connection
from routes.ui import ui_bp
from routes.admin import admin_bp

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# ── Health ────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    try:
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
        conn.commit()
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
        cur.execute("SELECT id, secret_key, secret_value, created_at FROM secrets;")
        rows = cur.fetchall()
        
        secrets_list = []
        for row in rows:
            secrets_list.append({
                "id": row[0],
                "secret_key": row[1],
                "secret_value": row[2],
                "created_at": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else None
            })
            
        cur.close()
        conn.close()
        return jsonify({"secrets": secrets_list, "count": len(secrets_list)}), 200
    except Exception as e:
        return jsonify({"error": "Database read error", "detail": str(e)}), 500

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
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "secret deleted", "key": key}), 200
    except Exception as e:
        return jsonify({"error": "Database delete error", "detail": str(e)}), 500
    
# ── Web UI Dashboard View ────────────────────────────────────────────────
@app.route("/")
def dashboard_ui():
    """Serves the frontend operator interface from the templates directory."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, secret_key, secret_value, created_at FROM secrets ORDER BY id DESC;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        rows = []
        print(f"UI Fetch Error: {e}")

    return render_template("index.html", rows=rows)

# ── Register Blueprints ───────────────────────────────────────────────────
app.register_blueprint(ui_bp, url_prefix='/ui')
app.register_blueprint(admin_bp, url_prefix='/admin') # Hooks up your dashboard route to /admin

# ── Run ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)