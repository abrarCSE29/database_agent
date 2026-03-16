import logging
from src.config import LOG_FILE
from src.database import initialize_db
from src.agent.graph import run_agent

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("sql_agent")

def main():
    setup_logging()
    # initialize_db()

    print("SQL Agent Ready! Ask me about your database (type 'quit' to exit)\n")
    print("Example queries:")
    print("- Show me all region names")
    print("- Create a table showing total orders by region")
    print("- Which region has the highest total sales?\n")

    while True:
        user_input = input("Your query: ").strip()
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        print("\nProcessing your request...")
        try:
            response = run_agent(user_input)
            print(f"\n{response}\n")
        except Exception as e:
            print(f"\nI encountered an unexpected error: {str(e)}")
            print("Please try rephrasing your request or try a simpler query.\n")

if __name__ == "__main__":
    main()
