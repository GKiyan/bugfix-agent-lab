# bugfix-agent-lab

A small lab to learn how LLM agents work, by building one: a LangGraph agent
that fixes bugs in small Python repositories, run with **local models through
Ollama**, and an evaluation script that measures how often it succeeds.

The question behind it: with a small local model, what actually improves the
success rate: the system prompt, the tools, or the model itself?

## How it works

```
START -> agent -> tools -> agent -> tools -> ... -> END
```

- **`agent.py`**: the LangGraph loop. The `agent` node calls the LLM, the
  `tools` node runs the tool calls it asked for, and the loop stops when the
  model stops calling tools or after `MAX_STEPS = 10` LLM calls. Some models
  write their tool calls as JSON text instead of real tool calls:
  `parse_text_tool_calls()` recovers them.
- **`tools.py`**: the three tools, restricted to the trial's repository:
  - `read_file(path)`
  - `edit_file(path, old_text, new_text)`: replaces a passage of a file
  - `run_tests()`: runs pytest and returns its output
- **`prompts.py`**: the system prompt variants compared:
  - **A**: minimal ("fix the bug so that all the tests pass")
  - **B**: A plus a working method (run the tests, read the files, smallest
    fix, never modify the tests, run the tests again)
  - **C**: B plus rules drawn from the failures seen in the transcripts
    (follow called functions to their definition, copy `old_text` from
    `read_file`, re-read the file after an `edit_file` error)
- **`benchmark/`**: 5 tasks, each with an `ISSUE.md`, a buggy `repo/` and the
  reference fix in `fix/`:

  | Task | Bug |
  |---|---|
  | `01_paginate` | off-by-one, the first page is skipped |
  | `02_grades` | `>` instead of `>=` at a grade boundary |
  | `03_normalize` | division by zero when all values are equal |
  | `04_word_stats` | the bug is in `tokenizer.py`, not in the file the issue points to |
  | `05_cart` | two bugs, one of them in `money.py` (truncation instead of rounding) |

- **`evaluate.py`**: runs every (task, variant) pair 15 times, each in a
  temporary copy of the repo. The model's own claims are never trusted: after
  each trial the original test files are restored and pytest is run again.
  Each trial is appended to `results/results.jsonl` and its full conversation
  is saved in `results/transcripts/`.
- **`scripts/`**: `check_benchmark.py` checks that the tests fail on the buggy
  code and pass with the reference fix; `smoke_test_tools.py` checks that a
  model calls tools reliably.

## Setup and usage

Requires Python 3.12+ and [Ollama](https://ollama.com).

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
ollama pull qwen2.5:14b                         # the model is set by MODEL in agent.py

.venv/bin/python scripts/check_benchmark.py     # sanity check of the benchmark
.venv/bin/python agent.py 01_paginate B         # one trial, prints the conversation
.venv/bin/python evaluate.py 1                  # 1 trial per (task, variant): quick check
.venv/bin/python evaluate.py                    # the real run: 15 trials each, 225 in total
```

`evaluate.py` appends to `results/` and overwrites transcripts with the same
number, so rename `results/` before starting a new run.

## Results

Every run changes **one thing** compared to the previous one, and is kept in
its own folder. Successes out of 75 trials per variant (15 per task), with
the 95% confidence interval of the success rate (Wilson interval, computed by
`wilson()` in `evaluate.py`):

| Run | Change | Model | A | B | C |
|---|---|---|---|---|---|
| `results_strict` | first run (stopped at 91 trials) | qwen2.5:7b | 10/46 (12–36%) | 15/45 (21–48%) | |
| `results_loose` | `edit_file` tolerates missing indentation | qwen2.5:7b | 25 (24–45%) | 24 (23–43%) | |
| `results_already` | `edit_file` says when an edit was already applied | qwen2.5:7b | 21 (19–39%) | 24 (23–43%) | |
| `results_c` | prompt C | qwen2.5:7b | | | 22 (20–40%) |
| `results_content` | `edit_file` errors show the current file content | qwen2.5:7b | 20 (18–38%) | 27 (26–47%) | 24 (23–43%) |
| `results_coder` | code-specialized model | qwen2.5-coder:7b | 12 (9–26%) | 21 (19–39%) | 17 (15–33%) |
| `results_14b` | bigger model | qwen2.5:14b | **28** (27–49%) | **40** (42–64%) | **38** (40–62%) |

Overlapping intervals do not mean there is no difference: for that, the
interval of the difference itself is needed (Newcombe's method):

| Comparison | Difference | 95% CI |
|---|---|---|
| 14B, B − A | +16 points | 0 to +31 |
| 14B, C − A | +13 points | −2 to +28 |
| 7B (`results_content`), B − A | +9 points | −5 to +24 |
| 7B → 14B, all variants (71/225 → 106/225) | +16 points | +7 to +24 |

Per task, 7B (`results_content`) vs 14B (`results_14b`), successes out of 15:

| Task | 7B A / B / C | 14B A / B / C |
|---|---|---|
| `01_paginate` | 10 / 13 / 14 | 15 / 14 / 15 |
| `02_grades` | 4 / 8 / 4 | 6 / 14 / 10 |
| `03_normalize` | 4 / 2 / 4 | 3 / 6 / 7 |
| `04_word_stats` | 1 / 4 / 2 | 2 / 3 / 4 |
| `05_cart` | 1 / 0 / 0 | 2 / 3 / 2 |

With 15 trials, a task's interval is wide: 7/15 gives 25–70%, 14/15 gives
70–99%. Rerunning the same setup moves a task's score by about ±4/15, so only
large or repeated gaps mean something.

## What I learned

- **The tools mattered more than the prompt.** Most early failures were
  `edit_file` calls whose `old_text` did not match the file. Making the tool
  more tolerant and giving useful error messages (the closest passage, the
  current file content, "this edit was probably already applied") changed
  the model's behavior, because the model reacts to what tools return.
- **A 7B model ignores prompt rules when it needs them.** Prompt C's rules
  were almost never applied (re-reading the file after an error, only 4 times
  out of 68...), and A vs B stayed within noise with the 7B models.
- **Code specialization did not help at 7B.** `qwen2.5-coder:7b` wrote its tool
  calls as text, edited the test files despite the prompt, and hit the step
  limit in 157 of 225 trials.
- **Model size was the only big jump**: 71 → 106 successes out of 225 from 7B
  to 14B. With the 14B, prompt B is probably better than A (+12), and the model
  starts finding the bug in `money.py` on `05_cart` (edited in 16/41 trials vs
  3/45 with the 7B). Debugging bugs whose cause is in another file
  (`04_word_stats`, `05_cart`) remains the weak point.
- **Measure, don't trust.** The agent often announces a fix it did not make;
  only re-running the original tests outside the agent gives a real score.
- **A gap is not a proof.** Before computing Wilson's confidence interval,
  I thought prompt B was far better than A with the 14B (40/75 vs 28/75).
  The 95% confidence interval of the difference goes from 0 to 31 points,
  so B is probably better, but it is not proven. With 15 trials per task,
  an interval like 7/15 still spans 25 to 70%, so a gap on a single task
  means almost nothing.

## Limits

- Run on an Apple M1 Pro with 16 GB of RAM: the 14B model is about the
  largest that runs well, and a full 225-trial run takes about 8 hours.
- 16 trials of the 14B run failed with an Ollama "token repeat limit" error
  (the model looped while generating) and count as failures.
- 5 tiny tasks are enough to compare variants, not to judge a model in general.

Ideas not tried: make `edit_file` refuse to modify `test_*.py`, tune
`temperature` / `repeat_penalty` against the token repeat errors.

## How it was built

Built as a learning project with [Claude Code](https://claude.com/claude-code)
as a tutor: I wrote the agent, the evaluation script and the tools, and chose
the experiments; Claude guided the design, reviewed the code, and wrote
prompt C and this README (except the "What I learned" part). That is why
Claude appears as co-author on the commits.
