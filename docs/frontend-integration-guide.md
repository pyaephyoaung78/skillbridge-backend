# SkillBridge Frontend Integration Guide

This guide is for the Flutter developer. It explains the app workflow, the API data to send, and the backend rules the frontend must follow.

## 1. The main product flow

SkillBridge connects one Project Owner with one suitable Student for a short, paid project.

```text
Choose role
  -> create demo user
  -> Student creates profile OR Project Owner creates project
  -> backend finds top 3 matches
  -> Owner selects one student and sends one invitation
  -> Student accepts or declines
  -> accepted project becomes FILLED
```

Important: **one project can be accepted by only one student.**

## 2. Frontend and backend responsibilities

### Flutter is responsible for

- Screens, navigation, Burmese-first labels, loading indicators, and error messages.
- Collecting user input.
- Sending API requests to FastAPI.
- Showing API responses to the user.
- Keeping the current demo user's ID locally during the demo.

### FastAPI is responsible for

- SQLite database storage.
- Validating input.
- Creating user, student, project, and invitation records.
- Matching candidates and calculating scores.
- Preventing invalid invitations or more than one accepted student.
- Changing project status to `FILLED` after acceptance.

**Do not access the SQLite database from Flutter.** Flutter must always use the API.

## 3. Current API status

These endpoints are ready now:

| Feature | Method and endpoint | Status |
|---|---|---|
| Create demo user | `POST /users` | Ready |
| Read user | `GET /users/{user_id}` | Ready |
| Create student profile | `POST /students` | Ready |
| Read student profile | `GET /students/{student_id}` | Ready |
| Edit student profile | `PATCH /students/{student_id}` | Ready |
| Create project | `POST /projects` | Ready |
| Read project | `GET /projects/{project_id}` | Ready |
| Owner project list | `GET /owners/{owner_id}/projects` | Ready |

These endpoints will be added next. You can build their screens and use mock data until the backend delivers them:

| Feature | Planned endpoint |
|---|---|
| Get top 3 matches | `GET /projects/{project_id}/matches` |
| Send invitation | `POST /invitations` |
| Student invitations | `GET /students/{student_id}/invitations` |
| Accept invitation | `POST /invitations/{invitation_id}/accept` |
| Decline invitation | `POST /invitations/{invitation_id}/decline` |

Voice transcription and AI parsing are later enhancements. Every voice screen must also have a normal text/form input.

## 4. API base URL

The backend runs locally on port `8000`.

| Flutter target | Base URL |
|---|---|
| Flutter on the same computer | `http://127.0.0.1:8000` |
| Android emulator | `http://10.0.2.2:8000` |
| Physical phone on the same Wi-Fi | `http://YOUR-COMPUTER-LAN-IP:8000` |

For a physical phone, start FastAPI like this:

```bash
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## 5. Shared values: use these exact strings

Do not invent different spelling or casing in Flutter. Send the exact values below.

### User roles

```text
STUDENT
PROJECT_OWNER
```

### Work types

```text
REMOTE
ON_SITE
```

### Student work preferences

```text
REMOTE
ON_SITE
BOTH
```

### Project statuses

```text
OPEN
FILLED
CANCELLED
```

### Invitation statuses

```text
PENDING
ACCEPTED
DECLINED
```

### Allowed skill values

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

In the UI, show friendly Burmese or English labels. Send the uppercase API value.

Example:

```text
UI label: Graphic Design
API value: GRAPHIC_DESIGN
```

## 6. Current student flow: build this now

### Screen 1: Role selection

Show two choices:

```text
I am a Student
I am a Project Owner
```

When a new demo user chooses a role, call `POST /users`.

Request:

```json
{
  "name": "မေသဇင်",
  "role": "STUDENT"
}
```

Success response:

```json
{
  "id": "user-uuid",
  "name": "မေသဇင်",
  "role": "STUDENT",
  "created_at": "2026-07-18T10:00:00+00:00"
}
```

Save these values locally for the current demo session:

```text
currentUserId
currentUserName
currentUserRole
```

For the hackathon, `SharedPreferences` is enough. Full login is not part of this MVP.

### Screen 2: Student profile form

Show these inputs:

| UI field | Required? | API field |
|---|---|---|
| University | yes | `university` |
| Skills, multi-select | yes, at least one | `skills` |
| Availability | yes | `availability` |
| Work preference | yes | `work_preference` |
| Portfolio URL | no | `portfolio_url` |
| Available for projects | yes | `is_available` |

When the user confirms the form, call `POST /students`.

```json
{
  "user_id": "user-uuid-from-post-users",
  "university": "University of Yangon",
  "skills": ["GRAPHIC_DESIGN", "CANVA"],
  "availability": "WEEKDAY_EVENINGS",
  "work_preference": "REMOTE",
  "portfolio_url": "https://www.behance.net/example",
  "is_available": true
}
```

The backend returns a profile. Save this value too:

```text
studentProfileId
```

Then navigate to the Student Dashboard.

### Screen 3: Student dashboard/profile display

To reload the student data, call:

```text
GET /students/{studentProfileId}
```

Show:

- name
- university
- skills
- availability
- work preference
- portfolio URL, if present
- available status
- demo rating and completed projects

### Screen 4: Edit profile

When the student edits the profile, call:

```text
PATCH /students/{studentProfileId}
```

Send only fields that changed. Example:

```json
{
  "is_available": false,
  "availability": "WEEKENDS"
}
```

Do not call `POST /students` again for an existing student. One user can have only one profile; a second create request returns `409 Conflict`.

## 7. Future Project Owner flow

Build these screens now, but use local mock data until their endpoints are available.

```text
Role Selection
  -> Project Owner Dashboard
  -> Project Brief (text input first)
  -> Project Draft Form
  -> Post Project
  -> Top 3 Candidate Cards
  -> Candidate Detail
  -> Invitation Confirmation
  -> Project FILLED status
```

The project form will need:

```text
title
description
role
required_skills
required_availability
deadline
work_type
budget_mmk
```

Do not show a required-count field. Every project is for one student.

The backend will set these itself:

```text
compensation_type = PAID
status = OPEN
```

Do not send these as editable Flutter form values.

## 8. Future matching and invitation flow

### Candidate cards

The matching endpoint will return at most three candidates. A candidate card should show:

```text
student name
skills
availability
work preference
portfolio link, if present
match score
recommendation explanation
Invite button
```

The frontend should display the backend score and explanation exactly as returned. Do not calculate a different score in Flutter.

### Invitation rule

```text
Project OPEN
  -> Owner sends invitation to one student
  -> Invitation PENDING
  -> Student accepts or declines

If accepted:
  invitation = ACCEPTED
  project = FILLED
  no more invitations allowed

If declined:
  invitation = DECLINED
  project remains OPEN
  owner can invite another candidate
```

The frontend should disable the Invite button while the request is loading. Once an invitation is pending or the project is filled, do not show another active Invite button.

## 9. Error handling rules

Always show a loading indicator while waiting for an API response.

Common HTTP responses:

| Status | Meaning | Frontend action |
|---|---|---|
| `201` | Created successfully | save returned ID and navigate forward |
| `200` | Successful read/update | show updated data |
| `404` | User/profile/project not found | show a friendly “not found” message |
| `409` | Conflict, such as duplicate profile | tell user to edit their existing profile |
| `422` | Validation problem | show the backend `detail` message near the form |
| `500` | Server error | show “Something went wrong. Please try again.” |

FastAPI may return `detail` as either text or a list of field errors. Handle both safely.

## 10. Suggested Flutter data models

Keep API DTOs simple and match the JSON field names.

```text
UserDto
- id
- name
- role
- createdAt

StudentProfileDto
- id
- userId
- name
- university
- skills
- availability
- workPreference
- portfolioUrl
- rating
- completedProjects
- isAvailable
```

Later add `ProjectDto`, `MatchCandidateDto`, and `InvitationDto` when their endpoints are ready.

## 11. Team coordination rule

When the frontend needs a field or endpoint that does not exist, ask the backend developer before guessing its JSON name or status value.

The API documentation at `/docs` is the source of truth for currently available request and response formats.
