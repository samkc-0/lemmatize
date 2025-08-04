# Headword Tagger API

<p align="center">
  <img width="256" height="256" alt="image" src="https://github.com/user-attachments/assets/f396e6e7-f231-438b-b5fe-150fcde7b4ce" />
</p>

<br/>
fastapi-based microservice for tokenizing and tagging short texts using spaCy, with optional language detection and streaming output.

## endpoints

### `POST /`
analyze short input and return tagged tokens.

**body**:
```json
{
  "text": "ciao, come stai?",
  "language": "it"
}
```

**response:**
```json
[
  { "text": "ciao", "tag": "INTJ" },
  { "text": "come", "tag": "ADV" },
  { "text": "stai", "tag": "VERB" }
]
```

### `POST /stream`

same as above but returns newline-delimited JSON (ndjson), line by line.
- useful for long multiline text inputs or streaming clients.
- content-type: application/x-ndjson

## features
- auto language detection (via langdetect)
- supports italian (it) and spanish (es) (more later)
- fast tagging via spaCy
- handles input up to 140 chars max

## errors
- `400`: invalid or unsupported language
- `413`: input too long
- `500`: spaCy processing error

## note
language detection is probabilistic; you can override it by passing "language" explicitly.

