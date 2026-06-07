# YouTube Knowledge Agent

A RAG-based agent that answers questions about YouTube content strategy using accumulated transcript knowledge. Built with the OpenAI API and ChromaDB — no frameworks.

## What It Does

Instead of searching YouTube fresh every time, this agent queries a local vector database of previously analyzed transcripts. Knowledge compounds — every transcript indexed makes future answers better.

```
You: "What hooks do top morning routine creators use?"
Agent: checks index → retrieves relevant chunks → synthesizes answer with sources
```

## Why This Exists (The RAG Learning)

Context windows have limits. You can't paste 500 transcripts into a prompt. RAG solves this by:
1. Converting every transcript paragraph into a vector (a list of numbers representing meaning)
2. Storing those vectors in a database
3. At query time: finding only the paragraphs semantically similar to the question
4. Sending only those relevant paragraphs to the LLM

Result: the model gets focused, relevant context instead of thousands of pages of noise.

## Project Structure

```
youtube-rag-agent/
├── main.py              # Ask questions
├── ingest.py            # Load transcripts into the knowledge base
├── agent/
│   ├── loop.py          # Agent loop — same pattern as the research agent
│   ├── tools.py         # Tool schemas for the retrieval tools
│   └── prompts.py       # System prompt
├── tools/
│   ├── indexer.py       # Converts transcripts to vectors, stores in Chroma
│   └── retriever.py     # Queries Chroma by semantic similarity
├── models/
│   └── schemas.py       # Pydantic models: TranscriptChunk, KnowledgeAnswer
└── vectorstore/         # Chroma database (gitignored — lives on your machine)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Quick Start

**Step 1 — Index sample data (no YouTube API needed):**
```bash
python ingest.py --sample
```
This loads 5 realistic transcript examples across 3 niches: morning_routines, stoic_philosophy, beginner_investing.

**Step 2 — Check what's indexed:**
```bash
python ingest.py --stats
```

**Step 3 — Ask questions:**
```bash
python main.py "What hooks do top morning routine creators use?"
python main.py "What do successful creators say about discipline vs motivation?"
python main.py "Why do beginner investing mistake videos perform so well?"
```

## Using Your Own Research Briefs

If you've run the YouTube Research Agent, you can index those briefs:
```bash
python ingest.py --from-research ../youtube-research-agent/output/brief_*.json
```

## Key Design Decisions

**Chunking with overlap** — Transcripts are split into ~500 word chunks with 50-word overlap. Overlap prevents losing context at chunk boundaries.

**Similarity threshold** — Chunks below 0.2 cosine similarity are filtered out. The agent gets nothing rather than irrelevant results.

**Same loop, different tools** — The agent loop in `agent/loop.py` is structurally identical to the research agent. The only differences are the tools (retrieve vs search) and the system prompt. The loop itself is reusable infrastructure.

**No YouTube API needed** — Once transcripts are indexed, the knowledge base works offline. Only the OpenAI API is needed for embeddings and chat.

## Connection to YouTube Research Agent

This project extends the pipeline:

```
Research Agent          →    Knowledge Agent
(fetches new data)           (queries accumulated data)
       ↓                            ↑
  Research Brief    →    ingest.py  →  vectorstore/
```

The research agent discovers. The knowledge agent remembers.
