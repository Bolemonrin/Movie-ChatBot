"""Terminal chat loop -- the plain-text front end for the agent.

Was the `if __name__ == "__main__"` block at the bottom of main.py; pulled out so
importing the agent never risks starting an interactive loop.
"""
import traceback
import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from .agent import media_agent

EXIT_WORDS = {"exit", "quit", "q"}


def main():
    # One thread id for the whole session, so the checkpointer treats every
    # question as part of the same conversation.
    #
    # The annotation is load-bearing for type checkers: invoke() takes a
    # RunnableConfig (a TypedDict), and without it this literal is inferred as a
    # plain dict[str, dict[str, str]], which is not assignable to a TypedDict.
    config: RunnableConfig = {
        'configurable': {
            'thread_id': str(uuid.uuid4()),
        }
    }

    while True:
        try:
            user_input = input("🎬 Ask about a movie (or 'quit'): ")
            if user_input.lower() in EXIT_WORDS:
                print("Exiting...")
                break

            results = media_agent.invoke(
                {'messages': [HumanMessage(content=user_input)]},
                config=config,
            )
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            break

        # [Claude Code] The old loop printed the FIRST non-tool AIMessage in the history,
        # which once the checkpointer accumulates turns is the OLDEST reply — every turn
        # re-printed the first answer. The newest reply is simply the last message.
        print(f"\nAI: {results['messages'][-1].content}\n")


if __name__ == "__main__":
    main()
