"""Entrypoint for the terminal chat:  uv run python main.py

The agent itself lives in movie_chatbot/ -- see movie_chatbot/__init__.py for
the layer map.
"""
from movie_chatbot.cli import main

if __name__ == "__main__":
    main()
