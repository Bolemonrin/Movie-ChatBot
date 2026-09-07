# experiments/

Scratch and superseded code. Nothing in `movie_chatbot/` imports any of it —
it's kept for reference, not as part of the app.

| File | What it is |
|---|---|
| `simple_agent.py` | Earlier, simpler agent (no checkpointer, no context node). Superseded by `movie_chatbot/agent/`. |
| `huggingface_agent.py` | Older agent variant on a HuggingFace endpoint instead of Ollama. Stale — it imports tools from a path that no longer exists, and runs its chat loop at import time. |
| `genre_classification.py` | Torch/transformers spike for genre classification (the "mood-based discovery" roadmap item). |
| `randomizer.py` | Unused id generator. |
| `clarify_ambiguity_check.py` | Was `test_tools.py` at the repo root. A manual print-based check for a `clarify_for_ambiguity` helper that no longer exists on any branch, so it fails on its first line. Renamed off the `test_` prefix so pytest and IDE test discovery ignore it. |
| `sample_output/` | Captured tool output kept as reference data. |

Run these as modules from the repo root so imports resolve:

```bash
python -m experiments.simple_agent
```
