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

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Please set it in your environment or .env file before running.\n")
        sys.exit(1)

    agent = HelpdeskAgent(timeout_seconds=15)

    while True:
        try:
            user_input = input("\nCustomer: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nThank you for reaching out to CityWheels! Goodbye.")
                break

            response = agent.run(user_input)

            if response.startswith("ERROR_TIMEOUT") or response.startswith("ERROR_API"):
                print(f"\n[System Notice]: {response}")
                print("Connection to Gemini failed or timed out. Please check your network connection or API key and try again.")
            else:
                print(f"\nAgent:\n{response}")

        except KeyboardInterrupt:
            print("\n\nSession terminated. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n[Unexpected Error]: {e}")

if __name__ == "__main__":
    main()