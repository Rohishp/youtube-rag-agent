# models/schemas.py
#
# Data models for the YouTube Knowledge Agent.
# Smaller than the pipeline project — this agent has one job:
# answer questions about YouTube niches using accumulated knowledge.

from pydantic import BaseModel, Field
from typing import Optional


class TranscriptChunk(BaseModel):
    """
    One chunk of a YouTube transcript stored in the vector database.
    
    Why chunk instead of storing the whole transcript?
    A full transcript is 8,000+ characters. If you store it as one unit,
    a query retrieves the ENTIRE transcript even if only one paragraph
    is relevant. Chunking means you retrieve only the relevant paragraph.
    
    Target chunk size: 400-600 words. Large enough to have context,
    small enough to be specific.
    """
    video_id: str
    title: str
    channel_name: str
    niche: str
    chunk_index: int        # Which chunk this is within the transcript (0, 1, 2...)
    text: str               # The actual transcript text
    view_count: int
    published_at: str


class RetrievedChunk(BaseModel):
    """A chunk returned by the retriever, with its similarity score."""
    chunk: TranscriptChunk
    similarity_score: float


class KnowledgeAnswer(BaseModel):
    """
    Structured answer from the knowledge agent.
    
    Every answer includes its sources — which videos the insights came from.
    This is important for two reasons:
    1. Credibility — the creator can verify the source
    2. Traceability — you can see which transcripts the agent is drawing from
    """
    question: str
    answer: str
    key_insights: list[str]         # Bullet-point summary of main findings
    sources: list[str]              # Video titles the answer draws from
    confidence: str                 # "high" / "medium" / "low"
    confidence_reasoning: str       # Why this confidence level
    suggested_followup: list[str]   # Questions the user might want to ask next
