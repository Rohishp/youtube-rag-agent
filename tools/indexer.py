# tools/indexer.py
#
# The Indexer converts YouTube transcripts into searchable vector chunks.
# This is the "R" setup in RAG — building the retrieval database.
#
# What happens here in plain English:
# 1. Take a transcript (long string of text)
# 2. Split it into chunks of ~500 words each
# 3. For each chunk, call OpenAI embeddings API → get a vector
# 4. Store the vector + original text + metadata in Chroma
#
# After indexing, the transcript is permanently searchable.
# Every future query can find relevant paragraphs from it.
#
# This runs ONCE per transcript. Not on every query.
# Indexing is expensive (API calls). Querying is cheap (local search).

import os
import chromadb
from chromadb.utils import embedding_functions
from models.schemas import TranscriptChunk


# Where the vector database lives on disk
VECTORSTORE_PATH = "./vectorstore/chroma_db"

# How many words per chunk
# Too small: chunks lack context, retrieval is noisy
# Too large: chunks are less specific, you retrieve too much irrelevant text
# 500 words is a well-tested default
CHUNK_SIZE_WORDS = 500

# How many words chunks overlap
# Overlap prevents losing context at chunk boundaries
# If a key sentence falls at the end of chunk 1 / start of chunk 2,
# overlap ensures it appears in at least one complete chunk
CHUNK_OVERLAP_WORDS = 50


def get_collection():
    """
    Get or create the Chroma collection.
    Called by both the indexer and retriever — single source of truth.
    """
    client = chromadb.PersistentClient(path=VECTORSTORE_PATH)

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )

    return client.get_or_create_collection(
        name="youtube_transcripts",
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity explicitly
    )


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """
    Split text into overlapping word chunks.
    
    Example with chunk_size=5, overlap=2:
    Text: "A B C D E F G H I J"
    Chunks: ["A B C D E", "D E F G H", "G H I J"]
    
    The overlap (D E, G H) ensures no context is lost at boundaries.
    """
    words = text.split()

    if len(words) <= chunk_size:
        # Text is small enough to be one chunk
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        # Move forward by chunk_size minus overlap
        # This creates the overlap between consecutive chunks
        start += chunk_size - overlap

        # Don't create a tiny final chunk — merge it with the previous one
        remaining = len(words) - start
        if 0 < remaining < chunk_size // 3:
            # Add remaining words to the last chunk and stop
            chunks[-1] = chunks[-1] + " " + " ".join(words[start:])
            break

    return chunks


def index_transcript(
    transcript: str,
    video_id: str,
    title: str,
    channel_name: str,
    niche: str,
    view_count: int,
    published_at: str,
) -> dict:
    """
    Index a YouTube transcript into the vector database.
    
    Returns a summary of what was indexed.
    
    This is called:
    - When you manually add transcripts from your research agent output
    - Or when the agent fetches a new transcript it hasn't seen before
    """
    collection = get_collection()

    # Check if this video is already indexed
    # video_id is unique per video — use it to avoid duplicates
    existing = collection.get(where={"video_id": video_id})
    if existing['ids']:
        return {
            "status": "already_indexed",
            "video_id": video_id,
            "title": title,
            "chunks_existing": len(existing['ids'])
        }

    # Split transcript into chunks
    chunks = chunk_text(transcript)

    # Prepare data for Chroma
    documents = []
    metadatas = []
    ids = []

    for i, chunk_text_content in enumerate(chunks):
        # Skip very short chunks — they're usually artifacts
        if len(chunk_text_content.split()) < 20:
            continue

        # Unique ID: video_id + chunk index
        chunk_id = f"{video_id}_chunk_{i}"

        documents.append(chunk_text_content)
        metadatas.append({
            "video_id": video_id,
            "title": title,
            "channel_name": channel_name,
            "niche": niche,
            "chunk_index": i,
            "view_count": view_count,
            "published_at": published_at,
        })
        ids.append(chunk_id)

    if not documents:
        return {"status": "error", "message": "No valid chunks generated from transcript"}

    # Store in Chroma — this is where the embeddings API gets called
    # Chroma handles the API call internally
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"  [Indexer] ✓ Indexed '{title}' → {len(documents)} chunks stored")

    return {
        "status": "indexed",
        "video_id": video_id,
        "title": title,
        "chunks_created": len(documents),
        "transcript_words": len(transcript.split()),
    }


def get_index_stats() -> dict:
    """How many transcripts and chunks are currently indexed?"""
    collection = get_collection()
    total_chunks = collection.count()

    if total_chunks == 0:
        return {"total_chunks": 0, "total_videos": 0, "niches": []}

    # Get all metadata to count unique videos and niches
    all_data = collection.get(include=["metadatas"])
    video_ids = set()
    niches = set()

    for metadata in all_data['metadatas']:
        video_ids.add(metadata.get('video_id', ''))
        niches.add(metadata.get('niche', ''))

    return {
        "total_chunks": total_chunks,
        "total_videos": len(video_ids),
        "niches": sorted(list(niches)),
    }
