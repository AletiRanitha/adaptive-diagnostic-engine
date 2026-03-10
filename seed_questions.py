"""
Seed script — inserts 20 GRE-style questions into MongoDB.
Run: python scripts/seed_questions.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

QUESTIONS = [
    # ── Algebra (5 questions) ────────────────────────────────────────────────
    {
        "text": "If 3x + 7 = 22, what is the value of x?",
        "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
        "correct_answer": "C",
        "difficulty": 0.2,
        "topic": "Algebra",
        "tags": ["linear_equations", "basic"],
    },
    {
        "text": "What is the solution set of |2x - 6| < 4?",
        "options": ["A) 1 < x < 5", "B) x < 1 or x > 5", "C) -1 < x < 5", "D) x > 5"],
        "correct_answer": "A",
        "difficulty": 0.45,
        "topic": "Algebra",
        "tags": ["absolute_value", "inequalities"],
    },
    {
        "text": "If f(x) = x² - 4x + 3, for what values of x does f(x) = 0?",
        "options": ["A) x = 1 and x = 3", "B) x = -1 and x = -3", "C) x = 2 and x = 6", "D) x = 0 and x = 4"],
        "correct_answer": "A",
        "difficulty": 0.5,
        "topic": "Algebra",
        "tags": ["quadratics", "factoring"],
    },
    {
        "text": "If a + b = 10 and a² + b² = 58, what is the value of ab?",
        "options": ["A) 18", "B) 20", "C) 21", "D) 24"],
        "correct_answer": "C",
        "difficulty": 0.7,
        "topic": "Algebra",
        "tags": ["systems", "identities"],
    },
    {
        "text": "For all real x, the expression (x + 2)/(x² - 4) simplifies to which of the following (x ≠ 2)?",
        "options": ["A) 1/(x - 2)", "B) 1/(x + 2)", "C) (x + 2)/(x - 2)", "D) x/(x - 2)"],
        "correct_answer": "A",
        "difficulty": 0.65,
        "topic": "Algebra",
        "tags": ["rational_expressions", "factoring"],
    },

    # ── Geometry (4 questions) ───────────────────────────────────────────────
    {
        "text": "A circle has a radius of 7. What is its area? (Use π ≈ 3.14)",
        "options": ["A) 43.96", "B) 153.86", "C) 21.98", "D) 49"],
        "correct_answer": "B",
        "difficulty": 0.2,
        "topic": "Geometry",
        "tags": ["circles", "area"],
    },
    {
        "text": "Two parallel lines are cut by a transversal. If one co-interior angle is 65°, what is the other?",
        "options": ["A) 65°", "B) 90°", "C) 115°", "D) 125°"],
        "correct_answer": "C",
        "difficulty": 0.4,
        "topic": "Geometry",
        "tags": ["parallel_lines", "angles"],
    },
    {
        "text": "The legs of a right triangle are 5 and 12. What is the length of the hypotenuse?",
        "options": ["A) 13", "B) 15", "C) 17", "D) 11"],
        "correct_answer": "A",
        "difficulty": 0.3,
        "topic": "Geometry",
        "tags": ["pythagorean_theorem", "triangles"],
    },
    {
        "text": "A cylinder has radius 3 and height 10. What is its volume? (Use π ≈ 3.14)",
        "options": ["A) 94.2", "B) 188.4", "C) 282.6", "D) 376.8"],
        "correct_answer": "C",
        "difficulty": 0.55,
        "topic": "Geometry",
        "tags": ["3d_shapes", "volume"],
    },

    # ── Statistics (3 questions) ─────────────────────────────────────────────
    {
        "text": "What is the median of the set {3, 7, 1, 9, 4, 6, 2}?",
        "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
        "correct_answer": "B",
        "difficulty": 0.25,
        "topic": "Statistics",
        "tags": ["median", "descriptive_stats"],
    },
    {
        "text": "A bag has 4 red, 3 blue, and 5 green balls. What is the probability of drawing a blue ball?",
        "options": ["A) 1/4", "B) 3/12", "C) 1/3", "D) 5/12"],
        "correct_answer": "B",
        "difficulty": 0.35,
        "topic": "Statistics",
        "tags": ["probability", "basic"],
    },
    {
        "text": "The standard deviation of {2, 4, 4, 4, 5, 5, 7, 9} is 2. What is the variance?",
        "options": ["A) 2", "B) 4", "C) 8", "D) 16"],
        "correct_answer": "B",
        "difficulty": 0.6,
        "topic": "Statistics",
        "tags": ["variance", "standard_deviation"],
    },

    # ── Vocabulary (5 questions) ─────────────────────────────────────────────
    {
        "text": "Choose the word most similar in meaning to LOQUACIOUS.",
        "options": ["A) Taciturn", "B) Garrulous", "C) Reticent", "D) Pensive"],
        "correct_answer": "B",
        "difficulty": 0.5,
        "topic": "Vocabulary",
        "tags": ["synonyms", "verbal_reasoning"],
    },
    {
        "text": "EPHEMERAL most nearly means:",
        "options": ["A) Eternal", "B) Transitory", "C) Substantial", "D) Recurring"],
        "correct_answer": "B",
        "difficulty": 0.4,
        "topic": "Vocabulary",
        "tags": ["synonyms", "gre_words"],
    },
    {
        "text": "The word OBFUSCATE most nearly means:",
        "options": ["A) To clarify", "B) To confuse or obscure", "C) To celebrate", "D) To examine closely"],
        "correct_answer": "B",
        "difficulty": 0.65,
        "topic": "Vocabulary",
        "tags": ["synonyms", "hard_gre_words"],
    },
    {
        "text": "Which word is the best antonym for GARRULOUS?",
        "options": ["A) Verbose", "B) Talkative", "C) Laconic", "D) Effusive"],
        "correct_answer": "C",
        "difficulty": 0.7,
        "topic": "Vocabulary",
        "tags": ["antonyms", "hard"],
    },
    {
        "text": "PERFIDIOUS most closely means:",
        "options": ["A) Loyal", "B) Treacherous", "C) Generous", "D) Industrious"],
        "correct_answer": "B",
        "difficulty": 0.75,
        "topic": "Vocabulary",
        "tags": ["synonyms", "hard_gre_words"],
    },

    # ── Reading Comprehension / Critical Reasoning (3 questions) ────────────
    {
        "text": (
            "All mammals are warm-blooded. Dolphins are mammals. "
            "Which conclusion is logically valid?"
        ),
        "options": [
            "A) All warm-blooded animals are dolphins",
            "B) Dolphins are warm-blooded",
            "C) Dolphins are fish",
            "D) All mammals are dolphins",
        ],
        "correct_answer": "B",
        "difficulty": 0.15,
        "topic": "Critical Reasoning",
        "tags": ["syllogism", "deduction"],
    },
    {
        "text": (
            "A study found that students who sleep ≥ 8 hours score higher on exams. "
            "Which of the following, if true, most weakens this conclusion?"
        ),
        "options": [
            "A) High-achieving students tend to manage time better",
            "B) Sleep deprivation reduces memory consolidation",
            "C) Students who scored highest also studied more hours",
            "D) The study sample had 2,000 participants",
        ],
        "correct_answer": "C",
        "difficulty": 0.8,
        "topic": "Critical Reasoning",
        "tags": ["weakening_argument", "hard"],
    },
    {
        "text": (
            "Passage: 'Automation has eliminated many manufacturing jobs, "
            "yet overall unemployment has not risen.' "
            "The author implies that:"
        ),
        "options": [
            "A) Automation is harmful to the economy",
            "B) New jobs have replaced eliminated ones",
            "C) Unemployment statistics are inaccurate",
            "D) Manufacturing is no longer important",
        ],
        "correct_answer": "B",
        "difficulty": 0.6,
        "topic": "Critical Reasoning",
        "tags": ["inference", "reading_comprehension"],
    },
]


async def seed():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "adaptive_engine")
    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]

    collection = db["questions"]
    existing = await collection.count_documents({})
    if existing > 0:
        print(f"⚠️  {existing} questions already in DB. Dropping and re-seeding...")
        await collection.drop()

    result = await collection.insert_many(QUESTIONS)
    print(f"✅ Seeded {len(result.inserted_ids)} questions successfully!")

    # Create indexes
    await collection.create_index("difficulty")
    await collection.create_index("topic")
    print("📑 Indexes created on 'difficulty' and 'topic'")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
