import os
from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# In-memory store for dev — PostgreSQL will replace this in Phase 4
store = {}

# ── Health ────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "vaultflow-api"}), 200

# ── Secrets ───────────────────────────────────────────────────────────────
@app.route("/secrets", methods=["POST"])
def create_secret():
    data = request.get_json()
    if not data or "key" not in data or "value" not in data:
        return jsonify({"error": "key and value are required"}), 400
    store[data["key"]] = data["value"]
    return jsonify({"message": "secret stored", "key": data["key"]}), 201

@app.route("/secrets", methods=["GET"])
def list_secrets():
    return jsonify({"secrets": list(store.keys()), "count": len(store)}), 200

@app.route("/secrets/<key>", methods=["DELETE"])
def delete_secret(key):
    if key not in store:
        return jsonify({"error": "key not found"}), 404
    del store[key]
    return jsonify({"message": "secret deleted", "key": key}), 200

# ── Run ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)