"""
Teaching Chunk Retrieval

Searches for relevant teaching chunks using vector similarity.
Phase 1: Mock implementation with local JSON + simple embedding.
Future: Replace with Supabase pgvector.

Teaching chunk schema:
{
    "id": "chunk_001",
    "course": "126",
    "topic": "partial_derivatives",
    "concept": "treating_variable_as_constant",
    "intent": "ask_explanation",
    "difficulty": "beginner",
    "language": "en",
    "canonical_explanation": "When taking partial derivative with respect to x...",
    "socratic_prompt": "What happens to y when we differentiate with respect to x?",
    "mini_example": "For f(x,y) = x^2 + 3y, ∂f/∂x = 2x (y is treated as constant)",
    "when_to_use": "Student confused about why y disappears or stays",
    "avoid": "Don't just say 'treat y as constant' without explaining why",
    "embedding": [0.1, 0.2, ...]  // Pre-computed
}
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# For mock embeddings
import hashlib


@dataclass
class TeachingChunk:
    """A retrieved teaching chunk."""
    id: str
    course: str
    topic: str
    concept: str
    intent: str
    difficulty: str
    language: str
    canonical_explanation: str
    socratic_prompt: str
    mini_example: str
    when_to_use: str
    avoid: str
    score: float  # Retrieval score 0-1


@dataclass
class RetrievalResult:
    """Result of teaching chunk search."""
    chunks: List[TeachingChunk]
    top_score: float
    query_embedding: List[float]  # For debugging


# ============================================================
# Mock Vector DB (Phase 1)
# ============================================================

_chunks_cache: Optional[List[Dict[str, Any]]] = None


def _load_chunks() -> List[Dict[str, Any]]:
    """Load teaching chunks from JSON file."""
    global _chunks_cache
    if _chunks_cache is not None:
        return _chunks_cache

    chunks_path = Path(__file__).parent / "data" / "teaching_chunks.json"
    if not chunks_path.exists():
        print(f"[retrieval] Warning: {chunks_path} not found, using empty chunks")
        _chunks_cache = []
        return _chunks_cache

    with open(chunks_path, "r", encoding="utf-8") as f:
        _chunks_cache = json.load(f)

    return _chunks_cache


def _mock_embedding(text: str) -> List[float]:
    """
    Mock embedding function.
    Phase 1: Use hash-based pseudo-embedding for deterministic results.
    Future: Replace with OpenAI/Voyage embeddings.
    """
    # Create a deterministic "embedding" from text hash
    h = hashlib.sha256(text.lower().encode()).hexdigest()
    # Convert hex to floats (128 dimensions)
    embedding = []
    for i in range(0, min(64, len(h)), 2):
        val = int(h[i:i+2], 16) / 255.0 - 0.5
        embedding.append(val)
    # Pad to 128 dims
    while len(embedding) < 128:
        embedding.append(0.0)
    return embedding


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _build_query_text(
    intent: str,
    concept: Optional[str],
    message: str,
    problem_context: Optional[Dict[str, Any]],
) -> str:
    """Build query text for embedding."""
    parts = []
    if intent:
        parts.append(f"intent:{intent}")
    if concept:
        parts.append(f"concept:{concept}")
    if problem_context:
        if problem_context.get("topic"):
            parts.append(f"topic:{problem_context['topic']}")
        if problem_context.get("course"):
            parts.append(f"course:{problem_context['course']}")
    parts.append(message[:100])  # Include part of message
    return " ".join(parts)


def search_teaching_chunks(
    intent: str,
    concept: Optional[str],
    message: str,
    problem_context: Optional[Dict[str, Any]] = None,
    top_k: int = 3,
    min_score: float = 0.3,
) -> RetrievalResult:
    """
    Search for relevant teaching chunks.

    Args:
        intent: Classified intent (from classifier)
        concept: Classified concept (from classifier)
        message: Original student message
        problem_context: Current problem info
        top_k: Number of chunks to return
        min_score: Minimum similarity score

    Returns:
        RetrievalResult with top chunks
    """
    chunks = _load_chunks()
    if not chunks:
        return RetrievalResult(chunks=[], top_score=0.0, query_embedding=[])

    # Build query
    query_text = _build_query_text(intent, concept, message, problem_context)
    query_embedding = _mock_embedding(query_text)

    # Score all chunks
    scored = []
    for chunk in chunks:
        # Get or compute chunk embedding
        if "embedding" in chunk:
            chunk_embedding = chunk["embedding"]
        else:
            # Build embedding from chunk content
            chunk_text = f"intent:{chunk.get('intent', '')} concept:{chunk.get('concept', '')} {chunk.get('canonical_explanation', '')}"
            chunk_embedding = _mock_embedding(chunk_text)

        score = _cosine_similarity(query_embedding, chunk_embedding)

        # Boost score for exact matches
        if concept and chunk.get("concept") == concept:
            score += 0.2
        if intent and chunk.get("intent") == intent:
            score += 0.15
        if problem_context:
            if problem_context.get("course") == chunk.get("course"):
                score += 0.1
            if problem_context.get("topic") == chunk.get("topic"):
                score += 0.1

        # Cap at 1.0
        score = min(score, 1.0)

        if score >= min_score:
            scored.append((chunk, score))

    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)

    # Convert to TeachingChunk objects
    results = []
    for chunk, score in scored[:top_k]:
        results.append(TeachingChunk(
            id=chunk.get("id", "unknown"),
            course=chunk.get("course", ""),
            topic=chunk.get("topic", ""),
            concept=chunk.get("concept", ""),
            intent=chunk.get("intent", ""),
            difficulty=chunk.get("difficulty", "intermediate"),
            language=chunk.get("language", "en"),
            canonical_explanation=chunk.get("canonical_explanation", ""),
            socratic_prompt=chunk.get("socratic_prompt", ""),
            mini_example=chunk.get("mini_example", ""),
            when_to_use=chunk.get("when_to_use", ""),
            avoid=chunk.get("avoid", ""),
            score=score,
        ))

    top_score = results[0].score if results else 0.0

    return RetrievalResult(
        chunks=results,
        top_score=top_score,
        query_embedding=query_embedding,
    )


# ============================================================
# Future: Supabase pgvector interface
# ============================================================

async def search_teaching_chunks_pgvector(
    intent: str,
    concept: Optional[str],
    message: str,
    problem_context: Optional[Dict[str, Any]] = None,
    top_k: int = 3,
) -> RetrievalResult:
    """
    Search using Supabase pgvector.
    TODO: Implement when ready to migrate.
    """
    raise NotImplementedError("pgvector search not yet implemented")
