"""
Driver Distraction & Drowsiness Monitoring - Dashboard Server
Run this on a hosting service (Render, Railway, etc.) or locally.
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

# In-memory storage (for production, use a real database)
alerts = []
MAX_ALERTS = 500  # keep last 500 alerts

# Stats counters
stats = {
    "total_alerts": 0,
    "phone_alerts": 0,
    "drowsy_alerts": 0,
    "yawn_alerts": 0,
    "distraction_alerts": 0,
    "last_status": "offline",
    "last_update": None,
}


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/alert", methods=["POST"])
def receive_alert():
    """Receive an alert from the inference script."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    alert = {
        "id": stats["total_alerts"] + 1,
        "type": data.get("type", "unknown"),
        "class": data.get("class", ""),
        "confidence": data.get("confidence", 0),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": data.get("duration", 0),
    }

    alerts.append(alert)
    stats["total_alerts"] += 1
    stats["last_update"] = alert["timestamp"]

    # Update category counters
    alert_type = alert["type"]
    if alert_type == "phone":
        stats["phone_alerts"] += 1
    elif alert_type == "drowsy":
        stats["drowsy_alerts"] += 1
    elif alert_type == "yawn":
        stats["yawn_alerts"] += 1
    elif alert_type == "distraction":
        stats["distraction_alerts"] += 1

    # Keep only last MAX_ALERTS
    if len(alerts) > MAX_ALERTS:
        alerts.pop(0)

    return jsonify({"status": "ok", "id": alert["id"]})


@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    """Receive heartbeat from inference script to show system is online."""
    data = request.get_json() or {}
    stats["last_status"] = data.get("status", "online")
    stats["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({"status": "ok"})


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Return recent alerts for the dashboard."""
    limit = request.args.get("limit", 50, type=int)
    return jsonify(alerts[-limit:][::-1])  # newest first


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return summary statistics."""
    return jsonify(stats)


@app.route("/api/clear", methods=["POST"])
def clear_alerts():
    """Clear all alerts."""
    alerts.clear()
    stats["total_alerts"] = 0
    stats["phone_alerts"] = 0
    stats["drowsy_alerts"] = 0
    stats["yawn_alerts"] = 0
    stats["distraction_alerts"] = 0
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
