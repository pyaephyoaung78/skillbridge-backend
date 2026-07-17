# Postman: Test User and Student APIs

## 1. Start the API

From the project root, run:

```bash
.venv/bin/python -m uvicorn main:app --reload
```

Keep this terminal running. The API base URL is:

```text
http://127.0.0.1:8000
```

## 2. Create a Postman environment

In Postman, create an environment named `SkillBridge Local`.

Create these variables:

| Variable | Initial value |
|---|---|
| `base_url` | `http://127.0.0.1:8000` |
| `student_user_id` | leave empty |
| `student_id` | leave empty |

Select this environment from the top-right environment menu.

## 3. Create a Student user

Create a request:

```text
POST {{base_url}}/users
```

Choose **Body -> raw -> JSON**, then send:

```json
{
  "name": "မေသဇင်",
  "role": "STUDENT"
}
```

You should receive status **201 Created**. Copy the returned `id` value into the `student_user_id` environment variable.

Example response:

```json
{
  "id": "a-uuid-value",
  "name": "မေသဇင်",
  "role": "STUDENT",
  "created_at": "2026-07-18T..."
}
```

## 4. Create the Student profile

Create a request:

```text
POST {{base_url}}/students
```

Choose **Body -> raw -> JSON**, then send:

```json
{
  "user_id": "{{student_user_id}}",
  "university": "University of Yangon",
  "skills": ["GRAPHIC_DESIGN", "CANVA"],
  "availability": "WEEKDAY_EVENINGS",
  "work_preference": "REMOTE",
  "portfolio_url": "https://www.behance.net/example",
  "is_available": true
}
```

You should receive status **201 Created**. Copy the returned profile `id` into the `student_id` environment variable.

## 5. View the Student profile

Create a request:

```text
GET {{base_url}}/students/{{student_id}}
```

Expected result: **200 OK** with the student name, skills, work preference, and availability.

## 6. Update availability

Create a request:

```text
PATCH {{base_url}}/students/{{student_id}}
```

Choose **Body -> raw -> JSON**, then send:

```json
{
  "is_available": false,
  "availability": "WEEKENDS"
}
```

Expected result: **200 OK**. The response should show `is_available: false` and `availability: "WEEKENDS"`.

## 7. Test validation errors

### Unknown skill

Send this to `POST {{base_url}}/students`. You may use the existing `student_user_id`; skill validation happens before the duplicate-profile check:

```json
{
  "user_id": "{{student_user_id}}",
  "university": "University of Yangon",
  "skills": ["MADE_UP_SKILL"],
  "availability": "WEEKDAY_EVENINGS",
  "work_preference": "REMOTE"
}
```

Expected result: **422 Unprocessable Entity**.

### Duplicate profile

Send the same valid create-profile request again using the same `student_user_id`.

Expected result: **409 Conflict** because one user can have only one student profile.

## Available skill values

Use only these uppercase values for now:

```text
GRAPHIC_DESIGN
CANVA
SOCIAL_MEDIA_DESIGN
BRANDING
ILLUSTRATION
CONTENT_WRITING
DIGITAL_MARKETING
DATA_ANALYSIS
VIDEO_EDITING
PROGRAMMING
TRANSLATION
```

## Alternative: Swagger UI

Open this page in a browser:

```text
http://127.0.0.1:8000/docs
```

Swagger shows the same endpoints and lets you send requests without Postman.
