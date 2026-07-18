# Voice and AI Setup

## What the endpoints do

| Endpoint | Purpose | Saves to database? |
|---|---|---|
| `POST /voice/transcribe` | Short Burmese audio -> editable transcript | No |
| `POST /profiles/parse` | Confirmed text -> student profile draft | No |
| `POST /projects/parse-brief` | Confirmed text -> project form draft | No |

Flutter must show the returned transcript or draft, let the user edit it, then call the existing `POST /students` or `POST /projects` endpoint only after confirmation.

## 1. Install dependencies

```bash
.venv/bin/python -m pip install -r requirements.txt
```

## 2. Configure environment variables

Copy the example file locally:

```bash
cp .env.example .env
```

Set these values in `.env`:

```text
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_AUDIO_MODEL=gemini-2.5-flash
```

Do not commit `.env`. Google Cloud Speech-to-Text, a Google Cloud project, and a service-account JSON file are no longer required.

## 3. Speech configuration

The Speech-to-Text configuration is:

```text
provider: Gemini API
model: gemini-2.5-flash
language instruction: Burmese (Myanmar)
```

Use short, completed recordings for the MVP (about 10–15 seconds). The API accepts audio uploads up to 10 MB by default. It is not a live, word-by-word transcription service.

## 4. Test in Postman

### Transcribe audio

```text
POST http://127.0.0.1:8000/voice/transcribe
```

In Postman select **Body -> form-data**:

| Key | Type | Value |
|---|---|---|
| `file` | File | choose a short `.m4a`, `.mp3`, `.wav`, or `.webm` recording |

### Parse a student profile

```text
POST http://127.0.0.1:8000/profiles/parse
```

Choose **Body -> raw -> JSON**:

```json
{
  "text": "ကျွန်တော် မောင်မောင်ပါ။ University of Yangon မှာ Computer Science တက်နေပါတယ်။ Graphic Design နဲ့ Canva တတ်ပါတယ်။ Weekday evening မှာ အလုပ်လုပ်လို့ရပါတယ်။ Remote project ကိုပိုကြိုက်ပါတယ်။"
}
```

### Parse a project brief

```text
POST http://127.0.0.1:8000/projects/parse-brief
```

```json
{
  "text": "Friday မတိုင်ခင် tech event အတွက် social media poster ဆွဲပေးမယ့် Graphic Designer လိုတယ်။ Remote လုပ်လို့ရတယ်။ Project budget က 60000 ကျပ်ပါ။"
}
```

If `GEMINI_API_KEY` is not configured, the endpoints return `503 Service Unavailable`. This is expected; Flutter should offer the normal manual form instead.
