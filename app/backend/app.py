import os

import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "devopsdb"),
        user=os.getenv("DB_USER", "devopsuser"),
        password=os.getenv("DB_PASSWORD", "devopspassword"),
    )


def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'pending'
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


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


# CREATE TASK
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or not data.get("title"):
        return jsonify({
            "error": "title is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (title, description, status)
        VALUES (%s, %s, %s)
        RETURNING id, title, description, status
        """,
        (
            data["title"],
            data.get("description"),
            data.get("status", "pending")
        )
    )

    task = cursor.fetchone()

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({
        "task": {
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "status": task[3]
        }
    }), 201


# GET ALL TASKS
@app.route("/tasks", methods=["GET"])
def get_tasks():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, description, status
        FROM tasks
        ORDER BY id
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    tasks = []

    for row in rows:
        tasks.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "status": row[3]
        })

    return jsonify(tasks)


# GET SINGLE TASK
@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, description, status
        FROM tasks
        WHERE id = %s
        """,
        (task_id,)
    )

    task = cursor.fetchone()

    cursor.close()
    connection.close()

    if not task:
        return jsonify({
            "error": "task not found"
        }), 404

    return jsonify({
        "id": task[0],
        "title": task[1],
        "description": task[2],
        "status": task[3]
    })


# UPDATE TASK
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "request body is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title = COALESCE(%s, title),
            description = COALESCE(%s, description),
            status = COALESCE(%s, status)
        WHERE id = %s
        RETURNING id, title, description, status
        """,
        (
            data.get("title"),
            data.get("description"),
            data.get("status"),
            task_id
        )
    )

    task = cursor.fetchone()

    connection.commit()
    cursor.close()
    connection.close()

    if not task:
        return jsonify({
            "error": "task not found"
        }), 404

    return jsonify({
        "id": task[0],
        "title": task[1],
        "description": task[2],
        "status": task[3]
    })


# DELETE TASK
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM tasks
        WHERE id = %s
        RETURNING id
        """,
        (task_id,)
    )

    deleted_task = cursor.fetchone()

    connection.commit()
    cursor.close()
    connection.close()

    if not deleted_task:
        return jsonify({
            "error": "task not found"
        }), 404

    return jsonify({
        "message": "task deleted successfully"
    })


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
