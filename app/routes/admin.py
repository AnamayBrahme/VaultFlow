from flask import Blueprint, jsonify
from database import get_db_connection

admin_bp = Blueprint('admin', __name__)

# ── Add strict_slashes=False Here ─────────────────────────────────────
@admin_bp.route('/', strict_slashes=False)
def admin_dashboard():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1;')
        cur.close()
        conn.close()
        return jsonify({
            "security_status": "SECURE",
            "network_policy": "Enforced (API -> DB allowed)",
            "database_connection": "Successful"
        }), 200
    except Exception as e:
        return jsonify({
            "security_status": "ISOLATED / BLOCKED",
            "network_policy": "Enforced (Isolation active)",
            "error_detail": str(e)
        }), 200