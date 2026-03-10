"""
Adaptive Algorithm — 1PL Item Response Theory (Rasch Model)
============================================================
Ability (θ) is updated after each response using the IRT logistic model.

P(correct | θ, b) = 1 / (1 + exp(-(θ - b)))

where:
  θ  = student ability (0.0 – 1.0, starts at 0.5)
  b  = item difficulty (0.1 – 1.0)

Ability Update (simplified MLE step):
  θ_new = θ + lr * (response - P(correct | θ, b))

Next question selection:
  - Pick the question whose difficulty is closest to the current θ
  - Exclude already-asked questions
"""

import math
from typing import List, Optional


LEARNING_RATE: float = 0.3      # step size for ability update
MIN_ABILITY: float = 0.05
MAX_ABILITY: float = 0.95


def probability_correct(ability: float, difficulty: float) -> float:
    """1PL IRT probability of a correct response."""
    return 1.0 / (1.0 + math.exp(-(ability - difficulty)))


def update_ability(ability: float, difficulty: float, correct: bool) -> float:
    """
    Update the student's ability estimate using a gradient step
    on the log-likelihood of the IRT model.
    """
    response = 1.0 if correct else 0.0
    p = probability_correct(ability, difficulty)
    new_ability = ability + LEARNING_RATE * (response - p)
    return max(MIN_ABILITY, min(MAX_ABILITY, round(new_ability, 4)))


def select_next_question(
    ability: float,
    questions: List[dict],
    asked_ids: List[str],
) -> Optional[dict]:
    """
    Choose the question with difficulty closest to current ability.
    Ties are broken by picking the harder question (slight upward bias).
    """
    eligible = [q for q in questions if str(q["_id"]) not in asked_ids]
    if not eligible:
        return None

    def closeness(q: dict) -> float:
        diff = abs(q["difficulty"] - ability)
        # small tiebreaker: slightly prefer harder questions
        harder_bonus = -0.01 if q["difficulty"] >= ability else 0.0
        return diff + harder_bonus

    return min(eligible, key=closeness)
