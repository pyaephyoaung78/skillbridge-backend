# Postman: Test Invitation APIs

## Before testing

Create these values first:

| Value | How to create it | Postman variable |
|---|---|---|
| Project Owner | `POST /users` with `PROJECT_OWNER` | `owner_id` |
| Open project | `POST /projects` | `project_id` |
| Eligible student profile | `POST /students` | `student_id` |

The student must be available, have at least one required project skill, and accept the project work type.

## 1. Send one invitation

```text
POST http://127.0.0.1:8000/invitations
```

Choose **Body -> raw -> JSON**:

```json
{
  "owner_id": "{{owner_id}}",
  "project_id": "{{project_id}}",
  "student_id": "{{student_id}}"
}
```

Expected result: **201 Created** and invitation status `PENDING`.

Copy the returned invitation `id` into an `invitation_id` variable.

## 2. Check the Student invitation inbox

```text
GET http://127.0.0.1:8000/students/{{student_id}}/invitations
```

The result includes the project title, budget, deadline, work type, and status. Show these details before asking a student to accept.

## 3. Accept the invitation

```text
POST http://127.0.0.1:8000/invitations/{{invitation_id}}/accept
```

Body:

```json
{
  "student_id": "{{student_id}}"
}
```

Expected result:

```text
invitation status = ACCEPTED
project status = FILLED
```

After this, another invitation attempt for the same project returns **409 Conflict**.

## 4. Decline instead of accepting

Use a fresh project and invitation, then send:

```text
POST http://127.0.0.1:8000/invitations/{{invitation_id}}/decline
```

Body:

```json
{
  "student_id": "{{student_id}}"
}
```

Expected result:

```text
invitation status = DECLINED
project status remains OPEN
```

The owner can now select and invite another eligible student.
