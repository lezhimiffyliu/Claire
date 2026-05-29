"""
CLI entrypoint — run Claire in your terminal.

    export ANTHROPIC_API_KEY=sk-ant-...
    pip install anthropic python-dotenv
    python run_cli.py
"""

import sys
import os

# Support running from both agent/ directory and root directory
if os.path.basename(os.getcwd()) == "agent":
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    sys.path.insert(0, os.getcwd())

from agent.claire_agent import ClaireAgent


def render_event(event: dict):
    """Render a tool event to the terminal."""
    kind = event.get("event")

    if kind == "say":
        print(f"\nClaire: {event['text']}")
        return

    if kind == "ask_back":
        print(f"\nClaire (?): {event['question']}")
        hints = event.get("hints") or []
        if hints:
            print("    options: " + " / ".join(hints))
        return

    if kind == "concept_card":
        card = event["card"]
        print("\n[Concept Card]")
        print(f"  Title: {card.get('title', '')}")
        if card.get("one_liner"):
            print(f"  One-liner: {card['one_liner']}")
        if card.get("explanation"):
            print(f"  Explanation: {card['explanation']}")
        if card.get("example"):
            print(f"  Example: {card['example']}")
        if card.get("connect_to_current"):
            print(f"  Connection: {card['connect_to_current']}")
        return

    print(f"\n[unknown event] {event}")


def main():
    agent = ClaireAgent()
    print("\nClaire is online. Type 'quit' to exit, 'status' for state.\n")

    # Seed with a problem so we can test forward-propagation behavior.
    seed = (
        "I'm starting a new problem: Find the vertex and axis of symmetry of "
        "y = x^2 - 4x + 3."
    )
    print(f"[seed problem]\n{seed}\n")
    agent.process_query(seed, on_event=render_event)

    while True:
        try:
            user_input = input("\nyou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue

        agent.process_query(user_input, on_event=render_event)


if __name__ == "__main__":
    main()