"""Smoke test: does the local model reliably call a tool?

We give the model one fake tool (`add`) and a question it should answer by
calling that tool. We repeat the call several times because LLM outputs are
random: one success proves nothing, we want a success *rate*.

Usage:
    python scripts/smoke_test_tools.py              # default model
    python scripts/smoke_test_tools.py llama3.1:8b  # another model
"""

import sys
import time

from langchain_core.tools import tool
from langchain_ollama import ChatOllama

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:7b"
N_TRIALS = 10


@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b


# temperature > 0 on purpose: same setting as the real experiment later,
# so we see the model's real variability.
llm = ChatOllama(model=MODEL, temperature=0.7)
llm_with_tools = llm.bind_tools([add])  # tells the model the tool exists

question = "What is 1234 + 5678? Use the add tool."

n_ok = 0
for i in range(N_TRIALS):
    start = time.time()
    response = llm_with_tools.invoke(question)
    elapsed = time.time() - start

    # A tool call is structured data, not text: name + arguments.
    calls = response.tool_calls
    ok = (
        len(calls) == 1
        and calls[0]["name"] == "add"
        and calls[0]["args"] == {"a": 1234, "b": 5678}
    )
    n_ok += ok
    detail = calls if calls else f"text: {response.content[:60]!r}"
    print(f"trial {i + 1:2d} | {'OK  ' if ok else 'FAIL'} | {elapsed:4.1f}s | {detail}")

print(f"\n{MODEL}: {n_ok}/{N_TRIALS} correct tool calls")
