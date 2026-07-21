"""
Opus Escalation Strategist

Decides when to escalate to Opus for complex teaching decisions.
Opus is expensive - only use when truly needed.

Escalate to Opus when:
1. Intent requires strategic teaching decision (next_step, check_answer)
2. Retrieval score is too low (no good teaching chunks found)
3. Student seems very confused after multiple attempts
4. Answer verification is needed
5. Complex multi-step reasoning required

Stay with Sonnet/retrieval when:
1. Clear intent + high retrieval score
2. Simple acknowledgment or encouragement
3. Straightforward concept explanation with good chunks
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from tutor.classifier import Classification
from tutor.retrieval import RetrievalResult


@dataclass
class StrategyDecision:
    """Decision on whether to use Opus."""
    use_opus: bool
    reason: str
    confidence: float


# Intents that almost always need Opus
OPUS_REQUIRED_INTENTS = {
    "check_answer",    # Need to verify correctness
    "attempt_answer",  # Need to evaluate student work
    "ask_next_step",   # Need to know teaching path
}

# Intents that rarely need Opus if retrieval is good
RETRIEVAL_SUFFICIENT_INTENTS = {
    "acknowledgment",
    "ask_hint",
    "ask_explanation",
    "confused",
}

# Minimum retrieval score to trust chunks
MIN_RETRIEVAL_SCORE = 0.5

# If student has been confused multiple times, escalate
MAX_CONFUSION_STREAK = 3


def should_use_opus(
    classification: Classification,
    retrieval_result: RetrievalResult,
    recent_thread: Optional[List[Dict[str, Any]]] = None,
) -> StrategyDecision:
    """
    Decide whether to use Opus for this response.

    Args:
        classification: Intent/concept classification
        retrieval_result: Teaching chunk retrieval result
        recent_thread: Recent conversation history

    Returns:
        StrategyDecision with reasoning
    """
    intent = classification.intent
    retrieval_score = retrieval_result.top_score
    requires_strategy = classification.requires_strategy

    # Rule 1: Classifier explicitly says strategy needed
    if requires_strategy and intent in OPUS_REQUIRED_INTENTS:
        return StrategyDecision(
            use_opus=True,
            reason=f"Intent '{intent}' requires strategic teaching decision",
            confidence=0.9,
        )

    # Rule 2: Check answer always needs Opus
    if intent == "check_answer":
        return StrategyDecision(
            use_opus=True,
            reason="Answer verification requires Opus",
            confidence=0.95,
        )

    # Rule 3: Next step needs Opus (teaching path decision)
    if intent == "ask_next_step":
        return StrategyDecision(
            use_opus=True,
            reason="Next step requires teaching path decision",
            confidence=0.9,
        )

    # Rule 4: Good retrieval + simple intent = Sonnet sufficient
    if retrieval_score >= MIN_RETRIEVAL_SCORE and intent in RETRIEVAL_SUFFICIENT_INTENTS:
        return StrategyDecision(
            use_opus=False,
            reason=f"Good retrieval (score={retrieval_score:.2f}) for '{intent}'",
            confidence=0.8,
        )

    # Rule 5: Low retrieval score = need Opus to generate from scratch
    if retrieval_score < MIN_RETRIEVAL_SCORE and len(retrieval_result.chunks) == 0:
        return StrategyDecision(
            use_opus=True,
            reason=f"No relevant teaching chunks found (score={retrieval_score:.2f})",
            confidence=0.7,
        )

    # Rule 6: Check confusion streak
    if recent_thread:
        confusion_count = _count_recent_confusion(recent_thread)
        if confusion_count >= MAX_CONFUSION_STREAK:
            return StrategyDecision(
                use_opus=True,
                reason=f"Student confused {confusion_count}x, need better strategy",
                confidence=0.8,
            )

    # Rule 7: Low confidence classification = be safe, use Opus
    if classification.confidence < 0.5:
        return StrategyDecision(
            use_opus=True,
            reason=f"Low classification confidence ({classification.confidence:.2f})",
            confidence=0.6,
        )

    # Default: If we have any chunks and intent is simple, use Sonnet
    if retrieval_result.chunks and not requires_strategy:
        return StrategyDecision(
            use_opus=False,
            reason="Sufficient chunks and no strategic decision needed",
            confidence=0.7,
        )

    # Ultimate fallback: use Opus to be safe
    return StrategyDecision(
        use_opus=True,
        reason="Default escalation (uncertain case)",
        confidence=0.5,
    )


def _count_recent_confusion(thread: List[Dict[str, Any]], lookback: int = 6) -> int:
    """Count how many recent messages indicate student confusion."""
    confusion_keywords = [
        "不懂", "confused", "still don't", "还是不", "what", "为什么",
        "don't understand", "不明白", "huh", "?", "啥"
    ]

    count = 0
    for msg in thread[-lookback:]:
        if msg.get("role") == "user":
            text = str(msg.get("text", msg.get("content", ""))).lower()
            if any(kw in text for kw in confusion_keywords):
                count += 1

    return count
