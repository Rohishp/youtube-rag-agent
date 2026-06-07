# main.py
#
# Entry point for the YouTube Knowledge Agent.
#
# Usage:
#   python main.py "What hooks do top morning routine creators use?"
#   python main.py "What content gaps exist in stoic philosophy content?"
#   python main.py "Why do beginner investing videos get so many views?"

import json
import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="YouTube Knowledge Agent")
    parser.add_argument(
        "question",
        type=str,
        help='Question to ask the knowledge base. Example: "What hooks work in morning routine videos?"'
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Check your .env file.")
        sys.exit(1)

    from agent.loop import ask

    try:
        answer = ask(args.question)

        # Print formatted answer
        print(f"\n{'='*60}")
        print(f"ANSWER")
        print(f"{'='*60}")
        print(f"\n{answer.answer}")

        print(f"\nKEY INSIGHTS:")
        for insight in answer.key_insights:
            print(f"  • {insight}")

        print(f"\nSOURCES ({len(answer.sources)}):")
        for source in answer.sources:
            print(f"  • {source}")

        print(f"\nCONFIDENCE: {answer.confidence.upper()}")
        print(f"  {answer.confidence_reasoning}")

        print(f"\nSUGGESTED FOLLOW-UP:")
        for q in answer.suggested_followup:
            print(f"  → {q}")

        print(f"{'='*60}\n")

    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
