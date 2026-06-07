# agent/loop.py
#
# The Knowledge Agent loop.
#
# ── COMPARE WITH YOUR RESEARCH AGENT ─────────────────────────────────────────
#
# Research Agent loop:               Knowledge Agent loop:
# - Tools: search_youtube,           - Tools: retrieve_knowledge,
#          get_transcript                      retrieve_by_niche,
#                                              get_index_stats
# - Goes OUT to gather info          - Goes IN to query stored knowledge
# - Runs 5-10 iterations             - Runs 3-5 iterations
# - Creates new knowledge            - Uses existing knowledge
#
# The LOOP STRUCTURE is IDENTICAL.
# Same while loop. Same tool execution pattern. Same stop condition.
# Same JSON parsing at the end.
#
# This is the key insight: the agent loop is REUSABLE INFRASTRUCTURE.
# You swap tools and prompts, the loop stays the same.
# ─────────────────────────────────────────────────────────────────────────────

import json
import re
from openai import OpenAI
from agent.tools import TOOL_SCHEMAS
from agent.prompts import SYSTEM_PROMPT, build_user_prompt
from tools.retriever import retrieve_knowledge, retrieve_by_niche
from tools.indexer import get_index_stats
from models.schemas import KnowledgeAnswer


MODEL = "gpt-4o"
client = OpenAI()


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Route tool calls to the correct function."""
    print(f"  → Tool: {tool_name}({json.dumps(tool_input)})")

    try:
        if tool_name == "retrieve_knowledge":
            result = retrieve_knowledge(
                query=tool_input["query"],
                n_results=tool_input.get("n_results", 5),
                niche_filter=tool_input.get("niche_filter")
            )
        elif tool_name == "retrieve_by_niche":
            result = retrieve_by_niche(
                niche=tool_input["niche"],
                n_results=tool_input.get("n_results", 10)
            )
        elif tool_name == "get_index_stats":
            stats = get_index_stats()
            result = json.dumps(stats)
        else:
            result = json.dumps({"error": f"Unknown tool: {tool_name}"})

        preview = result[:200] + "..." if len(result) > 200 else result
        print(f"  ← Result: {preview}")
        return result

    except Exception as e:
        error = f"Tool failed: {str(e)}"
        print(f"  ✗ {error}")
        return json.dumps({"error": error})


def ask(question: str, max_iterations: int = 10) -> KnowledgeAnswer:
    """
    Ask the knowledge agent a question about YouTube niches.
    Returns a structured KnowledgeAnswer with sources and confidence.
    """
    print(f"\n{'='*60}")
    print(f"Question: '{question}'")
    print(f"{'='*60}\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": build_user_prompt(question)},
    ]

    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"[Iteration {iteration}]")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=2048,
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Add assistant message to history
        assistant_msg = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in message.tool_calls
            ]
        messages.append(assistant_msg)

        # Done — parse the answer
        if finish_reason == "stop":
            print("\n[Agent] Answer ready. Parsing...")
            return parse_answer(message.content or "", question)

        # Tool calls
        if finish_reason == "tool_calls" and message.tool_calls:
            for tool_call in message.tool_calls:
                result = execute_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
            continue

        print(f"[Warning] Unexpected finish reason: {finish_reason}")
        break

    raise RuntimeError(f"Agent did not complete within {max_iterations} iterations")


def parse_answer(text: str, question: str) -> KnowledgeAnswer:
    """Parse agent output into KnowledgeAnswer."""
    text = text.strip()

    # Extract JSON from anywhere in the text
    fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if fence_match:
        json_str = fence_match.group(1)
    else:
        first = text.find('{')
        last = text.rfind('}')
        json_str = text[first:last+1] if first != -1 and last != -1 else text

    try:
        data = json.loads(json_str)
        answer = KnowledgeAnswer(**data)
        print(f"[Parser] ✓ Answer parsed. Confidence: {answer.confidence}")
        return answer
    except Exception as e:
        # Fallback — return a minimal valid answer rather than crashing
        print(f"[Parser] Schema validation failed: {e}. Returning raw answer.")
        return KnowledgeAnswer(
            question=question,
            answer=text,
            key_insights=[],
            sources=[],
            confidence="low",
            confidence_reasoning="Could not parse structured output",
            suggested_followup=[]
        )
