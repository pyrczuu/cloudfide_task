import sys
import os
from dotenv import load_dotenv

load_dotenv()

from helpdesk.agent import HelpdeskAgent

def main():
    print("=" * 60)
    print("  CityWheels Customer Help Desk AI Agent")
    print("=" * 60)
    print("Type your question below (or 'exit' / 'quit' to stop).\n")

    # Check for API Key
    if not os.environ.get("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY environment variable is not set.")
        print("Please set it before asking questions to live models.\n")

    try:
        agent = HelpdeskAgent()
    except Exception as e:
        print(f"Initialization Error: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\nCustomer: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nThank you for reaching out to CityWheels! Goodbye.")
                break

            print("\nAgent thinking...", end="\r", flush=True)
            response = agent.run(user_input)
            print(" " * 30, end="\r") # Clear "thinking" line
            print(f"Agent:\n{response}")

        except KeyboardInterrupt:
            print("\n\nSession terminated by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n[Error processing request]: {e}")

if __name__ == "__main__":
    main()