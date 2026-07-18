# SkillBridge Demo Seed Data

## What this creates

The seed script creates fictional, realistic demo records:

- Three Project Owners: Campus Tech Event Team, Mingalar Creative Studio, and Thaton Startup Club
- Eight student profiles with category skills and exact technical skills
- Six paid `OPEN` projects across design, backend development, content, video, data, and marketing
- Several intentional matches for both the Owner and Student dashboards

The data is fictional and safe for a hackathon demo.

## Run the seed script

From the backend project root:

```bash
.venv/bin/python -m app.seed
```

On a completely fresh database, expected output is:

```text
Seed complete: 11 user(s), 8 student profile(s), 6 project(s) created.
```

If you already created one of the demo users manually, the created-user count will be lower. This is expected: the script keeps existing records and creates only missing demo data.

Run the same command again if needed. It is safe: existing demo users and profiles are skipped, so it does not create duplicates.

Expected second-run output:

```text
Seed complete: 0 user(s), 0 student profile(s), 0 project(s) created.
```

## Demo matching

After seeding, call either endpoint:

```text
GET /projects/{project_id}/matches
```

```text
GET /students/{student_id}/matches
```

The Campus Tech Event poster project and its graphic-design students are a clear Top 3 demo. The other projects demonstrate programming, content, video, data, and marketing matching.

## Database note

The local SQLite file is `skillbridge.db`. It is ignored by Git and should not be committed to GitHub.
