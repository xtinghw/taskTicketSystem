import pytest
import importlib

from app import app
from database import get_db_connection


@pytest.fixture
def client():
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def created_ticket_ids():
    ticket_ids = []

    yield ticket_ids

    conn = get_db_connection()

    for ticket_id in ticket_ids:
        conn.execute(
            "DELETE FROM audit_logs WHERE ticket_id = ?",
            (ticket_id,)
        )
        conn.execute(
            "DELETE FROM tickets WHERE id = ?",
            (ticket_id,)
        )

    conn.commit()
    conn.close()


def login(client, username, password="1234"):
    return client.post(
        "/login",
        json={
            "username": username,
            "password": password
        }
    )


def logout(client):
    return client.post("/logout")


def create_manager_task(client, assigned_to="Staff A"):
    response = client.post(
        "/tickets",
        json={
            "ticket_type": "repair",
            "title": "Test repair task",
            "description": "Test task created by automated test",
            "assigned_to": assigned_to,
            "visibility": "public",
            "proof_required": 1,
            "proof_type": "photo"
        }
    )

    return response


def get_ticket(client, ticket_id):
    return client.get(f"/tickets/{ticket_id}").get_json()


def get_staff_followup_count(summary_data, staff_name):
    for item in summary_data.get("staff_followups", []):
        if item.get("staff_name") == staff_name:
            return item.get("followup_count", 0)

    return 0


def test_logged_out_user_can_view_summary_but_not_staff_followups(client):
    response = client.get("/dashboard/summary")

    assert response.status_code == 200

    data = response.get_json()

    assert "total_tickets" in data
    assert "status_summary" in data
    assert data["staff_followups"] == []


def test_dashboard_includes_tiki_demo_cases(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Ticket Demo" in response.data
    assert b"Student iPad login issue" in response.data
    assert b"Classroom MacBook storage support" in response.data
    assert b"Accessory barcode scanner mismatch" in response.data
    assert b"Phone battery replacement quality check" in response.data
    assert b"EFTPOS terminal intermittent connection" in response.data


def test_dashboard_includes_screenshot_ready_ticket_controls(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Manager Controls" not in response.data
    assert b"You can assign, approve, and reject tickets." in response.data
    assert b"Import Demo Data" in response.data
    assert b"Clear Demo Data" in response.data
    assert b'id="ticketList"' in response.data
    assert b'id="ticketSearchInput"' in response.data
    assert b'id="categoryFilterInput"' in response.data
    assert b'id="priorityFilterInput"' in response.data
    assert b'id="ticketSortInput"' in response.data
    assert b"Priority" in response.data
    assert b"Newest" in response.data
    assert b"Edit Filter" in response.data
    assert b"Edit Filter: Show" in response.data
    assert b'id="ticketFilterPanel"' in response.data
    assert b"Clear Filter" in response.data


def test_app_secret_key_can_be_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-from-env")

    import app as app_module

    reloaded_app = importlib.reload(app_module).app

    assert reloaded_app.secret_key == "test-secret-from-env"


def test_manager_can_import_and_clear_demo_tickets(client):
    login(client, "manager")

    clear_before_response = client.delete("/demo-data")
    assert clear_before_response.status_code == 200

    import_response = client.post("/demo-data/import")
    assert import_response.status_code == 201

    import_data = import_response.get_json()
    assert import_data["created_count"] == 10

    tickets_response = client.get("/tickets")
    tickets = tickets_response.get_json()
    demo_tickets = [
        ticket
        for ticket in tickets
        if ticket.get("is_demo") == 1
    ]

    assert len(demo_tickets) == 10
    assert {ticket["priority"] for ticket in demo_tickets} >= {"urgent", "high", "normal", "low"}
    assert len({ticket["category"] for ticket in demo_tickets}) >= 8
    assert {
        "pending",
        "assigned",
        "in_progress",
        "submitted",
        "approved",
        "rejected",
        "closed",
        "voided"
    }.issubset({ticket["status"] for ticket in demo_tickets})

    clear_response = client.delete("/demo-data")

    assert clear_response.status_code == 200

    clear_data = clear_response.get_json()
    assert clear_data["deleted_count"] == 10

    tickets_after_clear = client.get("/tickets").get_json()
    assert all(ticket.get("is_demo") == 0 for ticket in tickets_after_clear)


def test_logged_out_user_cannot_create_ticket(client):
    response = client.post(
        "/tickets",
        json={
            "ticket_type": "repair",
            "title": "Should not create",
            "description": "Logged out user should not create ticket"
        }
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False
    assert "login" in data["error"].lower()


def test_manager_can_login_and_create_task(client, created_ticket_ids):
    login_response = login(client, "manager")

    assert login_response.status_code == 200

    create_response = create_manager_task(client, assigned_to="Staff A")

    assert create_response.status_code == 201

    created_data = create_response.get_json()
    ticket_id = created_data["ticket_id"]
    created_ticket_ids.append(ticket_id)

    ticket_response = client.get(f"/tickets/{ticket_id}")

    assert ticket_response.status_code == 200

    ticket_data = ticket_response.get_json()

    assert ticket_data["title"] == "Test repair task"
    assert ticket_data["assigned_to"] == "Staff A"


def test_staff_can_login_and_report_issue(client, created_ticket_ids):
    login_response = login(client, "staffa")

    assert login_response.status_code == 200

    create_response = client.post(
        "/tickets",
        json={
            "ticket_type": "issue",
            "title": "Test issue report",
            "description": "Test issue reported by staff",
            "visibility": "public",
            "proof_required": 1,
            "proof_type": "note"
        }
    )

    assert create_response.status_code == 201

    created_data = create_response.get_json()
    ticket_id = created_data["ticket_id"]
    created_ticket_ids.append(ticket_id)

    ticket_response = client.get(f"/tickets/{ticket_id}")

    assert ticket_response.status_code == 200

    ticket_data = ticket_response.get_json()

    assert ticket_data["reported_by"] == "Staff A"
    assert ticket_data["reported_to"] == "Manager"
    assert ticket_data["assigned_to"] is None


def test_staff_followup_api_is_manager_only(client):
    logged_out_response = client.get("/staff/Staff A/followups")

    assert logged_out_response.status_code == 403

    login(client, "staffa")

    staff_response = client.get("/staff/Staff A/followups")

    assert staff_response.status_code == 403


def test_manager_followup_count_updates_after_returning_ticket(client, created_ticket_ids):
    login(client, "manager")

    before_response = client.get("/dashboard/summary")
    before_data = before_response.get_json()
    before_count = get_staff_followup_count(before_data, "Staff A")

    create_response = create_manager_task(client, assigned_to="Staff A")

    assert create_response.status_code == 201

    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")

    start_response = client.patch(f"/tickets/{ticket_id}/start")

    assert start_response.status_code == 200

    submit_response = client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_path": "uploads/test-proof.jpg"
        }
    )

    assert submit_response.status_code == 200

    logout(client)
    login(client, "manager")

    reject_response = client.patch(
        f"/tickets/{ticket_id}/reject",
        json={
            "manager_comment": "Proof needs clearer photo"
        }
    )

    assert reject_response.status_code == 200

    after_response = client.get("/dashboard/summary")
    after_data = after_response.get_json()
    after_count = get_staff_followup_count(after_data, "Staff A")

    assert after_count == before_count + 1

    followup_response = client.get("/staff/Staff A/followups")

    assert followup_response.status_code == 200

    followup_data = followup_response.get_json()

    assert followup_data["staff_name"] == "Staff A"
    assert followup_data["followup_count"] >= 1


def test_manager_can_assign_ticket_to_staff_a(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to=None)
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    assign_response = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={
            "assigned_to": "Staff A"
        }
    )

    assert assign_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["assigned_to"] == "Staff A"
    assert ticket_data["status"] == "assigned"


def test_manager_can_reassign_ticket_from_staff_a_to_staff_b(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    assign_response = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={
            "assigned_to": "Staff B"
        }
    )

    assert assign_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["assigned_to"] == "Staff B"
    assert ticket_data["status"] == "assigned"


def test_manager_can_assign_ticket_to_multiple_staff(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to=None)
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    assign_response = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={
            "assigned_to": " Staff A, Staff B, Staff A "
        }
    )

    assert assign_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["assigned_to"] == "Staff A, Staff B"


def test_assign_edit_does_not_change_submitted_ticket_back_to_assigned(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")
    client.patch(f"/tickets/{ticket_id}/start")
    client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_path": "uploads/original-proof.jpg"
        }
    )

    logout(client)
    login(client, "manager")

    assign_response = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={
            "assigned_to": "Staff B"
        }
    )

    assert assign_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["assigned_to"] == "Staff B"
    assert ticket_data["status"] == "submitted"


def test_approved_ticket_cannot_be_reassigned(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")
    client.patch(f"/tickets/{ticket_id}/start")
    client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_path": "uploads/approved-proof.jpg"
        }
    )

    logout(client)
    login(client, "manager")
    approve_response = client.patch(f"/tickets/{ticket_id}/approve")

    assert approve_response.status_code == 200

    assign_response = client.patch(
        f"/tickets/{ticket_id}/assign",
        json={
            "assigned_to": "Staff B"
        }
    )

    assert assign_response.status_code == 400

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["assigned_to"] == "Staff A"
    assert ticket_data["status"] == "approved"


def test_manager_can_edit_ticket_details(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    edit_response = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "ticket_type": "apple_device_support",
            "title": "Student iPad login issue",
            "description": "Fake school support ticket for an iPad login issue.",
            "visibility": "manager_only",
            "proof_required": 1,
            "proof_type": "note",
            "assigned_to": "Staff B"
        }
    )

    assert edit_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["ticket_type"] == "apple_device_support"
    assert ticket_data["title"] == "Student iPad login issue"
    assert ticket_data["description"] == "Fake school support ticket for an iPad login issue."
    assert ticket_data["visibility"] == "manager_only"
    assert ticket_data["proof_type"] == "note"
    assert ticket_data["assigned_to"] == "Staff B"
    assert ticket_data["status"] == "assigned"


def test_staff_cannot_edit_or_close_ticket(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")

    edit_response = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "title": "Staff should not edit this"
        }
    )
    close_response = client.patch(f"/tickets/{ticket_id}/close")

    assert edit_response.status_code == 403
    assert close_response.status_code == 403


def test_manager_can_close_approved_ticket(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")
    client.patch(f"/tickets/{ticket_id}/start")
    client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_type": "note",
            "proof_path": "uploads/apple-support-note.txt",
            "staff_note": "Fake Apple support workflow note recorded."
        }
    )

    logout(client)
    login(client, "manager")
    approve_response = client.patch(f"/tickets/{ticket_id}/approve")

    assert approve_response.status_code == 200

    close_response = client.patch(
        f"/tickets/{ticket_id}/close",
        json={
            "manager_comment": "Closed after fake support workflow review."
        }
    )

    assert close_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["status"] == "closed"
    assert ticket_data["manager_comment"] == "Closed after fake support workflow review."


def test_manager_can_save_manager_note(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    note_response = client.patch(
        f"/tickets/{ticket_id}/manager-note",
        json={
            "manager_comment": "Fake manager note for follow-up planning."
        }
    )

    assert note_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["manager_comment"] == "Fake manager note for follow-up planning."


def test_manager_can_void_ticket_with_note(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    void_response = client.patch(
        f"/tickets/{ticket_id}/void",
        json={
            "manager_comment": "Fake duplicate ticket created during workflow testing."
        }
    )

    assert void_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["status"] == "voided"
    assert ticket_data["manager_comment"] == "Fake duplicate ticket created during workflow testing."


def test_staff_cannot_save_manager_note_or_void_ticket(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")

    note_response = client.patch(
        f"/tickets/{ticket_id}/manager-note",
        json={
            "manager_comment": "Staff should not write manager notes."
        }
    )
    void_response = client.patch(
        f"/tickets/{ticket_id}/void",
        json={
            "manager_comment": "Staff should not void tickets."
        }
    )

    assert note_response.status_code == 403
    assert void_response.status_code == 403


def test_staff_can_start_ticket(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")

    start_response = client.patch(f"/tickets/{ticket_id}/start")

    assert start_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["status"] == "in_progress"


def test_staff_can_submit_proof_after_starting_ticket(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")
    client.patch(f"/tickets/{ticket_id}/start")

    submit_response = client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_type": "note",
            "proof_path": "uploads/started-proof.txt",
            "staff_note": "Confirmed the repair and tested the device."
        }
    )

    assert submit_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["status"] == "submitted"
    assert ticket_data["proof_path"] == "uploads/started-proof.txt"
    assert ticket_data["proof_type"] == "note"
    assert ticket_data["staff_note"] == "Confirmed the repair and tested the device."


def test_staff_cannot_submit_proof_without_proof_path(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")
    client.patch(f"/tickets/{ticket_id}/start")

    submit_response = client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_type": "photo",
            "staff_note": "Missing proof path."
        }
    )

    assert submit_response.status_code == 400


def test_staff_can_resubmit_proof_after_ticket_is_returned_for_followup(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)
    login(client, "staffa")
    client.patch(f"/tickets/{ticket_id}/start")
    client.patch(
        f"/tickets/{ticket_id}/submit",
        json={
            "proof_path": "uploads/unclear-proof.jpg"
        }
    )

    logout(client)
    login(client, "manager")
    reject_response = client.patch(
        f"/tickets/{ticket_id}/reject",
        json={
            "manager_comment": "Please upload a clearer photo."
        }
    )

    assert reject_response.status_code == 200

    logout(client)
    login(client, "staffa")

    resubmit_response = client.patch(
        f"/tickets/{ticket_id}/resubmit",
        json={
            "proof_type": "photo",
            "proof_path": "uploads/corrected-proof.jpg",
            "staff_note": "Uploaded clearer follow-up proof."
        }
    )

    assert resubmit_response.status_code == 200

    ticket_data = get_ticket(client, ticket_id)

    assert ticket_data["status"] == "submitted"
    assert ticket_data["proof_type"] == "photo"
    assert ticket_data["proof_path"] == "uploads/corrected-proof.jpg"
    assert ticket_data["staff_note"] == "Uploaded clearer follow-up proof."
    assert ticket_data["manager_comment"] is None


def test_logged_out_users_cannot_perform_ticket_actions(client, created_ticket_ids):
    login(client, "manager")

    create_response = create_manager_task(client, assigned_to="Staff A")
    ticket_id = create_response.get_json()["ticket_id"]
    created_ticket_ids.append(ticket_id)

    logout(client)

    action_responses = [
        client.patch(
            f"/tickets/{ticket_id}/assign",
            json={
                "assigned_to": "Staff B"
            }
        ),
        client.patch(f"/tickets/{ticket_id}/start"),
        client.patch(
            f"/tickets/{ticket_id}/submit",
            json={
                "proof_path": "uploads/proof.jpg"
            }
        ),
        client.patch(f"/tickets/{ticket_id}/approve"),
        client.patch(
            f"/tickets/{ticket_id}/reject",
            json={
                "manager_comment": "Return reason"
            }
        ),
        client.patch(
            f"/tickets/{ticket_id}/resubmit",
            json={
                "proof_path": "uploads/proof.jpg"
            }
        )
    ]

    assert all(response.status_code == 403 for response in action_responses)
