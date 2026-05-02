from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "dev_secret_key_change_later"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

#user table
USERS = {
    "manager":{
        "password": "1234",
        "role": "manager",
        "display_name": "Manager"
    },
    "staffa": {
        "password": "1234",
        "role": "staff",
        "display_name": "Staff A"
    },
    "staffb":{
        "password": "1234",
        "role": "staff",
        "display_name": "Staff B"        
    }
}

STATUS_PENDING = "pending"
STATUS_ASSIGNED = "assigned"
STATUS_IN_PROGRESS = "in_progress"
STATUS_SUBMITTED = "submitted"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

init_db()

def require_login():
    return "username" in session

def require_role(role):
    return session.get("role") == role

def error_response(message, status_code):
    return jsonify({
        "success": False,
        "error": message
    }), status_code

def current_user_role():
    return session.get("role")

def current_user_display_name():
    return session.get("display_name", "Unknown")

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

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = USERS.get(username)

    if user is None or user["password"] != password:
        return error_response("Invalid username or password", 401) 
     

    session["username"] = username
    session["role"] = user["role"]
    session["display_name"] = user.get("display_name", username)

    return jsonify({
        "message": "Login successful",
        "username": username,
        "role": user["role"],
        "display_name": session["display_name"]
    }), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    }), 200


@app.route("/me", methods=["GET"])
def me():
    if "username" not in session:
        return jsonify({
            "logged_in": False
        }), 200

    return jsonify({
        "logged_in": True,
        "username": session["username"],
        "role": session["role"],
        "display_name": session["display_name"]
    }), 200


@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json()

    ticket_type = data.get("ticket_type", "task")
    title = data.get("title")
    description = data.get("description")
    reported_by = session.get("display_name", "Unknown")
    role = session.get("role")

    if role == "staff":
        reported_to = "Manager"
        assigned_to = None
    else:
        reported_to = None
        assigned_to = data.get("assigned_to")

    visibility = data.get("visibility", "public")
    proof_required = data.get("proof_required", 1)
    proof_type = data.get("proof_type", "photo")
    
    # Basic validation must have title, description, and assigned_to fields
    if not title or not description:
        return error_response("Title and description are required", 400)

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO tickets (
            ticket_type,
            title,
            description,
            reported_by,
            reported_to,
            assigned_to,
            visibility,
            proof_required,
            proof_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_type,
            title,
            description,
            reported_by,
            reported_to,
            assigned_to,
            visibility,
            proof_required,
            proof_type
    ))

    conn.commit()

    ticket_id = cursor.lastrowid

    conn.close()

    if role == "manager":
        details = f"Ticket created by {reported_by} and assigned to {assigned_to}"
    else:
        details = f"Ticket reported by {reported_by} to {reported_to}"

    add_audit_log(
        ticket_id=ticket_id,
        action="created",
        actor=reported_by,
        details=details
    )

    return jsonify({
        "message": "Ticket created successfully",
        "ticket_id": ticket_id
    }), 201

@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()

    role = current_user_role()
    display_name = current_user_display_name()

    if role == "manager":
        tickets = conn.execute("""
            SELECT *
            FROM tickets
            ORDER BY created_at DESC
        """).fetchall()
    else:
        tickets = conn.execute("""
            SELECT *
            FROM tickets
            WHERE visibility = 'public'
               OR reported_by = ?
               OR assigned_to = ?
            ORDER BY created_at DESC
        """, (display_name, display_name)).fetchall()

    conn.close()

    ticket_list = []

    for ticket in tickets:
        ticket_list.append({
            "id": ticket["id"],
            "ticket_type": ticket["ticket_type"],
            "title": ticket["title"],
            "description": ticket["description"],
            "reported_by": ticket["reported_by"],
            "reported_to": ticket["reported_to"],
            "assigned_to": ticket["assigned_to"],
            "visibility": ticket["visibility"],
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

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    role = current_user_role()
    display_name = current_user_display_name()

    if role != "manager":
        if (
            ticket["visibility"] == "manager_only"
            and ticket["reported_by"] != display_name
            and ticket["assigned_to"] != display_name
        ):
            conn.close()
            return error_response("You do not have permission to view this ticket", 403)

    conn.close()

    return jsonify({
        "id": ticket["id"],
        "ticket_type": ticket["ticket_type"],
        "title": ticket["title"],
        "description": ticket["description"],
        "reported_by": ticket["reported_by"],
        "reported_to": ticket["reported_to"],
        "assigned_to": ticket["assigned_to"],
        "visibility": ticket["visibility"],
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
        return error_response("proof_path is required", 400)

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if ticket["status"] not in  [STATUS_PENDING, STATUS_IN_PROGRESS]:
        conn.close()
        return error_response("Only pending or in progress tickets can be submitted", 400)
    
    conn.execute("""
        UPDATE tickets
        SET status = ?,
            proof_path = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_SUBMITTED,
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
        "status": STATUS_SUBMITTED
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
        return error_response("Ticket not found", 404)

    if ticket["status"] != STATUS_SUBMITTED:
        conn.close()
        return error_response("Only submitted tickets can be approved", 400)
    
    conn.execute("""
        UPDATE tickets
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_APPROVED,
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
        return error_response("manager_comment is required when rejecting a ticket", 400)

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if ticket["status"] != STATUS_SUBMITTED:
        conn.close()
        return error_response("Only submitted tickets can be rejected", 400)

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            manager_comment = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_REJECTED,
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
        "status": STATUS_REJECTED,
        "manager_comment": manager_comment
    }), 200


@app.route("/tickets/<int:ticket_id>/resubmit", methods=["PATCH"])
def resubmit_ticket(ticket_id):
    data = request.get_json()

    proof_path = data.get("proof_path")

    if not proof_path:
        return error_response("proof_path is required", 400)

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if ticket["status"] != STATUS_REJECTED:
        conn.close()
        return error_response("Only rejected tickets can be resubmitted", 400)

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            proof_path = ?,
            manager_comment = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_SUBMITTED,
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
        "status": STATUS_SUBMITTED
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


@app.route("/tickets/<int:ticket_id>/start", methods=["PATCH"])
def start_ticket(ticket_id):
    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return  error_response("Ticket not found", 404)

    if ticket["status"] not in [STATUS_PENDING, STATUS_ASSIGNED]:
        conn.close()
        return error_response("Only pending tickets can be started", 400)

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_IN_PROGRESS,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="started",
        actor="staff",
        details="Ticket started"
    )

    return jsonify({
        "message": "Ticket started successfully"
    }), 200

@app.route("/tickets/<int:ticket_id>/assign", methods=["PATCH"])
def assign_ticket(ticket_id):
    data = request.get_json()
    assigned_to = data.get("assigned_to")

    if not assigned_to:
        return error_response("assigned_to is required", 400)

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    conn.execute("""
        UPDATE tickets
        SET assigned_to = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (assigned_to, STATUS_ASSIGNED, ticket_id))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="assigned",
        actor="manager",
        details=f"Assigned to {assigned_to}"
    )

    return jsonify({
        "message": f"Ticket assigned to {assigned_to}"
    }), 200



if __name__ == "__main__":
    app.run(debug=True, port=5002, use_reloader=False)