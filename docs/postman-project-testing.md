# Postman: Test Project APIs

## 1. Create a Project Owner user

First create a user with the `PROJECT_OWNER` role.

```text
POST http://127.0.0.1:8000/users
```

Choose **Body -> raw -> JSON** and send:

```json
{
  "name": "Tech Event Club",
  "role": "PROJECT_OWNER"
}
```

Copy the returned `id`. In Postman, save it as an environment variable named `owner_id`.

## 2. Create a paid project

```text
POST http://127.0.0.1:8000/projects
```

Choose **Body -> raw -> JSON** and send:

```json
{
  "owner_id": "{{owner_id}}",
  "title": "Tech Event Social Media Design",
  "description": "Create social-media posters for a university tech event.",
  "role": "GRAPHIC_DESIGNER",
  "required_skills": ["GRAPHIC_DESIGN"],
  "required_technical_skills": ["Canva"],
  "required_availability": "WEEKDAY_EVENINGS",
  "deadline": "2026-07-24",
  "work_type": "REMOTE",
  "budget_mmk": 60000
}
```

Expected result: **201 Created**. The response must include:

```json
{
  "compensation_type": "PAID",
  "status": "OPEN"
}
```

Project requirements are split deliberately:

- `required_skills`: allowed matching categories in uppercase, for example `GRAPHIC_DESIGN`.
- `required_technical_skills`: optional exact tools/technologies, for example `Canva`, `Figma`, or `Python`.

Do not send `city`, `location`, `work_mode`, a nested `availability_time` object, or a nested `fee` object. This MVP uses `work_type`, `required_availability`, and `budget_mmk` instead. A project is remote or on-site; it does not currently match by city.

Use a deadline that is today or in the future. The backend rejects past dates.

Copy the response `id` to a Postman environment variable named `project_id`.

## 3. View one project

```text
GET http://127.0.0.1:8000/projects/{{project_id}}
```

Expected result: **200 OK**.

## 4. View the Project Owner dashboard list

```text
GET http://127.0.0.1:8000/owners/{{owner_id}}/projects
```

Expected result: **200 OK** and a JSON list of the owner's projects.

## 5. Test errors

### A Student cannot post a project

Create a user with role `STUDENT`, then use that user's ID as `owner_id` in the project request.

Expected result: **422 Unprocessable Entity**.

### Budget must be positive

Set this in the request body:

```json
"budget_mmk": 0
```

Expected result: **422 Unprocessable Entity**.

### Required skills must use allowed values

Set this in the request body:

```json
"required_skills": ["MADE_UP_SKILL"]
```

Expected result: **422 Unprocessable Entity**.
