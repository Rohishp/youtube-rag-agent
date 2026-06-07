# tools/retriever.py
#
# The Retriever queries the vector database to find relevant transcript chunks.
# This is the "R" in RAG — the retrieval step that happens at query time.
#
# What happens here in plain English:
# 1. Take a question (plain English text)
# 2. Convert it to a vector using the same embedding model used during indexing
# 3. Ask Chroma: "what stored chunks are most similar to this vector?"
# 4. Return those chunks as context for the LLM
#
# This is what the agent calls as a tool.
# The agent doesn't know about vectors or cosine similarity.
# It just calls retrieve_knowledge("what hooks work in morning routine videos?")
# and gets back relevant transcript excerpts.

import json
from tools.indexer import get_collection
from models.schemas import RetrievedChunk, TranscriptChunk


# Minimum similarity threshold
# Chunks below this score are not returned even if they're the "best" available
# Prevents the agent from getting irrelevant results when knowledge base
# doesn't contain anything related to the query
SIMILARITY_THRESHOLD = 0.2


def retrieve_knowledge(query: str, n_results: int = 5, niche_filter: str = None) -> str:
    """
    Retrieve relevant transcript chunks for a given query.
    
    This is the function called by the agent as a tool.
    Returns a formatted string so the agent can read it directly.
    
    Parameters
    ----------
    query : str
        The question or topic to search for
    n_results : int
        How many chunks to return (default 5)
    niche_filter : str, optional
        If provided, only search within this niche
        Example: "morning_routines" or "stoic_philosophy"
    
    Returns
    -------
    str
        Formatted string of relevant chunks with source information
        Ready to be included in the agent's context
    """
    collection = get_collection()

    if collection.count() == 0:
        return json.dumps({
            "error": "Knowledge base is empty. No transcripts have been indexed yet.",
            "suggestion": "Run the indexer first to add transcript knowledge."
        })

    # Build the query parameters
    query_params = {
        "query_texts": [query],
        "n_results": min(n_results, collection.count()),  # Can't request more than exists
        "include": ["documents", "metadatas", "distances"]
    }

    # Apply niche filter if specified
    if niche_filter:
        query_params["where"] = {"niche": niche_filter}

    results = collection.query(**query_params)

    if not results['documents'][0]:
        return json.dumps({
            "error": f"No results found for query: '{query}'",
            "niche_filter": niche_filter
        })

    # Process results
    retrieved = []

    for doc, metadata, distance in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        # Convert Chroma distance to similarity score
        # Chroma with cosine space returns distances where 0 = identical
        similarity = 1 - distance

        # Skip chunks below similarity threshold
        if similarity < SIMILARITY_THRESHOLD:
            continue

        retrieved.append({
            "text": doc,
            "source_video": metadata.get('title', 'Unknown'),
            "channel": metadata.get('channel_name', 'Unknown'),
            "niche": metadata.get('niche', 'Unknown'),
            "view_count": metadata.get('view_count', 0),
            "similarity_score": round(similarity, 3),
        })

    if not retrieved:
        return json.dumps({
            "message": f"No sufficiently relevant chunks found for: '{query}'",
            "note": f"All results were below the similarity threshold of {SIMILARITY_THRESHOLD}",
            "suggestion": "Try rephrasing the query or broadening the search"
        })

    # Format as readable context for the agent
    output = {
        "query": query,
        "chunks_found": len(retrieved),
        "results": retrieved
    }

    return json.dumps(output, ensure_ascii=False, indent=2)


def retrieve_by_niche(niche: str, n_results: int = 10) -> str:
    """
    Retrieve all knowledge about a specific niche.
    Used when the agent wants a broad overview rather than answering
    a specific question.
    """
    collection = get_collection()

    if collection.count() == 0:
        return json.dumps({"error": "Knowledge base is empty."})

    # Get chunks filtered by niche
    niche_data = collection.get(
        where={"niche": niche},
        include=["documents", "metadatas"],
        limit=n_results
    )

    if not niche_data['ids']:
        return json.dumps({
            "message": f"No indexed content found for niche: '{niche}'",
            "available_niches": "Use get_index_stats to see what niches are available"
        })

    results = []
    for doc, metadata in zip(niche_data['documents'], niche_data['metadatas']):
        results.append({
            "text": doc[:300] + "..." if len(doc) > 300 else doc,
            "source_video": metadata.get('title', 'Unknown'),
            "channel": metadata.get('channel_name', 'Unknown'),
        })

    return json.dumps({
        "niche": niche,
        "chunks_found": len(results),
        "results": results
    }, ensure_ascii=False, indent=2)
