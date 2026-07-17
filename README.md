# SkillBridge Backend

FastAPI backend for the SkillBridge campus talent match hackathon MVP.

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Start the API from the project root:

```bash
.venv/bin/python -m uvicorn main:app --reload
```

Open the API documentation at <http://127.0.0.1:8000/docs>.

## Run tests

```bash
.venv/bin/python -m pytest
```
