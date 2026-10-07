# Hackathon: the note-taking cooking agent (60 min)

Build an AI agent with LangChain that follows a conversation about a dish, **takes notes** while you talk, and when you write `/conclude` produces a complete recipe **based only on what was said**.

The dish used for the final test is secret and invented, so the model cannot rely on memorised recipes. If your notes are wrong or missing, your recipe will be wrong.

## Setup (5 min)

You need [uv](https://docs.astral.sh/uv/). Python 3.12 is installed and managed by uv automatically.

```bash
uv sync                     # creates .venv with Python 3.12 and installs dependencies
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. You get a chat and, on the right, the notes your agent has saved so far.

Never commit `.env` and never put the key in frontend code.

## What you edit

Only `app/agent.py` and `app/helpers.py`. The server (`app/main.py`) and the chat page are provided. The server calls `run_agent(message)` and returns whatever string it gives back.

The file already contains a working but naive agent built with `langchain.agents.create_agent` and one tool, `get_current_time`. Run it first and see how it works.

> Many tutorials online use `create_react_agent` or `AgentExecutor`. Those are deprecated in LangChain/LangGraph v1: use `create_agent`, as in the scaffold.

## Requirements

Your agent must:

1. **Chat** normally and ask for missing details.
2. **Route every message**: decide whether it contains recipe information (save a note), is a correction (remove or change a note), is off-topic (do not save), or is the request for the final recipe.
3. **Keep clean notes**: one fact per note, no duplicates, no greetings or chit-chat, corrections applied ("actually, no garlic" means garlic disappears from the notes).
4. **Write the final recipe from the notes only**: ingredients with quantities and steps. Do not invent ingredients. If something essential was never specified (cooking times, temperatures), say so instead of making it up.

## Suggested pacing

| Minutes | Goal |
|---|---|
| 0-5 | Setup, run the naive agent |
| 5-20 | Working chat, write a real system prompt |
| 20-40 | Tools creation, routing rules, corrections |
| 40-55 | Final recipe from notes, test with the grader |
| 55-60 | README note (see below) |

## Test your agent

With the server running, in another terminal:

```bash
uv run python scripts/grade.py --scenario scenarios/practice.json
```

It plays a scripted conversation, asks for the final recipe and prints a score out of 100. At the end of the hour we run the same script with a **different, hidden dish**, so do not hard-code anything from the practice scenario.

The script grades only the latest assistant reply. It checks that every required ingredient and recipe passage is present, that no ingredient listed as forbidden (unmentioned or retracted) appears, and that notes have no duplicates or chit-chat. Missing required content or an additional forbidden ingredient is a hard failure, even if the numerical score is otherwise high. It cannot check whether you flagged unspecified details, so check that by hand.

In a scenario file, `required_ingredients` maps each ingredient to accepted wording. `required_passages` maps each required step to alternatives; words grouped in a nested list must occur in the same sentence or step. Use `forbidden` to enumerate additions and retracted ingredients that must not appear.

## Hints

Tool documentation strings are what the model reads to decide when to call a tool: write them like instructions. Test one behaviour at a time in the chat UI before running the grader. If the agent "remembers" things you never saved, check that the final recipe really goes through `list_notes`. 

## Grading

| Weight | Criterion |
|---|---|
| 40% | Score of the automated test on the hidden dish |
| 30% | Quality of prompts and routing logic: is the decision to save, correct or ignore explicit and sensible? |
| 20% | A 5-line section at the bottom of this README: one design choice that failed and how you fixed it |
| 10% | Edge cases: corrections, off-topic messages, repeated information |
