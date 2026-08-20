import os

import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "devopsdb"),
        user=os.getenv("DB_USER", "devopsuser"),
        password=os.getenv("DB_PASSWORD", "devopspassword"),
    )


@app.route("/")
def home():
    return jsonify({
        "message": "DevOps Task Platform API",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/db-health")
def db_health():
    try:
        connection = get_db_connection()
        connection.close()

        return jsonify({
            "database": "connected",
            "status": "healthy"
        })

    except Exception as error:
        return jsonify({
            "database": "disconnected",
            "status": "unhealthy",
            "error": str(error)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
