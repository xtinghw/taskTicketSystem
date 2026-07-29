import os
import secrets

from flask import Flask, request, jsonify, render_template, session, url_for
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def is_debug_enabled():
    return os.environ.get("FLASK_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


# Demo user table
USERS = {
    "manager": {
        "password": "1234",
        "role": "manager",
        "display_name": "Manager"
    },
    "staffa": {
        "password": "1234",
        "role": "staff",
        "display_name": "Staff A"
    },
    "staffb": {
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
STATUS_CLOSED = "closed"
STATUS_VOIDED = "voided"


DEMO_TICKETS = [
    {
        "ticket_type": "pos_store_system",
        "category": "pos_store_system",
        "priority": "urgent",
        "title": "Front counter printer cannot print labels",
        "description": "Fake demo ticket: label printer stopped during a busy service period. Staff need escalation notes and a clear workaround.",
        "reported_by": "Staff A",
        "reported_to": "Manager",
        "assigned_to": "Staff B",
        "visibility": "public",
        "status": STATUS_SUBMITTED,
        "proof_type": "photo",
        "proof_path": "uploads/demo-printer-label-proof.jpg",
        "staff_note": "Checked paper path, restarted workstation, attached printer queue screenshot.",
        "manager_comment": None,
        "created_at": "2026-07-08 08:15:00",
        "updated_at": "2026-07-08 09:05:00"
    },
    {
        "ticket_type": "customer_complaint",
        "category": "customer_complaint",
        "priority": "urgent",
        "title": "Customer complaint about refund over AUD 100",
        "description": "Fake demo ticket: customer is requesting a refund above the staff approval threshold.",
        "reported_by": "Staff B",
        "reported_to": "Manager",
        "assigned_to": "Staff A",
        "visibility": "manager_only",
        "status": STATUS_REJECTED,
        "proof_type": "receipt",
        "proof_path": "uploads/demo-refund-receipt.pdf",
        "staff_note": "Customer asked for immediate decision. Receipt reference recorded for manager review.",
        "manager_comment": "Please add final resolution options before customer follow-up.",
        "created_at": "2026-07-08 08:35:00",
        "updated_at": "2026-07-08 09:20:00"
    },
    {
        "ticket_type": "repair",
        "category": "repair",
        "priority": "normal",
        "title": "Student iPad screen check",
        "description": "Fake demo ticket: iPad screen touch response is inconsistent after customer drop-off.",
        "reported_by": "Manager",
        "reported_to": None,
        "assigned_to": "Staff A",
        "visibility": "public",
        "status": STATUS_IN_PROGRESS,
        "proof_type": "note",
        "proof_path": None,
        "staff_note": "Initial diagnostics started. Waiting for second test after restart.",
        "manager_comment": None,
        "created_at": "2026-07-08 09:00:00",
        "updated_at": "2026-07-08 09:40:00"
    },
    {
        "ticket_type": "warranty_return",
        "category": "warranty_return",
        "priority": "high",
        "title": "Warranty return needs manager approval",
        "description": "Fake demo ticket: accessory return is inside warranty period but needs condition check.",
        "reported_by": "Staff A",
        "reported_to": "Manager",
        "assigned_to": "Staff B",
        "visibility": "public",
        "status": STATUS_APPROVED,
        "proof_type": "photo",
        "proof_path": "uploads/demo-warranty-condition.jpg",
        "staff_note": "Photos uploaded. Product condition is consistent with warranty claim.",
        "manager_comment": "Approved for warranty exchange after proof review.",
        "created_at": "2026-07-08 09:25:00",
        "updated_at": "2026-07-08 10:10:00"
    },
    {
        "ticket_type": "staff_report",
        "category": "staff_report",
        "priority": "high",
        "title": "Staff report: SOP discount question",
        "description": "Fake demo ticket: staff asked which discount rule applies when manager is unavailable.",
        "reported_by": "Staff B",
        "reported_to": "Manager",
        "assigned_to": "Staff A, Staff B",
        "visibility": "public",
        "status": STATUS_ASSIGNED,
        "proof_type": "note",
        "proof_path": None,
        "staff_note": None,
        "manager_comment": "Use SOP guidance first, then escalate if the customer asks for an exception.",
        "created_at": "2026-07-08 10:00:00",
        "updated_at": "2026-07-08 10:05:00"
    },
    {
        "ticket_type": "customer_feedback",
        "category": "customer_feedback",
        "priority": "low",
        "title": "Customer feedback about pickup communication",
        "description": "Fake demo ticket: customer suggested clearer repair pickup timing messages.",
        "reported_by": "Staff A",
        "reported_to": "Manager",
        "assigned_to": "Staff B",
        "visibility": "public",
        "status": STATUS_CLOSED,
        "proof_type": "note",
        "proof_path": "uploads/demo-feedback-note.txt",
        "staff_note": "Customer feedback recorded and template wording updated.",
        "manager_comment": "Closed after message template was updated.",
        "created_at": "2026-07-08 10:20:00",
        "updated_at": "2026-07-08 10:55:00"
    },
    {
        "ticket_type": "stock_inventory",
        "category": "stock_inventory",
        "priority": "normal",
        "title": "Stock count mismatch for charging cables",
        "description": "Fake demo ticket: inventory count does not match shelf quantity.",
        "reported_by": "Manager",
        "reported_to": None,
        "assigned_to": None,
        "visibility": "public",
        "status": STATUS_PENDING,
        "proof_type": "note",
        "proof_path": None,
        "staff_note": None,
        "manager_comment": None,
        "created_at": "2026-07-08 11:00:00",
        "updated_at": "2026-07-08 11:00:00"
    },
    {
        "ticket_type": "general_task",
        "category": "general_task",
        "priority": "low",
        "title": "Duplicate cleaning checklist task",
        "description": "Fake demo ticket: duplicate task was created during workflow review and should stay visible as voided history.",
        "reported_by": "Manager",
        "reported_to": None,
        "assigned_to": None,
        "visibility": "public",
        "status": STATUS_VOIDED,
        "proof_type": "note",
        "proof_path": None,
        "staff_note": None,
        "manager_comment": "Voided because the task was duplicated during demo setup.",
        "created_at": "2026-07-08 11:15:00",
        "updated_at": "2026-07-08 11:25:00"
    },
    {
        "ticket_type": "repair",
        "category": "repair",
        "priority": "high",
        "title": "Phone battery replacement quality check",
        "description": "Fake demo ticket: battery replacement needs final quality check before customer pickup.",
        "reported_by": "Manager",
        "reported_to": None,
        "assigned_to": "Staff A",
        "visibility": "public",
        "status": STATUS_SUBMITTED,
        "proof_type": "photo",
        "proof_path": "uploads/demo-battery-test.jpg",
        "staff_note": "Battery replaced, charging tested, final photo attached.",
        "manager_comment": None,
        "created_at": "2026-07-08 11:30:00",
        "updated_at": "2026-07-08 12:05:00"
    },
    {
        "ticket_type": "pos_store_system",
        "category": "pos_store_system",
        "priority": "urgent",
        "title": "EFTPOS terminal intermittent connection",
        "description": "Fake demo ticket: payment terminal intermittently disconnects and may affect customer checkout.",
        "reported_by": "Staff A",
        "reported_to": "Manager",
        "assigned_to": "Staff A, Staff B",
        "visibility": "public",
        "status": STATUS_IN_PROGRESS,
        "proof_type": "note",
        "proof_path": None,
        "staff_note": "Checked cable, restarted terminal, monitoring next transaction window.",
        "manager_comment": "Escalate to provider if the next disconnect happens.",
        "created_at": "2026-07-08 12:10:00",
        "updated_at": "2026-07-08 12:35:00"
    }
]


init_db()


def require_login():
    return "username" in session


def require_role(role):
    return session.get("role") == role


def current_user_role():
    return session.get("role")


def current_user_display_name():
    return session.get("display_name", "Unknown")


def split_assignees(assigned_to):
    if not assigned_to:
        return []

    return [
        name.strip()
        for name in assigned_to.split(",")
        if name.strip()
    ]


def normalize_assigned_to(assigned_to):
    if not assigned_to:
        return None

    names = split_assignees(assigned_to)

    unique_names = []

    for name in names:
        if name not in unique_names:
            unique_names.append(name)

    if not unique_names:
        return None

    return ", ".join(unique_names)


def next_status_after_assignment(current_status, assigned_to):
    if current_status == STATUS_PENDING:
        if assigned_to:
            return STATUS_ASSIGNED
        return STATUS_PENDING

    if current_status == STATUS_ASSIGNED:
        if assigned_to:
            return STATUS_ASSIGNED
        return STATUS_PENDING

    return current_status


def is_terminal_status(status):
    return status in [STATUS_CLOSED, STATUS_VOIDED]


def serialize_ticket(ticket):
    return {
        "id": ticket["id"],
        "ticket_type": ticket["ticket_type"],
        "category": ticket["category"],
        "priority": ticket["priority"],
        "title": ticket["title"],
        "description": ticket["description"],
        "reported_by": ticket["reported_by"],
        "reported_to": ticket["reported_to"],
        "assigned_to": ticket["assigned_to"],
        "visibility": ticket["visibility"],
        "status": ticket["status"],
        "proof_required": ticket["proof_required"],
        "proof_type": ticket["proof_type"],
        "proof_path": ticket["proof_path"],
        "staff_note": ticket["staff_note"],
        "manager_comment": ticket["manager_comment"],
        "is_demo": ticket["is_demo"],
        "created_at": ticket["created_at"],
        "updated_at": ticket["updated_at"]
    }


def error_response(message, status_code):
    return jsonify({
        "success": False,
        "error": message
    }), status_code


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
    dashboard_url = url_for("dashboard_page")

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Task Ticket System</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f4f6f8;
                color: #1f2937;
            }}

            main {{
                width: min(420px, 90vw);
                padding: 32px;
                border: 1px solid #d8dee4;
                border-radius: 8px;
                background: #ffffff;
                text-align: center;
            }}

            h1 {{
                margin: 0 0 12px;
                font-size: 28px;
            }}

            p {{
                margin: 0 0 24px;
                color: #4b5563;
            }}

            a {{
                display: inline-block;
                padding: 12px 18px;
                border-radius: 6px;
                background: #2563eb;
                color: #ffffff;
                text-decoration: none;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>Task Ticket System</h1>
            <p>The application is running.</p>
            <a href="{dashboard_url}">Open Dashboard</a>
        </main>
    </body>
    </html>
    """


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

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
    if not require_login():
        return error_response("Please login first to create a task or report an issue", 401)

    data = request.get_json() or {}

    ticket_type = data.get("ticket_type", "task")
    category = data.get("category", ticket_type or "general_task")
    priority = data.get("priority", "normal")
    title = data.get("title")
    description = data.get("description")
    reported_by = current_user_display_name()
    role = current_user_role()

    if role == "staff":
        reported_to = "Manager"
        assigned_to = None
    else:
        reported_to = None
        assigned_to = normalize_assigned_to(data.get("assigned_to"))

    visibility = data.get("visibility", "public")
    proof_required = data.get("proof_required", 1)
    proof_type = data.get("proof_type", "photo")

    if not title or not description:
        return error_response("Title and description are required", 400)

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO tickets (
            ticket_type,
            category,
            priority,
            title,
            description,
            reported_by,
            reported_to,
            assigned_to,
            visibility,
            proof_required,
            proof_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_type,
        category,
        priority,
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

    elif role == "staff":
        tickets = conn.execute("""
            SELECT *
            FROM tickets
            WHERE visibility = 'public'
               OR reported_by = ?
               OR assigned_to = ?
               OR assigned_to LIKE ?
            ORDER BY created_at DESC
        """, (
            display_name,
            display_name,
            f"%{display_name}%"
        )).fetchall()

    else:
        tickets = conn.execute("""
            SELECT *
            FROM tickets
            WHERE visibility = 'public'
            ORDER BY created_at DESC
        """).fetchall()

    conn.close()

    ticket_list = []

    for ticket in tickets:
        ticket_list.append(serialize_ticket(ticket))

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

    return jsonify(serialize_ticket(ticket)), 200


@app.route("/tickets/<int:ticket_id>", methods=["PATCH"])
def update_ticket(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can edit tickets", 403)

    data = request.get_json() or {}

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if is_terminal_status(ticket["status"]):
        conn.close()
        return error_response("Closed or voided tickets cannot be edited", 400)

    ticket_type = data.get("ticket_type", ticket["ticket_type"])
    category = data.get("category", ticket["category"])
    priority = data.get("priority", ticket["priority"])
    title = data.get("title", ticket["title"])
    description = data.get("description", ticket["description"])
    visibility = data.get("visibility", ticket["visibility"])
    proof_required = data.get("proof_required", ticket["proof_required"])
    proof_type = data.get("proof_type", ticket["proof_type"])

    if "assigned_to" in data:
        assigned_to = normalize_assigned_to(data.get("assigned_to"))
    else:
        assigned_to = ticket["assigned_to"]

    if not title or not description:
        conn.close()
        return error_response("Title and description are required", 400)

    new_status = next_status_after_assignment(
        current_status=ticket["status"],
        assigned_to=assigned_to
    )

    conn.execute("""
        UPDATE tickets
        SET ticket_type = ?,
            category = ?,
            priority = ?,
            title = ?,
            description = ?,
            assigned_to = ?,
            visibility = ?,
            proof_required = ?,
            proof_type = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        ticket_type,
        category,
        priority,
        title,
        description,
        assigned_to,
        visibility,
        proof_required,
        proof_type,
        new_status,
        ticket_id
    ))

    conn.commit()
    updated_ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="updated",
        actor=current_user_display_name(),
        details="Ticket details updated"
    )

    return jsonify({
        "message": "Ticket updated successfully",
        "ticket": serialize_ticket(updated_ticket)
    }), 200


@app.route("/tickets/<int:ticket_id>/assign", methods=["PATCH"])
def assign_ticket(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can assign tickets", 403)

    data = request.get_json() or {}

    assigned_to = normalize_assigned_to(data.get("assigned_to"))

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if ticket["status"] == STATUS_APPROVED:
        conn.close()
        return error_response("Approved tickets cannot be reassigned", 400)

    if is_terminal_status(ticket["status"]):
        conn.close()
        return error_response("Closed or voided tickets cannot be reassigned", 400)

    new_status = next_status_after_assignment(
        current_status=ticket["status"],
        assigned_to=assigned_to
    )

    conn.execute("""
        UPDATE tickets
        SET assigned_to = ?,
            status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        assigned_to,
        new_status,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="assigned",
        actor=current_user_display_name(),
        details=f"Assignment updated to {assigned_to or 'Unassigned'}"
    )

    return jsonify({
        "message": f"Assignment updated to {assigned_to or 'Unassigned'}",
        "assigned_to": assigned_to,
        "status": new_status
    }), 200


@app.route("/tickets/<int:ticket_id>/start", methods=["PATCH"])
def start_ticket(ticket_id):
    if current_user_role() != "staff":
        return error_response("Only staff can start assigned tickets", 403)

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if ticket["status"] not in [STATUS_PENDING, STATUS_ASSIGNED]:
        conn.close()
        return error_response("Only pending or assigned tickets can be started", 400)

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
        actor=current_user_display_name(),
        details="Ticket started"
    )

    return jsonify({
        "message": "Ticket started successfully"
    }), 200


@app.route("/tickets/<int:ticket_id>/submit", methods=["PATCH"])
def submit_ticket(ticket_id):
    if current_user_role() != "staff":
        return error_response("Only staff can submit ticket proof", 403)

    data = request.get_json() or {}
    proof_type = data.get("proof_type") or "photo"
    proof_path = data.get("proof_path")
    staff_note = data.get("staff_note")

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

    if ticket["status"] not in [STATUS_PENDING, STATUS_IN_PROGRESS]:
        conn.close()
        return error_response("Only pending or in progress tickets can be submitted", 400)

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            proof_type = ?,
            proof_path = ?,
            staff_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_SUBMITTED,
        proof_type,
        proof_path,
        staff_note,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="submitted",
        actor=current_user_display_name(),
        details=f"Proof submitted ({proof_type}): {proof_path}"
    )

    return jsonify({
        "message": "Ticket submitted successfully",
        "ticket_id": ticket_id,
        "status": STATUS_SUBMITTED,
        "proof_type": proof_type,
        "proof_path": proof_path,
        "staff_note": staff_note
    }), 200


@app.route("/tickets/<int:ticket_id>/approve", methods=["PATCH"])
def approve_ticket(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can approve tickets", 403)

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
        actor=current_user_display_name(),
        details="Ticket approved by manager"
    )

    return jsonify({
        "message": "Ticket approved successfully",
        "ticket_id": ticket_id,
        "status": STATUS_APPROVED
    }), 200


@app.route("/tickets/<int:ticket_id>/close", methods=["PATCH"])
def close_ticket(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can close tickets", 403)

    data = request.get_json() or {}
    manager_comment = data.get("manager_comment")

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if ticket["status"] != STATUS_APPROVED:
        conn.close()
        return error_response("Only approved tickets can be closed", 400)

    final_comment = manager_comment or ticket["manager_comment"]

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            manager_comment = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_CLOSED,
        final_comment,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="closed",
        actor=current_user_display_name(),
        details=final_comment or "Ticket closed by manager"
    )

    return jsonify({
        "message": "Ticket closed successfully",
        "ticket_id": ticket_id,
        "status": STATUS_CLOSED,
        "manager_comment": final_comment
    }), 200


@app.route("/tickets/<int:ticket_id>/manager-note", methods=["PATCH"])
def save_manager_note(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can update manager notes", 403)

    data = request.get_json() or {}
    manager_comment = data.get("manager_comment")

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
        SET manager_comment = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        manager_comment,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="manager_note_updated",
        actor=current_user_display_name(),
        details=manager_comment or "Manager note cleared"
    )

    return jsonify({
        "message": "Manager note saved successfully",
        "ticket_id": ticket_id,
        "manager_comment": manager_comment
    }), 200


@app.route("/tickets/<int:ticket_id>/void", methods=["PATCH"])
def void_ticket(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can void tickets", 403)

    data = request.get_json() or {}
    manager_comment = data.get("manager_comment")

    if not manager_comment:
        return error_response("manager_comment is required when voiding a ticket", 400)

    conn = get_db_connection()

    ticket = conn.execute("""
        SELECT *
        FROM tickets
        WHERE id = ?
    """, (ticket_id,)).fetchone()

    if ticket is None:
        conn.close()
        return error_response("Ticket not found", 404)

    if is_terminal_status(ticket["status"]):
        conn.close()
        return error_response("Closed or voided tickets cannot be voided again", 400)

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            manager_comment = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_VOIDED,
        manager_comment,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="voided",
        actor=current_user_display_name(),
        details=manager_comment
    )

    return jsonify({
        "message": "Ticket voided successfully",
        "ticket_id": ticket_id,
        "status": STATUS_VOIDED,
        "manager_comment": manager_comment
    }), 200


@app.route("/tickets/<int:ticket_id>/reject", methods=["PATCH"])
def reject_ticket(ticket_id):
    if current_user_role() != "manager":
        return error_response("Only manager can return tickets for follow-up", 403)

    data = request.get_json() or {}
    manager_comment = data.get("manager_comment")

    if not manager_comment:
        return error_response("manager_comment is required when returning a ticket for follow-up", 400)

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
        return error_response("Only submitted tickets can be returned for follow-up", 400)

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
        actor=current_user_display_name(),
        details=manager_comment
    )

    return jsonify({
        "message": "Ticket returned for follow-up successfully",
        "ticket_id": ticket_id,
        "status": STATUS_REJECTED,
        "manager_comment": manager_comment
    }), 200


@app.route("/tickets/<int:ticket_id>/resubmit", methods=["PATCH"])
def resubmit_ticket(ticket_id):
    if current_user_role() != "staff":
        return error_response("Only staff can resubmit tickets", 403)

    data = request.get_json() or {}
    proof_type = data.get("proof_type") or "photo"
    proof_path = data.get("proof_path")
    staff_note = data.get("staff_note")

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
        return error_response("Only tickets returned for follow-up can be resubmitted", 400)

    conn.execute("""
        UPDATE tickets
        SET status = ?,
            proof_type = ?,
            proof_path = ?,
            staff_note = ?,
            manager_comment = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        STATUS_SUBMITTED,
        proof_type,
        proof_path,
        staff_note,
        ticket_id
    ))

    conn.commit()
    conn.close()

    add_audit_log(
        ticket_id=ticket_id,
        action="resubmitted",
        actor=current_user_display_name(),
        details=f"Follow-up proof submitted ({proof_type}): {proof_path}"
    )

    return jsonify({
        "message": "Ticket resubmitted successfully",
        "ticket_id": ticket_id,
        "status": STATUS_SUBMITTED,
        "proof_type": proof_type,
        "proof_path": proof_path,
        "staff_note": staff_note
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


def delete_demo_tickets(conn):
    demo_ticket_rows = conn.execute("""
        SELECT id
        FROM tickets
        WHERE is_demo = 1
    """).fetchall()

    demo_ticket_ids = [
        row["id"]
        for row in demo_ticket_rows
    ]

    if not demo_ticket_ids:
        return 0

    placeholders = ",".join("?" for _ in demo_ticket_ids)

    conn.execute(
        f"DELETE FROM audit_logs WHERE ticket_id IN ({placeholders})",
        demo_ticket_ids
    )
    conn.execute(
        f"DELETE FROM tickets WHERE id IN ({placeholders})",
        demo_ticket_ids
    )

    return len(demo_ticket_ids)


def demo_status_action(ticket):
    status = ticket["status"]

    if status == STATUS_PENDING:
        return None

    if status == STATUS_ASSIGNED:
        return "assigned"

    if status == STATUS_IN_PROGRESS:
        return "started"

    if status == STATUS_SUBMITTED:
        return "submitted"

    if status == STATUS_APPROVED:
        return "approved"

    if status == STATUS_REJECTED:
        return "rejected"

    if status == STATUS_CLOSED:
        return "closed"

    if status == STATUS_VOIDED:
        return "voided"

    return status


@app.route("/demo-data/import", methods=["POST"])
def import_demo_data():
    if current_user_role() != "manager":
        return error_response("Only manager can import demo data", 403)

    conn = get_db_connection()
    deleted_count = delete_demo_tickets(conn)
    created_ticket_ids = []

    for ticket in DEMO_TICKETS:
        cursor = conn.execute("""
            INSERT INTO tickets (
                ticket_type,
                category,
                priority,
                title,
                description,
                reported_by,
                reported_to,
                assigned_to,
                visibility,
                status,
                proof_required,
                proof_type,
                proof_path,
                staff_note,
                manager_comment,
                is_demo,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket["ticket_type"],
            ticket["category"],
            ticket["priority"],
            ticket["title"],
            ticket["description"],
            ticket["reported_by"],
            ticket["reported_to"],
            ticket["assigned_to"],
            ticket["visibility"],
            ticket["status"],
            1,
            ticket["proof_type"],
            ticket["proof_path"],
            ticket["staff_note"],
            ticket["manager_comment"],
            1,
            ticket["created_at"],
            ticket["updated_at"]
        ))

        ticket_id = cursor.lastrowid
        created_ticket_ids.append(ticket_id)

        conn.execute("""
            INSERT INTO audit_logs (
                ticket_id,
                action,
                actor,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            ticket_id,
            "created",
            ticket["reported_by"],
            f"Demo ticket created ({ticket['category']} / {ticket['priority']})",
            ticket["created_at"]
        ))

        status_action = demo_status_action(ticket)

        if status_action is not None:
            conn.execute("""
                INSERT INTO audit_logs (
                    ticket_id,
                    action,
                    actor,
                    details,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                ticket_id,
                status_action,
                ticket["assigned_to"] or ticket["reported_by"],
                f"Demo workflow state set to {ticket['status']}",
                ticket["updated_at"]
            ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Demo data imported successfully",
        "created_count": len(created_ticket_ids),
        "deleted_count": deleted_count,
        "ticket_ids": created_ticket_ids
    }), 201


@app.route("/demo-data", methods=["DELETE"])
def clear_demo_data():
    if current_user_role() != "manager":
        return error_response("Only manager can clear demo data", 403)

    conn = get_db_connection()
    deleted_count = delete_demo_tickets(conn)
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Demo data cleared successfully",
        "deleted_count": deleted_count
    }), 200


@app.route("/staff/<staff_name>/followups", methods=["GET"])
def get_staff_followups(staff_name):
    if current_user_role() != "manager":
        return error_response("Only manager can view staff follow-up details", 403)

    conn = get_db_connection()

    rejected_tickets = conn.execute("""
        SELECT *
        FROM tickets
        WHERE assigned_to = ?
        AND status = ?
        ORDER BY updated_at DESC
    """, (
        staff_name,
        STATUS_REJECTED
    )).fetchall()

    followup_count = len(rejected_tickets)

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
        "followup_count": followup_count,
        "rejected_tickets": ticket_list
    }), 200


@app.route("/staff/<staff_name>/followup-history", methods=["GET"])
def get_staff_followup_history(staff_name):
    if current_user_role() != "manager":
        return error_response("Only manager can view staff follow-up history", 403)

    conn = get_db_connection()

    followup_logs = conn.execute("""
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
        AND audit_logs.action = ?
        ORDER BY audit_logs.created_at DESC
    """, (
        staff_name,
        "rejected"
    )).fetchall()

    followup_history = []

    for log in followup_logs:
        followup_history.append({
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
        "followup_count": len(followup_history),
        "followup_history": followup_history
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

    status_summary = {
        "pending": 0,
        "assigned": 0,
        "in_progress": 0,
        "submitted": 0,
        "approved": 0,
        "rejected": 0,
        "closed": 0,
        "voided": 0
    }

    for row in status_counts:
        status_summary[row["status"]] = row["count"]

    staff_followup_list = []

    if current_user_role() == "manager":
        staff_followups = conn.execute("""
            SELECT 
                tickets.assigned_to,
                COUNT(audit_logs.id) AS followup_count
            FROM tickets
            LEFT JOIN audit_logs 
                ON tickets.id = audit_logs.ticket_id
                AND audit_logs.action = ?
            WHERE tickets.assigned_to IS NOT NULL
            GROUP BY tickets.assigned_to
            ORDER BY followup_count DESC
        """, (
            "rejected",
        )).fetchall()

        for row in staff_followups:
            staff_followup_list.append({
                "staff_name": row["assigned_to"],
                "followup_count": row["followup_count"]
            })

    conn.close()

    return jsonify({
        "total_tickets": total_tickets,
        "status_summary": status_summary,
        "staff_followups": staff_followup_list
    }), 200


if __name__ == "__main__":
    app.run(debug=is_debug_enabled(), port=5002, use_reloader=False)
