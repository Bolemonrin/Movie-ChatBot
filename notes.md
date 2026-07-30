# Testing note: why we patch `agenttest.modelWithTools` (not the model object)

## The pattern

```python
with patch("agenttest.modelWithTools", mock_model):
    from agenttest import agent
    result = agent.invoke(...)
```

This replaces the **name** `modelWithTools` *inside the `agenttest` module* with a
mock, but only for the duration of the `with` block. When the block exits, the real
object is automatically restored.

## Why it works this way

The key fact is **how our node functions look up their dependencies**.

In `agenttest.py`, `llm_call` does:

```python
def llm_call(state):
    return {"messages": [modelWithTools.invoke(...)]}
```

It references `modelWithTools` as a **module-level global, resolved at call time** —
not as an argument passed in, and not as a value captured when the function was
defined. Python doesn't "freeze" that name when the function is created; it looks it
up in the module's namespace *every time the function runs*.

So the swap works because of timing:

1. `patch(...)` rebinds `agenttest.modelWithTools` to the mock.
2. `agent.invoke(...)` runs the graph, which eventually calls `llm_call`.
3. `llm_call` looks up `modelWithTools` **now**, at call time, and finds the mock.
4. The block exits; patch restores the original.

If `llm_call` had instead taken the model as a parameter, or captured it in a closure
at definition time, patching the module global would have no effect — you'd have to
inject the mock some other way.

## Why the import is *inside* the `with` block

```python
with patch("agenttest.modelWithTools", mock_model):
    from agenttest import agent   # <-- inside, on purpose
    result = agent.invoke(...)
```

The patch is only active *within* the block. The line that actually matters is
`agent.invoke(...)` — the graph must **run** while the mock is installed. Putting the
import inside keeps everything that touches the model inside the patched window.

(The import itself is cheap: Python caches modules after first import, so this doesn't
re-execute `agenttest.py`. It just grabs the already-built `agent` object.)

## Why pass the mock as the 2nd argument to `patch`

```python
patch("agenttest.modelWithTools", mock_model)   # good
patch("agenttest.modelWithTools")               # breaks for this object
```

When you call `patch()` **without** a replacement, it first *introspects* the real
object to auto-build a mock (e.g. checks whether it's async). Our real object is a
`_ConfigurableModel` from `init_chat_model`, and its `__getattr__` is booby-trapped:
any unknown attribute access triggers lazy model construction — which throws
`TypeError: _init_chat_model_helper() missing 1 required positional argument: 'model'`.

Passing `mock_model` explicitly tells `patch` "use this, don't introspect," so it never
touches the real object and the trap never fires.

## Patch where the name is *used*, not where it's *defined*

The single most important rule with `patch`: you patch the name **in the namespace
where it is looked up**, which is the module doing the using — here, `agenttest`.
Even though `modelWithTools` is ultimately built from `langchain`, we don't patch
`langchain...`; we patch `agenttest.modelWithTools`, because that's the name
`llm_call` reads at runtime.

Same reasoning for `toolsByName`: `tool_node` reads `agenttest.toolsByName`, so that's
what we patch.

## The general principle

Mock at the **boundaries** (the LLM, the tools — anything external, slow, or
non-deterministic) and let your **own** code (the graph, the routing in
`should_continue`, the message assembly) run for real. The test then verifies *your
logic*, not HuggingFace's uptime or TMDB's API.

---

## Where to read more

- **`unittest.mock` — the `patch` docs**
  https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch
  Covers `return_value`, `side_effect`, and passing `new` explicitly.

- **"Where to patch" (read this one carefully — it's the whole mental model)**
  https://docs.python.org/3/library/unittest.mock.html#where-to-patch
  Explains why you patch the name in the *using* module, not the *defining* one.

- **`side_effect` vs `return_value`**
  https://docs.python.org/3/library/unittest.mock.html#unittest.mock.Mock.side_effect
  A list makes successive calls return successive items — how we script a two-turn
  conversation in the tool-routing test.

- **`MagicMock`**
  https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock

- **pytest's `monkeypatch` (an alternative to `with patch(...)`)**
  https://docs.pytest.org/en/stable/how-to/monkeypatch.html
  Does the same job with a slightly different ergonomics; some people prefer it for
  patching module attributes.

- **Python name resolution / scopes (why the global is read at call time)**
  https://docs.python.org/3/reference/executionmodel.html#resolution-of-names
