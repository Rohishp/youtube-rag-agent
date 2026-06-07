# agent/tools.py
#
# Tool schemas for the Knowledge Agent.
#
# Compare this to the Research Agent's tools:
#
# Research Agent tools:         Knowledge Agent tools:
# - search_youtube              - retrieve_knowledge
# - get_transcript              - retrieve_by_niche
#                               - get_index_stats
#
# The Research Agent went OUT to gather new information.
# The Knowledge Agent goes IN to query what's already known.
#
# This is the fundamental difference between the two agents —
# and it's entirely expressed in the tool definitions.

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_knowledge",
            "description": """Search the YouTube transcript knowledge base for insights relevant to a specific question or topic.
            
            Use this when you need to answer a question about what works in a YouTube niche,
            what hooks top creators use, what content gaps exist, or what language resonates
            with a specific audience.
            
            The knowledge base contains transcript chunks from YouTube videos that have been
            previously analyzed. Results are ranked by semantic relevance to your query.
            
            Call this multiple times with different phrasings to get comprehensive coverage.
            Example queries:
            - "what opening hooks do morning routine videos use?"
            - "how do successful creators structure productivity content?"
            - "what problems do entrepreneurs say they face with mornings?"
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or topic to search for. Use natural language. Be specific — 'what hooks work in morning routine videos' is better than 'morning routines'."
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of transcript chunks to retrieve. Use 5 for focused questions, 8-10 for broad topics.",
                        "default": 5
                    },
                    "niche_filter": {
                        "type": "string",
                        "description": "Optional. Filter results to a specific niche. Use this when you want insights only from a particular content category. Example: 'morning_routines', 'stoic_philosophy'."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_by_niche",
            "description": """Get a broad overview of everything indexed about a specific niche.
            
            Use this at the START of answering a question to understand what niches
            are well-represented in the knowledge base before doing specific searches.
            
            Also useful when the user asks a general question about a niche rather
            than a specific question about technique or strategy.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "niche": {
                        "type": "string",
                        "description": "The niche to retrieve knowledge for. Must match the niche name used during indexing. Example: 'morning_routines', 'stoic_philosophy', 'beginner_investing'."
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of chunks to return. Default 10.",
                        "default": 10
                    }
                },
                "required": ["niche"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_index_stats",
            "description": """Check what is currently in the knowledge base — how many videos, 
            how many chunks, and which niches are available.
            
            Call this FIRST at the start of every conversation to understand what 
            knowledge is available before trying to answer questions.
            
            If the knowledge base is empty or missing the relevant niche,
            tell the user what needs to be indexed first.
            """,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]
