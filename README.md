# 🧠 AI-Driven Adaptive Diagnostic Engine

A 1-Dimension Adaptive Testing system that dynamically selects GRE-style questions based on a student's estimated ability using **Item Response Theory (IRT)**, backed by **FastAPI**, **MongoDB**, and **Anthropic Claude**.

---

## 📁 Project Structure

```
adaptive-engine/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── core/
│   │   └── database.py          # Async MongoDB connection (Motor)
│   ├── models/
│   │   └── schemas.py           # Pydantic models (Question, Session, etc.)
│   ├── routers/
│   │   ├── questions.py         # GET /questions endpoints
│   │   └── sessions.py          # Session lifecycle & adaptive logic
│   └── services/
│       ├── adaptive.py          # IRT ability update + question selection
│       └── llm.py               # Anthropic API integration for study plan
├── scripts/
│   └── seed_questions.py        # Seeds 20 GRE questions into MongoDB
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/adaptive-engine.git
cd adaptive-engine
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   MONGO_URI     — your MongoDB Atlas URI or local URI
#   ANTHROPIC_API_KEY — from https://console.anthropic.com/
```

### 5. Seed the database

```bash
python scripts/seed_questions.py
```

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

API is now available at: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sessions` | Start a new adaptive test session |
| `GET` | `/api/sessions/{session_id}` | Get current session state |
| `GET` | `/api/sessions/{session_id}/next-question` | Get the next adaptively selected question |
| `POST` | `/api/sessions/submit-answer` | Submit an answer and update ability |
| `GET` | `/api/sessions/{session_id}/study-plan` | Get AI-generated study plan (after session ends) |
| `GET` | `/api/questions` | List all questions (no correct answers) |
| `GET` | `/api/questions/{question_id}` | Get a single question |

### Example: Full Flow

```bash
# 1. Start a session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"student_name": "Alice", "max_questions": 10}'
# → returns { "session_id": "abc123", ... }

# 2. Get first question
curl http://localhost:8000/api/sessions/abc123/next-question

# 3. Submit answer
curl -X POST http://localhost:8000/api/sessions/submit-answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "abc123", "question_id": "q1id", "selected_answer": "B"}'

# 4. Repeat steps 2–3 until session_complete=true

# 5. Get study plan
curl http://localhost:8000/api/sessions/abc123/study-plan
```

---

## 🧮 Adaptive Algorithm Explanation

### Model: 1-Parameter Logistic IRT (Rasch Model)

The system uses a simplified **Item Response Theory** model to estimate student ability (θ, theta).

#### Probability of a Correct Response

```
P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))
```

- **θ (theta)** = student ability, range `[0.05, 0.95]`, starts at `0.5`
- **b** = item difficulty, range `[0.1, 1.0]`

If θ > b, the student is more likely than not to answer correctly. If θ < b, they are more likely to get it wrong.

#### Ability Update (Gradient Step on Log-Likelihood)

After each answer, ability is updated by:

```
θ_new = θ + lr * (response - P(correct | θ, b))
```

- `lr = 0.3` (learning rate / step size)
- `response = 1` if correct, `0` if incorrect

This is a single-step Newton-Raphson update on the IRT log-likelihood. It moves θ upward when the student answers correctly (especially on hard questions) and downward when incorrect (especially on easy ones). The update naturally diminishes when the question difficulty matches the student's ability.

#### Next Question Selection

The system selects the question from the remaining pool whose **difficulty is closest to the student's current θ**. This maximises Fisher Information — questions near the student's ability are most informative for estimation. A small tiebreaker bias toward harder questions is applied to avoid stagnation.

---

## 🤖 AI Log — How I Used AI Tools

**What I used:** Claude (Anthropic) for development acceleration.

**How it helped:**
- **Boilerplate generation**: FastAPI router structure, Pydantic model definitions, and MongoDB async query patterns were scaffolded in seconds, letting me focus on algorithmic correctness.
- **IRT formula verification**: Used Claude to cross-check the Rasch model update formula and confirm the gradient step derivation against IRT literature.
- **Question bank**: Generated 20 diverse GRE-style questions with calibrated difficulty scores across 5 topics.
- **Prompt engineering**: Iterated on the LLM prompt for the study plan to produce clean JSON output reliably.

**Challenges AI couldn't fully solve:**
- **Motor (async MongoDB) quirks**: Auto-complete and AI suggestions sometimes suggested sync PyMongo calls instead of async Motor equivalents — required manual correction.
- **ObjectId serialization**: Pydantic v2 + PyMongo ObjectId handling required manual testing; AI suggestions were based on Pydantic v1 patterns.
- **IRT parameter tuning**: Choosing the right learning rate (`lr = 0.3`) required empirical reasoning about convergence behavior — AI gave a range but couldn't optimize for this specific question pool.

---

## 🗄️ MongoDB Schema

### `questions` collection

```json
{
  "_id": ObjectId,
  "text": "string",
  "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "correct_answer": "A|B|C|D",
  "difficulty": 0.1–1.0,
  "topic": "Algebra|Geometry|Statistics|Vocabulary|Critical Reasoning",
  "tags": ["tag1", "tag2"]
}
```
**Indexes:** `difficulty`, `topic`

### `sessions` collection

```json
{
  "_id": ObjectId,
  "student_name": "string",
  "ability": 0.0–1.0,
  "question_count": 0–10,
  "max_questions": 10,
  "responses": [
    {
      "question_id": "string",
      "topic": "string",
      "difficulty": 0.1–1.0,
      "selected_answer": "A|B|C|D",
      "correct": true|false,
      "timestamp": ISODate
    }
  ],
  "asked_question_ids": ["id1", "id2"],
  "complete": false,
  "created_at": ISODate
}
```
