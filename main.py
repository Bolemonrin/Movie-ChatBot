from dotenv import load_dotenv
load_dotenv()

# langchain imports
from langchain.agents import Tool, AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
from langhchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessageState, StageGraph

# custom imports
from tools import *

# define graph
workflow = 



llm = ChatOpenAI(
    model="gpt-4o"
)
# 3. Context / conversation state
search_results = {}   # cache {user_query: [results]}
current_choice = None

# 4. Helper: handle a user query


def handle_query(query: str):
    global search_results, current_choice

    # search TMDB
    results = find_media(query, "movie")  # default to movies for now
    if not results:
        return "Sorry, I couldn’t find anything."

    # if multiple results, save them for clarification
    if len(results) > 1:
        search_results[query] = results
        titles = [
            f"{r['title']} ({r.get('release_date','?')[:4]})" for r in results]
        return f"I found multiple matches: {', '.join(titles)}. Which one did you mean?"

    # if only one, just return summary + recs
    media_id = get_media_id(results, results[0]['title'])
    summary = get_media_summary(media_id, "movie")
    recs = get_media_recommendations(results, "movie", media_id)

    return {
        "summary": summary,
        "recommendations": recs
    }

# 5. Main loop


def main():
    print("MovieBot 🎬 — ask me for a movie or TV show!")

    while True:
        user_input = input("> ")

        if user_input.lower() in {"quit", "exit"}:
            break

        response = handle_query(user_input)
        print(response)


if __name__ == "__main__":
    main()
