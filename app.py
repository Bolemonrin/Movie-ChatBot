"""Entrypoint for the Gradio web chat:  uv run python app.py
(then open http://localhost:7860)

The UI itself lives in movie_chatbot/ui/gradio_app.py.
"""
from movie_chatbot.ui.gradio_app import main

if __name__ == "__main__":
    main()
