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
| Get all matches, with top 3 priority ranks | `GET /projects/{project_id}/matches` | Ready |
| Generate top 3 recommendations | `POST /projects/{project_id}/recommendations` | Ready with AI fallback |
| Send invitation | `POST /invitations` | Ready |
| Student invitations | `GET /students/{student_id}/invitations` | Ready |
| Accept invitation | `POST /invitations/{invitation_id}/accept` | Ready |
| Decline invitation | `POST /invitations/{invitation_id}/decline` | Ready |
| Transcribe voice and optionally save a draft | `POST /voice/transcribe` | Available when `GEMINI_API_KEY` is configured |
| Student transcription history | `GET /student-users/{student_user_id}/transcripts` | Ready |
| Parse student text | `POST /profiles/parse` | Available when `GEMINI_API_KEY` is configured |
| Parse project text | `POST /projects/parse-brief` | Available when `GEMINI_API_KEY` is configured |
| Create read-only project draft from owner voice | `POST /projects/voice-draft` | Available when `GEMINI_API_KEY` is configured |

All core text-based MVP APIs are ready. Voice transcription and AI parsing are optional enhancements that need provider credentials; every voice screen must also keep a normal text/form input.

### Saved voice-profile draft flow

To save a recording for a student, send `multipart/form-data` to `POST /voice/transcribe` with both fields:

| Key | Type | Value |
|---|---|---|
| `file` | File | The audio recording |
| `student_user_id` | Text | The Student User ID returned by `POST /users` |

The response includes a saved `transcription` record and an optional `profile_draft`. Extracted fields can be `null` when speech was unclear or information was not spoken. Show those empty values in the form for the student to complete manually.

`skills` contains controlled matching categories, such as `PROGRAMMING`. `technical_skills` contains exact technologies, such as `Python`, `C++`, `C#`, and `Java`. Send both fields when the student confirms their normal profile form.

For matching, send availability and work preference as exact English API values. The voice extractor converts Burmese phrases to these availability codes:

```text
WEEKDAY_MORNINGS
WEEKDAY_EVENINGS
WEEKEND_MORNINGS
WEEKEND_EVENINGS
FLEXIBLE
```

Do not automatically create or overwrite a `StudentProfile` from a transcript. The student must review/edit the draft, then submit the normal `POST /students` or `PATCH /students/{student_id}` request.

## 4. API base URL

The current backend is deployed for team testing on the cloud server at:

```text
http://165.101.220.41:8000
```

Use this value in Flutter as the API base URL. Do not add a second `/` when joining it with a path.

```dart
const apiBaseUrl = 'http://165.101.220.41:8000';
```

Useful checks:

```text
http://165.101.220.41:8000/
http://165.101.220.41:8000/docs
```

The cloud firewall must allow inbound TCP port `8000`. If the server IP changes, update `apiBaseUrl` and this guide. The current address is for development/testing; production should use a domain name and HTTPS.

For local development, use the URL that matches the Flutter target:

| Flutter target | Base URL |
|---|---|
| Flutter on the same computer | `http://127.0.0.1:8000` |
| Android emulator | `http://10.0.2.2:8000` |
| Physical phone on the same Wi-Fi | `http://YOUR-COMPUTER-LAN-IP:8000` |

The backend must listen on all interfaces when another device needs to reach it:

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

The cloud server currently uses the same command. Keep that terminal/process running while testing.

### Flutter mobile HTTP note

The temporary cloud URL uses `http`, not `https`. If Android blocks the request, enable cleartext HTTP for the debug build in `android/app/src/main/AndroidManifest.xml`, then switch to HTTPS when the final domain is configured. Never put the Gemini API key in Flutter.

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

## 6. Student flow

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
| Name | yes for manual profile | `name` |
| University | yes | `university` |
| Skills, multi-select | yes, at least one | `skills` |
| Technical skills, multi-select | no | `technical_skills` |
| Availability | yes | `availability` |
| Work preference | yes | `work_preference` |
| Portfolio URL | no | `portfolio_url` |
| Available for projects | yes | `is_available` |

When the user confirms the form, call `POST /students`.

```json
{
  "user_id": "user-uuid-from-post-users",
  "name": "မေသဇင်",
  "university": "University of Yangon",
  "skills": ["GRAPHIC_DESIGN", "CANVA"],
  "availability": "WEEKDAY_EVENINGS",
  "work_preference": "REMOTE",
  "portfolio_url": "https://www.behance.net/example",
  "is_available": true
}
```

For a voice-created profile, do not copy the extracted name into the request. Send the saved transcript ID instead of `name`:

```json
{
  "user_id": "user-uuid-from-post-users",
  "transcript_id": "saved-transcript-uuid",
  "university": "Computer University (Thaton)",
  "skills": ["PROGRAMMING"],
  "technical_skills": ["Python", "C++", "C#", "Java"],
  "availability": "WEEKEND_EVENINGS",
  "work_preference": "BOTH",
  "is_available": true
}
```

The backend checks that the transcript belongs to the same `user_id`, then copies `student_transcripts.extracted_name` into the new `student_profiles.name` column.

For an existing profile created before this feature, copy its saved transcript name with:

```json
PATCH /students/{studentProfileId}

{
  "transcript_id": "saved-transcript-uuid"
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

## 7. Project Owner flow

```text
Role Selection
  -> Project Owner Dashboard
  -> Project Form (text input first)
  -> Post paid project
  -> Top 3 Candidate Cards
  -> Candidate Detail
  -> Invitation Confirmation
  -> Project FILLED status
```

### Screen 1: Create a Project Owner demo user

Use the same `POST /users` endpoint as the Student flow, but send the Project Owner role:

```text
POST /users
```

```json
{
  "name": "Tech Event Club",
  "role": "PROJECT_OWNER"
}
```

Example response:

```json
{
  "id": "owner-user-uuid",
  "name": "Tech Event Club",
  "role": "PROJECT_OWNER",
  "created_at": "2026-07-19T10:00:00+00:00"
}
```

Save the returned `id` as:

```text
ownerUserId
```

Important ID rule:

```text
owner_id   = User ID returned by POST /users
student_id = Student Profile ID returned by POST /students
```

### Screen 2: Project Owner dashboard

Load the owner's projects with:

```text
GET /owners/{ownerUserId}/projects
```

Show each project's title, budget, deadline, work type, and status.

### Screen 3: Create a project

Use a normal text/form screen first. When the owner confirms, call:

```text
POST /projects
```

The project form will need:

```text
title (optional)
description
role
required_skills
required_technical_skills (optional)
required_availability
deadline
work_type
budget_mmk
```

Example request:

```json
{
  "owner_id": "owner-user-uuid",
  "title": "Tech Event Social Media Design",
  "description": "Create social-media posters for a university tech event.",
  "role": "GRAPHIC_DESIGNER",
  "required_skills": ["GRAPHIC_DESIGN"],
  "required_technical_skills": ["Canva", "Figma"],
  "required_availability": "WEEKDAY_EVENINGS",
  "deadline": "2026-07-24",
  "work_type": "REMOTE",
  "budget_mmk": 60000
}
```

Use the two skill fields correctly:

| Form field | API field | Example | Matching purpose |
|---|---|---|---|
| Skill category | `required_skills` | `["GRAPHIC_DESIGN"]` | Matches the student's controlled `skills` list. |
| Tool / technology | `required_technical_skills` | `["Canva", "Figma"]` | Matches the student's exact `technical_skills` list, case-insensitively. |

Do **not** send `city` or `location`. Location is intentionally not part of the Project model or matching logic. Also do not send `work_mode`, nested `availability_time`, or nested `fee` fields. Use these flat backend fields instead:

```text
work_type              -> REMOTE or ON_SITE
required_availability  -> one of the availability codes
budget_mmk             -> whole-number MMK amount
```

For this MVP, an owner can require multiple technical terms, but a student is eligible when they match at least one of them; matching more terms improves the score. The owner should use only truly important tools here.

Save the returned project ID as:

```text
projectId
```

Do not show a required-count field. Every project is for one student. The deadline must be today or later.

The backend will set these itself:

```text
compensation_type = PAID
status = OPEN
```

Do not send these as editable Flutter form values.

### Owner voice project flow (no edit screen)

The owner can create a project by voice without editing generated fields:

```text
Record voice
  -> POST /projects/voice-draft
  -> display read-only project summary
  -> owner taps Confirm
  -> POST /projects with the returned project_draft fields
  -> GET /projects/{projectId}/matches
```

Send `multipart/form-data` to `POST /projects/voice-draft`:

| Key | Type | Value |
|---|---|---|
| `file` | File | Owner's audio recording |
| `owner_id` | Text | Project Owner User ID from `POST /users` |

The response is not yet saved as a project:

```json
{
  "transcript": "...",
  "project_draft": {
    "title": "Tech Event Poster Designer",
    "description": "Create posters for an upcoming technology event.",
    "role": "GRAPHIC_DESIGNER",
    "required_skills": ["GRAPHIC_DESIGN"],
    "required_technical_skills": ["Figma"],
    "required_availability": "WEEKEND_MORNINGS",
    "deadline": "2026-07-31",
    "work_type": "REMOTE",
    "budget_mmk": 60000,
    "missing_fields": []
  }
}
```

Show these draft values as read-only. `title` can be `null`; display `Untitled project` in that case. If every other required value is present and `missing_fields` is empty, enable **Confirm**. On confirmation, copy the returned draft values into `POST /projects` and add `owner_id`. Do not provide edit controls. If `missing_fields` contains anything, disable Confirm and ask the owner to record again.

## 8. Matching and invitation flow

### Screen 4: Matched candidate cards

After a project is created, call:

```text
GET /projects/{projectId}/matches
```

The backend returns **every eligible student**, ordered by matching score. The first three candidates have `priority_rank` values `1`, `2`, and `3`; every remaining candidate has `priority_rank: null`.

Show a **Top 3 Recommended Students** section first, then show all remaining candidates in an **Other Eligible Students** section. A candidate card should show:

```text
student name
skills
technical skills
matched technical skills
availability
work preference
portfolio link, if present
match score
rule-based explanation
Invite button
```

The frontend should display the backend score and explanation exactly as returned. Do not calculate a different score in Flutter.

After rendering the top three cards, call:

```text
POST /projects/{projectId}/recommendations
```

No request body is required. It returns one short Burmese recommendation for each priority candidate:

```json
{
  "project_id": "project-uuid",
  "recommendations": [
    {
      "student_id": "student-profile-uuid",
      "priority_rank": 1,
      "score": 100,
      "recommendation": "100% ကိုက်ညီမှုရှိပြီး...",
      "source": "AI"
    }
  ]
}
```

Match ranking always stays rule-based. AI only writes the human-friendly explanation. If Gemini is unavailable, the endpoint returns `source: "RULE_BASED_FALLBACK"`; display that text normally so the owner screen never fails.

If the candidate list is empty, show a friendly empty state such as: “No suitable available students were found for this project.”

### Screen 5: Send one invitation

When the owner selects one candidate, call:

```text
POST /invitations
```

```json
{
  "owner_id": "owner-user-uuid",
  "project_id": "project-uuid",
  "student_id": "student-profile-uuid-from-match-result"
}
```

The result has status `PENDING`. Disable all Invite buttons while the request is loading. After success, show that an invitation is waiting for a response.

### Screen 6: Student invitation inbox

Load invitations for the current student profile:

```text
GET /students/{studentProfileId}/invitations
```

Before the student responds, show the data returned by the backend:

```text
project_title
owner_name
required_skills
deadline
work_type
budget_mmk
status
```

### Screen 7: Accept or decline

To accept:

```text
POST /invitations/{invitationId}/accept
```

To decline:

```text
POST /invitations/{invitationId}/decline
```

Both requests use this JSON body:

```json
{
  "student_id": "student-profile-uuid"
}
```

### Invitation state rule

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

The current backend has no project-cancellation endpoint. Do not add a Cancel button that sends a request yet.

## 9. Error handling rules

Always show a loading indicator while waiting for an API response.

Common HTTP responses:

| Status | Meaning | Frontend action |
|---|---|---|
| `201` | Created successfully | save returned ID and navigate forward |
| `200` | Successful read/update | show updated data |
| `404` | User/profile/project not found | show a friendly “not found” message |
| `403` | Current demo user is not allowed to perform this action | show “You cannot perform this action.” |
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

```text
ProjectDto
- id
- ownerId
- ownerName
- title
- description
- role
- requiredSkills
- requiredTechnicalSkills
- requiredAvailability
- deadline
- workType
- compensationType
- budgetMmk
- status

MatchCandidateDto
- studentId
- name
- skills
- technicalSkills
- availability
- workPreference
- portfolioUrl
- rating
- completedProjects
- matchedSkills
- matchedTechnicalSkills
- score
- explanation

InvitationDto
- id
- projectId
- studentId
- studentName
- ownerName
- projectTitle
- requiredSkills
- deadline
- workType
- budgetMmk
- projectStatus
- status
```

## 11. Team coordination rule

When the frontend needs a field or endpoint that does not exist, ask the backend developer before guessing its JSON name or status value.

The API documentation at `/docs` is the source of truth for currently available request and response formats.

## 12. Current frontend handoff checklist

The frontend developer can now build and connect these screens:

- Role selection and demo user creation.
- Student profile create, read, and edit.
- Project Owner project create and project list.
- Top-three match cards with the backend score and explanation.
- One-invitation flow: send, pending, accept, or decline.
- Project status display: `OPEN` or `FILLED`.
- Optional voice transcription and AI draft parsing after the backend Gemini key is configured.

Use this request order for the main demo:

```text
POST /users
POST /students                  (student role)
POST /users
POST /projects                  (project owner role)
GET  /projects/{projectId}/matches
POST /invitations
GET  /students/{studentId}/invitations
POST /invitations/{id}/accept   OR   POST /invitations/{id}/decline
```

The voice and AI endpoints only return editable text/drafts. They never save a profile or project automatically. After the user confirms the draft, call the normal `POST /students` or `POST /projects` endpoint.
