# SkillBridge Demo Seed Data

## What this creates

The seed script creates:

- One Project Owner: `Tech Event Club`
- Twelve student profiles
- Three strong Graphic Design candidates for the main demo
- Students with Content Writing, Digital Marketing, Data Analysis, Video Editing, Programming, and Translation skills

The data is fictional and safe for a hackathon demo.

## Run the seed script

From the backend project root:

```bash
.venv/bin/python -m app.seed
```

On a completely fresh database, expected output is:

```text
Seed complete: 13 user(s), 12 student profile(s) created.
```

If you already created `Tech Event Club` or any demo users manually in Postman, the created-user count will be lower. This is expected: the script keeps existing records and creates only missing demo data.

Run the same command again if needed. It is safe: existing demo users and profiles are skipped, so it does not create duplicates.

Expected second-run output:

```text
Seed complete: 0 user(s), 0 student profile(s) created.
```

## Main demo project

Create this project from Postman or Flutter after seeding:

```text
Title: Tech Event Social Media Design
Required skills: GRAPHIC_DESIGN, CANVA
Required availability: WEEKDAY_EVENINGS
Work type: REMOTE
Budget: 60,000 MMK
```

Then call:

```text
GET /projects/{project_id}/matches
```

The main graphic-design candidates should appear near the top of the result.

## Database note

The local SQLite file is `skillbridge.db`. It is ignored by Git and should not be committed to GitHub.
