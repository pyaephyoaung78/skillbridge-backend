# Postman: Test Matching API

## Before testing

You need:

1. One `PROJECT_OWNER` user and one open project. Follow [postman-project-testing.md](postman-project-testing.md).
2. At least three available Student profiles. Follow [postman-user-student-testing.md](postman-user-student-testing.md).

For the best demo result, create these students:

| Student | Skills | Availability | Work preference | Portfolio |
|---|---|---|---|---|
| မေသဇင် | `GRAPHIC_DESIGN`, `CANVA` | `WEEKDAY_EVENINGS` | `REMOTE` | Yes |
| ကိုမင်း | `GRAPHIC_DESIGN`, `CANVA` | `WEEKENDS` | `REMOTE` | Yes |
| အိမ့်ပိုး | `GRAPHIC_DESIGN` | `WEEKDAY_EVENINGS` | `REMOTE` | No |

Create a remote project requiring `GRAPHIC_DESIGN` and `CANVA`, with `required_availability` set to `WEEKDAY_EVENINGS`.

## Get the top three matches

Copy the project response `id` into a Postman environment variable named `project_id`.

Send this request:

```text
GET http://127.0.0.1:8000/projects/{{project_id}}/matches
```

Expected result: **200 OK**.

Example response shape:

```json
{
  "project_id": "project-uuid",
  "candidates": [
    {
      "student_id": "student-profile-uuid",
      "name": "မေသဇင်",
      "skills": ["GRAPHIC_DESIGN", "CANVA"],
      "availability": "WEEKDAY_EVENINGS",
      "work_preference": "REMOTE",
      "portfolio_url": "https://www.behance.net/may",
      "matched_skills": ["GRAPHIC_DESIGN", "CANVA"],
      "score": 100,
      "explanation": "..."
    }
  ]
}
```

## Scoring rules

The backend calculates the score. Flutter must show it and must not calculate another score.

| Rule | Points |
|---|---:|
| Required skill coverage | up to 55 |
| Exact availability match | 25 |
| Compatible work type | 15 |
| Portfolio URL exists | 5 |

Students are excluded when they are unavailable, have no matching skill, or do not accept the project's work type.

## Student view: matching projects

Copy a Student Profile response `id` into a Postman variable named `student_id`. This is the ID from `POST /students`, not the User ID from `POST /users`.

```text
GET http://127.0.0.1:8000/students/{{student_id}}/matches
```

Expected result: **200 OK**. The response includes only `OPEN` projects for which the student is eligible. Projects are ranked by the same score and Top 3 priority rules used by the owner candidate list.

This is a project recommendation list, not an official offer. The student can accept only records returned by `GET /students/{{student_id}}/invitations` after an owner sends an invitation.
