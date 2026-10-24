"""The 3 tools the agent can use: read a file, edit a file, run the tests.

A tool is a plain Python function. The @tool decorator turns its name,
docstring and type hints into a description that is sent to the model:
the docstring is the only "manual" the model gets, so it must be clear.

Tools never raise: on a problem they return an error message, so the model
can read it and try again instead of crashing the whole trial.
"""

import subprocess
import sys
from pathlib import Path

from langchain_core.tools import tool

MAX_OUTPUT_CHARS = 3000  # keep pytest output short: a 7B model has a small context


def make_tools(repo_dir):
    """Build the tools for one trial. They can only touch files inside `repo_dir`."""
    repo_dir = Path(repo_dir).resolve()

    def safe_path(path):
        """Resolve `path` inside the repo, refusing anything outside it (e.g. '../x')."""
        full = (repo_dir / path).resolve()
        if not full.is_relative_to(repo_dir):
            raise ValueError(f"'{path}' is outside the repository")
        return full

    @tool
    def read_file(path: str) -> str:
        """Read a file of the repository and return its full content.
        `path` is relative to the repository root, for example 'cart.py'."""
        try:
            return safe_path(path).read_text()
        except Exception as e:
            return f"Error: {e}"

    @tool
    def edit_file(path: str, old_text: str, new_text: str) -> str:
        """Edit a file by replacing `old_text` with `new_text`.
        `old_text` must appear exactly once in the file: copy it exactly from
        the file, including indentation. Include a few lines if needed to make it unique."""
        try:
            full = safe_path(path)
            content = full.read_text()
        except Exception as e:
            return f"Error: {e}"

        count = content.count(old_text)
        if count == 0:
            return "Error: old_text was not found. Read the file again and copy the text exactly."
        if count > 1:
            return f"Error: old_text appears {count} times. Include more lines to make it unique."

        full.write_text(content.replace(old_text, new_text))
        return f"Successfully edited {path}."

    @tool
    def run_tests() -> str:
        """Run all the tests of the repository with pytest and return the output."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return "Error: the tests took more than 60 seconds and were stopped."

        output = result.stdout + result.stderr
        if len(output) > MAX_OUTPUT_CHARS:
            # Keep the end: pytest puts the summary of failures there.
            output = "...(truncated)...\n" + output[-MAX_OUTPUT_CHARS:]
        return output

    return [read_file, edit_file, run_tests]
