#!/usr/bin/env python3
"""
Claire - Making Calculus Clear
CLI Entry Point (LangChain ReAct Version)
"""
import os
import sys
from claire_agent import ClaireAgent


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print the application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                     CLAIRE v2.0                       ║
    ║            Making Calculus Clear ✨                   ║
    ║         Powered by Claude Sonnet + SymPy              ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def print_welcome():
    """Print welcome message"""
    print("\n" + "=" * 60)
    print("🎓 Welcome to Claire - Making Calculus Clear!")
    print("=" * 60)

    print("\n🤖 **What I can do:**")
    print("• Guide you through calculus problems (Socratic method)")
    print("• Calculate derivatives, integrals, limits")
    print("• Explain calculus concepts in simple terms")
    print("• Adapt to your learning level")

    print("\n💡 **Tips:**")
    print("• Type 'help' for commands")
    print("• Type 'examples' for question ideas")
    print("• Type 'status' to see system status")
    print("• Type '/study' to toggle guided learning mode")

    print("\n" + "=" * 60)


def create_env_file():
    """Create a sample .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("\n⚠️  Notice: No .env file found")
        print("Creating sample .env file...")
        with open('.env', 'w') as f:
            f.write("# Anthropic API Key (required for Claire)\n")
            f.write("# Get one from: https://console.anthropic.com/\n")
            f.write("# ANTHROPIC_API_KEY=your_key_here\n\n")
        print("✅ Created .env file. Add your ANTHROPIC_API_KEY to enable Claire.")


def main():
    """Main entry point"""
    clear_screen()
    print_banner()

    # Create .env file if needed
    create_env_file()

    # Initialize the agent
    print("\n🔄 Initializing Claire Agent...")
    try:
        agent = ClaireAgent()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("\nPlease check:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Add ANTHROPIC_API_KEY to your .env file")
        return

    print_welcome()

    print("\n💬 **Ready to help! Ask your calculus questions:**")
    print("Type 'quit' to exit, 'help' for commands")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n🔍 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for using Claire! Happy learning! 🎓")
                print("   Claire - Making Calculus Clear ✨")
                break

            # Process the query (returns dict with 'output' and 'intermediate_steps')
            result = agent.process_query(user_input)

            # Extract the output (handle both dict and string returns)
            if isinstance(result, dict):
                output = result.get('output', '')
                steps = result.get('intermediate_steps', [])

                # Optionally show tool usage in verbose mode
                if steps and os.getenv('CLAIRE_VERBOSE', '').lower() == 'true':
                    print("\n" + "-" * 40)
                    print("🧠 Thinking process:")
                    for i, step in enumerate(steps):
                        if hasattr(step[0], 'tool'):
                            print(f"   Step {i + 1}: Used {step[0].tool}")
                    print("-" * 40)
            else:
                output = str(result)

            print("\n" + "=" * 60)
            print("📚 Claire:")
            print(output)
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted. Type 'quit' to exit or continue asking.")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.")


if __name__ == "__main__":
    main()
