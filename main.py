#!/usr/bin/env python3
"""
Calctoa - AI Calculus Teaching Assistant
Main entry point
"""
import os
import sys
from calctoa_agent import CalctoaAgent

def clear_screen():
    """Clear screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║                    CALCTOA v1.0                       ║
    ║      AI-Powered Calculus Teaching Assistant           ║
    ║      Powered by Mathics + OpenAI GPT                  ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)

def print_welcome():
    """Print welcome message"""
    print("\n" + "="*60)
    print("🎓 Welcome to Calctoa - Your Intelligent Calculus Tutor!")
    print("="*60)
    
    print("\n🤖 **What I can do:**")
    print("• Explain calculus concepts in simple terms")
    print("• Solve problems step-by-step")
    print("• Calculate derivatives, integrals, limits")
    print("• Teach you calculus from basics to advanced")
    print("• Understand both natural language and math syntax")
    
    print("\n💡 **Tips:**")
    print("• Type 'help' for commands")
    print("• Type 'examples' for question ideas")
    print("• Type 'capabilities' to see what I can do")
    print("• Use Mathics/Wolfram syntax for precise calculations")
    
    print("\n" + "="*60)

def main():
    """Main function"""
    clear_screen()
    print_banner()
    
    if not os.path.exists('.env'):
        print("\n⚠️  Notice: No .env file found")
        print("Creating sample .env file...")
        with open('.env', 'w') as f:
            f.write("# OpenAI API Key (optional but recommended)\n")
            f.write("# Get one from: https://platform.openai.com/api-keys\n")
            f.write("# OPENAI_API_KEY=your_key_here\n\n")
            f.write("# Other configuration\n")
        print("✅ Created .env file. Add your OpenAI API key for AI capabilities.")
    
    print("\n🔄 Initializing Calctoa Agent...")
    try:
        agent = CalctoaAgent()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("\nPlease check:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. For Mathics: pip install mathics")
        print("3. For AI: Add OpenAI API key to .env")
        return
    
    print_welcome()
    
    print("\n💬 **Ready to help! Ask your calculus questions:**")
    print("Type 'quit' to exit, 'help' for commands")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n🔍 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for using Calctoa! Happy learning! 🎓")
                break
            
            response = agent.process_query(user_input)
            
            print("\n" + "="*60)
            print("📚 Calctoa:")
            print(response)
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted. Type 'quit' to exit or continue asking.")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()