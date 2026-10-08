"""
THE FILE YOU EDIT.

Goal: an agent that follows a chat about a dish, saves recipe-relevant facts as
notes, handles corrections, ignores chit-chat, and on "final recipe" writes a
recipe using ONLY the saved notes.

The server calls `run_agent(session_id, message)` and nothing else. Everything
inside this file is yours to change.
"""
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app import helpers
from scripts import extensions

load_dotenv()

model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)

# --- Tools -------------------------------------------------------------------
# The docstring is what the model reads to decide WHEN to call the tool.
# The output is what the model reads after running the function 

@tool 
def get_current_time() -> str:
    """Returns the current time""" # This is what the agent knows about this function (in addition to the type of input to be given)(the model will generate the input automatically)
    return "Current time is: " + helpers.get_current_time() # This is what the agents reads as an output (it is a text)(make it meaningful)

# TODO 1: write the necessary tools using the helpers in app/notes.py
#   - remove_note(keyword): needed when the user corrects themselves
#   - list_notes(): needed so the final recipe is built from the notes


# --- Prompt (routing lives here, or in code you add around the agent) ---------
# TODO 2: replace this. Decide, for EVERY message: chat only? save a note?
# correct a note? write the final recipe? Spell the rules out.
SYSTEM_PROMPT = "You are a helpful cooking assistant."


agent = create_agent(
    model=model,
    tools=[get_current_time],  # TODO: add your new tools
    system_prompt=SYSTEM_PROMPT
)

def run_agent(message: str) -> str:
    if extensions._is_final_request(message):
        return extensions.conclude(helpers.get_notes(), helpers.get_ingredients())
    
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]}
    )
    return result["messages"][-1].content