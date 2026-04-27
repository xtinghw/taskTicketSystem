from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

init_db()

def add_audit_log(ticket_id, action, actor, details=None):
    conn = get_db_connection()

    conn.execute("""
        INSERT INTO audit_logs (
            ticket_id,
            action,
            actor,
            details
        )
        VALUES (?, ?, ?, ?)
    """, (
        ticket_id,
        action,
        actor,
        details
    ))

    conn.commit()
    conn.close()

@app.route("/dashboard")
def dashboard_page():
    return render_template("index.html")

@app.route("/")
def home():
    return "Task Ticket System is running."


@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    assigned_to = data.get("assigned_to")
    proof_required = data.get("proof_required", 1)
    
    # Basic validation must have title, description, and assigned_to fields
    if not title or not description or not assigned_to:
        return jsonify({
            "error": "title, description, and assigned_to are required"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO tickets (
            title,
            description,
            assigned_to,
            proof_required
        )
        VALUES (?, ?, ?, ?)
    """, (
        title,
        description,
        assigned_to,
        proof_required
    ))

    conn.commit()

    ticket_id = cursor.lastrowid

    conn.close()

    add_audit_log(
    ticket_id=ticket_id,
    action="created",
    actor="manager",
    details=f"Ticket created and assigned to {assigned_to}"
)

    return jsonify({
        "message": "Ticket created successfully",
        "ticket_id": ticket_id
    }), 201

@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()

    tickets = conn.execute("""
        SELECT *
        FROM tickets
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    ticket_list = []

    for ticket in tickets:
        ticket_list.append({
            "id": ticket["id"],
            "title": ticket["title"],
            "description": ticket["description"],
            "assigned_to": ticket["assigned_to"],
            "status": ticket["status"],
            "proof_required": ticket["proof_required"],
            "proof_path": ticket["proof_path"],
            "manager_comment": ticket["manager_comment"],
            "created_at": ticket["created_at"],
            "updated_at": ticket["updated_at"]
        })

    return jsonify(ticket_list), 200

@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    conn.close()

    if ticket is None:
        return jsonify({
            "error": "Ticket not found"
        }), 404

    return jsonify({
        "id": ticket["id"],
        "title": ticket["title"],
        "description": ticket["description"],
        "assigned_to": ticket["assigned_to"],
        "status": ticket["status"],
        "proof_required": ticket["proof_required"],
        "proof_path": ticket["proof_path"],
        "manager_comment": ticket["manager_comment"],
        "created_at": ticket["created_at"],
        "updated_at": ticket["updated_at"]
    }), 200

@app.route("/tickets/<int:ticket_id>/submit", methods=["PATCH"])
def submit_ticket(ticket_id):
    data = request.get_json()

    proof_path = data.get("proof_path")

    if not proof_path:
        return jsonify({
            "error": "proof_path is required"
        }), 400

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if ticket["status"] != "pending":
        conn.close()
        return jsonify({
            "error": "Only pending tickets can be submitted"
        }), 400

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            proof_path = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "submitted",
        proof_path,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
    ticket_id=ticket_id,
    action="submitted",
    actor="staff",
    details=f"Proof submitted: {proof_path}"
)

    return jsonify({
        "message": "Ticket submitted successfully",
        "ticket_id": ticket_id,
        "status": "submitted"
    }), 200

@app.route("/tickets/<int:ticket_id>/approve", methods=["PATCH"])
def approve_ticket(ticket_id):
    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if ticket["status"] != "submitted":
        conn.close()
        return jsonify({
            "error": "Only submitted tickets can be approved"
        }), 400

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "approved",
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
    ticket_id=ticket_id,
    action="approved",
    actor="manager",
    details="Ticket approved by manager"
)

    return jsonify({
        "message": "Ticket approved successfully",
        "ticket_id": ticket_id,
        "status": "approved"
    }), 200

@app.route("/tickets/<int:ticket_id>/reject", methods=["PATCH"])
def reject_ticket(ticket_id):
    data = request.get_json()

    manager_comment = data.get("manager_comment")

    if not manager_comment:
        return jsonify({
            "error": "manager_comment is required when rejecting a ticket"
        }), 400

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if ticket["status"] != "submitted":
        conn.close()
        return jsonify({
            "error": "Only submitted tickets can be rejected"
        }), 400

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            manager_comment = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "rejected",
        manager_comment,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
    ticket_id=ticket_id,
    action="rejected",
    actor="manager",
    details=manager_comment
    )

    return jsonify({
        "message": "Ticket rejected successfully",
        "ticket_id": ticket_id,
        "status": "rejected",
        "manager_comment": manager_comment
    }), 200


@app.route("/tickets/<int:ticket_id>/resubmit", methods=["PATCH"])
def resubmit_ticket(ticket_id):
    data = request.get_json()

    proof_path = data.get("proof_path")

    if not proof_path:
        return jsonify({
            "error": "proof_path is required"
        }), 400

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return jsonify({
            "error": "Ticket not found"
        }), 404

    if ticket["status"] != "rejected":
        conn.close()
        return jsonify({
            "error": "Only rejected tickets can be resubmitted"
        }), 400

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            proof_path = ?,
            manager_comment = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        "submitted",
        proof_path,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
    ticket_id=ticket_id,
    action="resubmitted",
    actor="staff",
    details=f"New proof submitted: {proof_path}"
)

    return jsonify({
        "message": "Ticket resubmitted successfully",
        "ticket_id": ticket_id,
        "status": "submitted"
    }), 200

@app.route("/tickets/<int:ticket_id>/logs", methods=["GET"])
def get_ticket_logs(ticket_id):
    conn = get_db_connection()

    logs = conn.execute("""
        SELECT *
        FROM audit_logs
        WHERE ticket_id = ?
        ORDER BY created_at ASC
    """, (ticket_id,)).fetchall()

    conn.close()

    log_list = []

    for log in logs:
        log_list.append({
            "id": log["id"],
            "ticket_id": log["ticket_id"],
            "action": log["action"],
            "actor": log["actor"],
            "details": log["details"],
            "created_at": log["created_at"]
        })

    return jsonify(log_list), 200

@app.route("/staff/<staff_name>/failures", methods=["GET"])
def get_staff_failures(staff_name):
    conn = get_db_connection()

    rejected_tickets = conn.execute("""
        SELECT *
        FROM tickets
        WHERE assigned_to = ?
        AND status = 'rejected'
        ORDER BY updated_at DESC
    """, (staff_name,)).fetchall()

    failure_count = len(rejected_tickets)

    ticket_list = []

    for ticket in rejected_tickets:
        ticket_list.append({
            "id": ticket["id"],
            "title": ticket["title"],
            "description": ticket["description"],
            "status": ticket["status"],
            "manager_comment": ticket["manager_comment"],
            "updated_at": ticket["updated_at"]
        })

    conn.close()

    return jsonify({
        "staff_name": staff_name,
        "failure_count": failure_count,
        "rejected_tickets": ticket_list
    }), 200

@app.route("/staff/<staff_name>/failure-history", methods=["GET"])
def get_staff_failure_history(staff_name):
    conn = get_db_connection()

    failure_logs = conn.execute("""
        SELECT 
            audit_logs.id AS log_id,
            audit_logs.ticket_id,
            audit_logs.action,
            audit_logs.actor,
            audit_logs.details,
            audit_logs.created_at,
            tickets.title,
            tickets.assigned_to
        FROM audit_logs
        JOIN tickets ON audit_logs.ticket_id = tickets.id
        WHERE tickets.assigned_to = ?
        AND audit_logs.action = 'rejected'
        ORDER BY audit_logs.created_at DESC
    """, (staff_name,)).fetchall()

    failure_history = []

    for log in failure_logs:
        failure_history.append({
            "log_id": log["log_id"],
            "ticket_id": log["ticket_id"],
            "title": log["title"],
            "assigned_to": log["assigned_to"],
            "reason": log["details"],
            "rejected_at": log["created_at"]
        })

    conn.close()

    return jsonify({
        "staff_name": staff_name,
        "failure_count": len(failure_history),
        "failure_history": failure_history
    }), 200

@app.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():
    conn = get_db_connection()

    total_tickets = conn.execute("""
        SELECT COUNT(*) AS count
        FROM tickets
    """).fetchone()["count"]

    status_counts = conn.execute("""
        SELECT status, COUNT(*) AS count
        FROM tickets
        GROUP BY status
    """).fetchall()

    staff_failures = conn.execute("""
        SELECT 
            tickets.assigned_to,
            COUNT(audit_logs.id) AS failure_count
        FROM tickets
        LEFT JOIN audit_logs 
            ON tickets.id = audit_logs.ticket_id
            AND audit_logs.action = 'rejected'
        GROUP BY tickets.assigned_to
        ORDER BY failure_count DESC
    """).fetchall()

    conn.close()

    status_summary = {
        "pending": 0,
        "submitted": 0,
        "approved": 0,
        "rejected": 0
    }

    for row in status_counts:
        status_summary[row["status"]] = row["count"]

    staff_failure_list = []

    for row in staff_failures:
        staff_failure_list.append({
            "staff_name": row["assigned_to"],
            "failure_count": row["failure_count"]
        })

    return jsonify({
        "total_tickets": total_tickets,
        "status_summary": status_summary,
        "staff_failures": staff_failure_list
    }), 200

if __name__ == "__main__":
    app.run(debug=True)