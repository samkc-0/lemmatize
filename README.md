# Headword Tagger API

fastapi-based microservice for tokenizing and tagging short texts using spaCy, with optional language detection and streaming output.

---

## 🚀 endpoints

### `POST /`
analyze short input and return tagged tokens.

- **body**:
  ```json
  {
    "text": "ciao, come stai?",
    "language": "it" // optional
  }
