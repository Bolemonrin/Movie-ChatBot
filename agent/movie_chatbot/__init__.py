"""Movie ChatBot -- a LangGraph agent that answers movie and TV questions from TMDB.

Layers, outermost first:

    cli.py          the terminal front end (the web front end is the React app
                    in frontend/, served over the api/ package)
    agent/          the LangGraph agent: prompt, state, model, nodes, graph
    tools/          the @tool functions the LLM is allowed to call
    media_lookup    title -> TMDB id
    summarizer      shortening plot overviews
    formatters      rendering a TMDB result as a tool-output line
    rendering       pure string helpers (thinking blocks, poster links)
    tmdb_client     raw HTTP against the TMDB API

Each layer only reaches downwards, so the LLM knowledge stops at agent/ and the
network knowledge stops at tmdb_client.

`from movie_chatbot import media_agent` is deliberately not re-exported here:
importing the agent constructs the model client, which the tool and TMDB tests
have no reason to pay for. Import it from movie_chatbot.agent instead.
"""
