# SkillBridge Backend

> Burmese-first FastAPI backend for matching students with short paid projects through voice-driven profile and project creation.

SkillBridge is a hackathon MVP that connects students with project owners. Students create a skill profile, project owners create a paid project, and the backend calculates transparent matches based on skills, technical tools, availability, and work preference.

## Main workflow

```text
Student
  -> create User and Student Profile (form or Burmese voice)
  -> view matching OPEN projects
  -> receive an invitation
  -> accept or decline

Project Owner
  -> create Project Owner User
  -> create paid project (form or Burmese voice)
  -> view matching students
  -> see Top 3 priorities and all remaining matches
  -> send one invitation

Accepted invitation -> Project status becomes FILLED
```

One project can have only one active invitation and can be accepted by only one student.

## Features

- Student and Project Owner user roles.
- Student profiles with category skills, technical skills, availability, work preference, and portfolio URL.
- Paid project creation with category and technical requirements.
- Burmese voice transcription with Gemini, including M4A/WebM-to-WAV conversion through FFmpeg when needed.
- AI extraction of profile and project drafts with safe normalization for imperfect AI output.
- Voice drafts return `missing_fields`; incomplete drafts do not create final profiles or projects.
- Owner-to-student matching: `GET /projects/{project_id}/matches`.
- Student-to-project matching: `GET /students/{student_id}/matches`.
- Transparent 100-point matching score, Top 3 priority ranks, and all remaining eligible matches.
- AI-written recommendation text for an owner's Top 3 candidates, with a rule-based fallback.
- One-student invitation workflow: send, accept, decline, and project `FILLED` status.
- Realistic fictional seed data for demo student and project lists.

## Matching rules

The backend does not use AI to rank results. It uses clear rules that can be explained to users and judges.

| Rule | Points |
|---|---:|
| Category skill coverage | Up to 55, or up to 45 when technical requirements exist |
| Technical skill coverage | Up to 10 |
| Exact availability match | 25 |
| Compatible remote/on-site preference | 15 |
| Portfolio URL exists | 5 |

An eligible student must be available, share at least one required category skill, accept the project work type, and match at least one technical requirement when the project specifies technical skills. Student project lists include only `OPEN` projects.

## Tech stack

- Python 3.12+
- FastAPI
- SQLModel and SQLite
- Pydantic
- Google Gemini API for voice transcription and draft extraction
- FFmpeg for M4A/WebM conversion
- Pytest

## Project structure

```text
app/
  models/       Database tables
  schemas/      Request and response models
  routers/      API endpoints
  services/     Matching, Gemini, and voice logic
  seed.py       Repeatable fictional demo data
docs/           Frontend, Postman, voice, and seed guides
tests/          Automated tests
main.py         FastAPI application entry point
```

## Setup

Clone the repository and create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your local environment file. Never commit this file.

```bash
cp .env.example .env
```

Set your Gemini API key in `.env` only when testing voice transcription or AI draft extraction:

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_AUDIO_MODEL=gemini-2.5-flash
MAX_AUDIO_BYTES=10485760
```

Start the development server:

```bash
uvicorn main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### FFmpeg for phone/browser recordings

Install FFmpeg if you upload M4A or WebM recordings:

```bash
sudo apt install -y ffmpeg
```

MP3, WAV, AAC, OGG, AIFF, and FLAC are supported directly by the voice service.

## Seed demo data

The seed script creates 3 project owners, 8 student profiles, and 6 paid `OPEN` projects. It is repeatable and does not duplicate its own records.

```bash
python -m app.seed
```

On a fresh database, expected output:

```text
Seed complete: 11 user(s), 8 student profile(s), 6 project(s) created.
```

See [the demo seed guide](docs/demo-seed-data.md) for details.

## Key endpoints

| Feature | Endpoint |
|---|---|
| Create user | `POST /users` |
| Create student profile | `POST /students` |
| Create project | `POST /projects` |
| Owner's projects | `GET /owners/{owner_id}/projects` |
| Student matches for a project | `GET /projects/{project_id}/matches` |
| Project matches for a student | `GET /students/{student_id}/matches` |
| Owner Top 3 recommendation text | `POST /projects/{project_id}/recommendations` |
| Send invitation | `POST /invitations` |
| Student invitation inbox | `GET /students/{student_id}/invitations` |
| Accept / decline invitation | `POST /invitations/{id}/accept` or `POST /invitations/{id}/decline` |
| Student voice transcription | `POST /voice/transcribe` |
| Owner voice project draft | `POST /projects/voice-draft` |

For exact request examples, use the interactive Swagger page or the documentation in [`docs/`](docs/).

## Run tests

```bash
python -m pytest -q
```

## Documentation

- [Frontend integration guide](docs/frontend-integration-guide.md)
- [Postman user and student testing](docs/postman-user-student-testing.md)
- [Postman project testing](docs/postman-project-testing.md)
- [Postman matching testing](docs/postman-matching-testing.md)
- [Postman invitation testing](docs/postman-invitation-testing.md)
- [Voice and AI setup](docs/voice-and-ai-setup.md)

## Security notes

- Keep `.env`, SQLite databases, and real Gemini API keys out of Git.
- `.env.example` contains placeholders only.
- This MVP has demo identities and does not yet implement authentication or authorization tokens.
