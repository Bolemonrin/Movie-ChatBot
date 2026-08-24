"""Movie ChatBot -- a LangGraph agent that answers movie and TV questions from TMDB.

Layers, outermost first:

    ui/, cli.py     front ends (Gradio web chat, terminal REPL)
    agent/          the LangGraph agent: prompt, state, model, nodes, graph
    tools/          the @tool functions the LLM is allowed to call
    media_lookup    title -> TMDB id
    summarizer      shortening plot overviews
    formatters      rendering a TMDB result as a tool-output line
    tmdb_client     raw HTTP against the TMDB API

Each layer only reaches downwards, so the LLM knowledge stops at agent/ and the
network knowledge stops at tmdb_client.

`from movie_chatbot import media_agent` is deliberately not re-exported here:
importing the agent constructs the model client, which the tool and TMDB tests
have no reason to pay for. Import it from movie_chatbot.agent instead.
"""
