# Dev 2 Assignment: Project Owner Invitation History

## Goal

Build one API endpoint that lets a Project Owner see every invitation sent for one of their projects.

This feature helps the owner dashboard show whether an invitation is `PENDING`, `ACCEPTED`, or `DECLINED`.

## Important project rule

One project can have only one active invitation at a time.

However, an owner may invite another student after a previous student declines. Therefore, this endpoint must return the full invitation history for the project.

## Endpoint to build

```text
GET /projects/{project_id}/invitations?owner_id={owner_user_id}
```

Example:

```text
GET /projects/PROJECT_UUID/invitations?owner_id=OWNER_USER_UUID
```

`owner_id` is a **User ID**, not a project ID and not a student profile ID.

## Expected successful response

Return a list of the existing `InvitationRead` response objects. Do not create a new response format.

```json
[
  {
    "id": "invitation-uuid",
    "project_id": "project-uuid",
    "student_id": "student-profile-uuid",
    "student_name": "မေသဇင်",
    "owner_name": "Tech Event Club",
    "project_title": "Tech Event Social Media Design",
    "required_skills": ["GRAPHIC_DESIGN", "CANVA"],
    "deadline": "2026-07-24",
    "work_type": "REMOTE",
    "budget_mmk": 60000,
    "project_status": "OPEN",
    "status": "DECLINED",
    "created_at": "2026-07-18T10:00:00Z",
    "responded_at": "2026-07-18T10:05:00Z"
  }
]
```

Return invitations in newest-first order.

## Backend logic

Follow this order in the route:

1. Find the project using `project_id`.
2. If the project does not exist, return `404 Not Found`.
3. Compare `owner_id` with `project.owner_id`.
4. If they are different, return `403 Forbidden`.
5. Query all `Invitation` rows where `invitation.project_id == project_id`.
6. Sort by `created_at` descending, so the newest invitation is first.
7. Return every invitation using the existing `InvitationRead` response format.

Do not change these existing rules:

- Do not create a new invitation in this endpoint.
- Do not accept or decline an invitation here.
- Do not allow another owner to read this project’s invitation history.
- Do not change the project status.

## Suggested files

| File | What to do |
|---|---|
| `app/routers/projects.py` | Add the new `GET /{project_id}/invitations` route. |
| `app/routers/invitations.py` | Reuse the existing `InvitationRead` response helper if needed. Avoid duplicating response fields. |
| `tests/test_invitations.py` | Add automated tests for this endpoint. |
| `docs/frontend-integration-guide.md` | Add this endpoint for the frontend developer. |

## Helpful existing code

Before coding, read these files:

```text
app/routers/invitations.py
app/routers/projects.py
app/schemas/invitation.py
app/models/invitation.py
```

Look for the existing `InvitationRead` schema and invitation response helper. Reusing existing code keeps the API consistent.

## Required tests

Add at least these tests:

1. The real project owner gets the invitation list successfully (`200`).
2. Another Project Owner gets `403`.
3. A missing project returns `404`.
4. The returned invitation status is correct, for example `PENDING` or `DECLINED`.
5. The list is newest-first when there is more than one invitation.

Run all tests before committing:

```bash
.venv/bin/python -m pytest -q
```

## Postman test

Method:

```text
GET
```

URL:

```text
http://127.0.0.1:8000/projects/PROJECT_UUID/invitations?owner_id=OWNER_USER_UUID
```

For the cloud test server, replace the base URL with the current deployed API address.

No request body is needed.

## Definition of done

The assignment is complete when:

- The endpoint returns the project invitation history for the correct owner.
- Another owner cannot access it.
- Tests pass.
- The frontend guide is updated.
- The change is committed on a separate Git branch.

## Git workflow

Start from the latest `main` branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c feat/project-invitation-history
```

After testing:

```bash
git add app/routers/projects.py app/routers/invitations.py tests/test_invitations.py docs/frontend-integration-guide.md
git commit -m "feat: add project invitation history for owners"
git push -u origin feat/project-invitation-history
```

Then create a pull request into `main` for review.
