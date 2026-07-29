# RetailOps Memory Loop

**Current working module: Task Ticket Dashboard**

Frontline support cases, repair follow-ups, handover details, SOP guidance, and practical know-how are often scattered across separate notes and people's memory. When that context is lost, repeated issues take longer to understand and process improvements are harder to carry forward.

RetailOps Memory Loop is a working Flask and SQLite retail support and repair workflow prototype that turns those activities into structured, reviewable records. The current module supports ticket intake, assignment, status tracking, staff evidence, manager review, follow-up, and audit history.

The longer-term direction is planned, human-reviewed AI assistance for recurring issue analysis, operational guidance, and SOP or training improvement. That AI capability is **not implemented in the current build**.

This is an ICT support portfolio prototype, not a production ITSM system. All screenshots and records use fake demo data.

<img src="assets/staff-dashboard-summary.png" alt="Task Ticket Dashboard showing fake demo ticket counts, workflow status and login access" width="900">

---

## Why This Project Exists

Resolving an individual issue is only part of reliable support. A useful operational workflow also needs enough context for another person to understand:

* what was reported
* who owns the next action
* what work has been completed
* what evidence or notes were provided
* what a manager approved, rejected, or returned
* what the team may need to improve later

The current dashboard creates that shared record before any future AI assistance is considered.

---

## Built Now

Everything in this section is implemented in the current repository and visible in the code, tests, or screenshots.

### Ticket Intake and Tracking

* Create support requests and operational tasks with type, title, description, priority, visibility, assignment, and proof requirements
* Track pending, assigned, in-progress, submitted, approved, rejected, closed, and voided states
* Search, filter, and sort the operational ticket list
* Use fake demo tickets for safe local demonstration

### Staff Workflow

* Sign in with a staff demo account and view assigned work
* Start work and submit notes or proof references
* See rejected work that requires follow-up
* Correct and resubmit work after manager feedback

### Manager Workflow

* Create, assign, and edit tickets
* Review submitted work and staff notes
* Approve, reject, close, or void tickets
* Add manager notes and return work with a correction reason
* Review staff follow-up counts

### Shared Operational Record

* Show dashboard totals and status summaries
* Keep an activity history of ticket actions
* Preserve handover context across staff and manager steps
* Make follow-up and review needs visible

---

## Current Support Workflow

1. A support request or operational task is recorded.
2. Its type, priority, visibility, proof requirement, and owner are captured.
3. Staff starts the assigned work and submits notes or evidence.
4. A manager reviews the submission.
5. The manager approves it, returns it for correction, closes it, or voids it.
6. Returned work can be corrected and resubmitted.
7. The activity history preserves the handover and decision trail.

---

## Product Screenshots

The dashboard shown above is the main visual overview. The seven additional screenshots below show the rest of the implemented workflow. All records are fake.

<details>
<summary>View seven more workflow screenshots</summary>

### Ticket Search and Filtering

Tickets can be searched, filtered, sorted, and reviewed from one operational list.

<img src="assets/ticket-search-and-filters.png" alt="Ticket list with search, filters, priority sorting and assigned staff information" width="900">

### Staff Issue Reporting

Staff can report an issue with type, title, description, visibility, and proof type.

<img src="assets/staff-report-issue-form.png" alt="Staff report issue form with proof type options" width="900">

### Manager Task Creation

Managers can create tasks, assign staff, set visibility, and choose proof requirements.

<img src="assets/manager-create-and-assign-task.png" alt="Manager create and assign task form" width="900">

### Manager Review Actions

Managers can open ticket actions for assignment, editing, proof review, follow-up, closure, or voiding.

<img src="assets/manager-ticket-actions.png" alt="Manager ticket actions menu with review and follow-up options" width="900">

### Ticket Details

The detail view shows the issue description, assignment, reporter, visibility, proof reference, notes, and timestamps.

<img src="assets/ticket-details-overview.png" alt="Ticket details modal showing description, assignment, proof and staff notes" width="900">

### Activity History

Each ticket keeps an activity record for later handover, follow-up, and review.

<img src="assets/ticket-activity-history.png" alt="Ticket activity history showing created, assigned, started, submitted and manager note events" width="900">

### Staff Follow-up Review

The manager follow-up view highlights returned work that may require correction, resubmission, or coaching.

<img src="assets/manager-staff-follow-up.png" alt="Manager staff follow-up details showing rejected or follow-up ticket counts by staff member" width="900">

</details>

---

## Future AI Direction - Not Yet Implemented

The existing structured workflow is designed as the foundation for possible human-reviewed AI assistance. A future version could help:

* organise unstructured support and repair notes into a manager-reviewable draft
* flag missing context before a handover or management review
* surface recurring issue patterns and workflow gaps from recorded cases
* assist with draft operational guidance
* assist managers in preparing SOP or training drafts for review

AI would remain a process assistant, not the decision-maker. It must not automatically:

* decide refunds or warranty outcomes
* approve policy exceptions
* make customer commitments
* publish or change an SOP

Human review and approval would remain required. Concepts previously explored under names such as Quote Desk, Store Pulse Board, or Repair Warranty Learning Loop are future product exploration only; they are not locked modules and are not built features.

---

## Example Use Case

A staff member receives a device check, repair follow-up, customer issue, or store technology task. They record the work and supporting notes. A manager reviews the submission and either approves it or returns it with clear feedback. If returned, the staff member corrects the issue and resubmits it.

The resulting record supports current handover and accountability. In the future, approved records could also give human reviewers better material for recurring issue analysis, operational guidance, and training improvement.

---

## Technology

* Python
* Flask
* SQLite
* HTML templates
* Vanilla JavaScript

---

## Run Locally

Install the application dependency and start the dashboard:

```bash
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5002/
```

Debug mode is off by default. To enable it explicitly for local troubleshooting:

```bash
FLASK_DEBUG=1 python app.py
```

### Run the Tests

If pytest is not already available in your environment:

```bash
pip install pytest
```

Run the full test suite:

```bash
python -m pytest -q
```

---

## Demo Login

| Role    | Username | Password |
| ------- | -------- | -------- |
| Manager | manager  | 1234     |
| Staff   | staffa   | 1234     |
| Staff   | staffb   | 1234     |

These credentials are for local fake demo data only.

---

## Privacy and Safety Boundary

This project must not include:

* real customer, staff, or business names
* real workplace images or SOP documents
* real payment, warranty, refund, or repair records
* real phone numbers, emails, addresses, serial numbers, IMEI numbers, or internal records

---

## What This Demonstrates

* practical ICT and retail technology support workflow thinking
* structured intake, ownership, status, and follow-up
* staff-to-manager handover and review
* service notes, evidence, correction, and resubmission
* audit history and operational visibility
* privacy-aware documentation with fake demo data
* a human-approval boundary for future AI-assisted process improvement

---

## Current Status

The Task Ticket Dashboard is working locally and covered by automated workflow tests. Near-term improvements can continue to strengthen status transitions, manager assignment and edit flows, guided fake-data demonstrations, and safe operational guidance examples.
