import re, os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), temperature=0)

FINAL_PROMPT = """Write a recipe using ONLY the saved notes below. The notes are
the complete and exclusive source of truth. Do not add ingredients, quantities,
times, temperatures, techniques, equipment, garnishes, or background facts
from general cooking knowledge.

Return:
1. A short title that introduces no new ingredient.
2. An Ingredients section containing every recorded ingredient and quantity.
3. A numbered Method section containing every recorded preparation passage.
4. An "Unspecified details" section listing essential details absent from the
   notes rather than inventing them.

Preserve relationships expressed by the notes: when several notes share the
same action or timing cue (for example, ingredients stirred in "at the end"),
combine them into one method step rather than splitting that passage. Include
recorded serving information and do not describe it as unspecified.

Do not add implied actions such as boiling pasta, draining it, heating a pan,
mixing ingredients, or following package instructions unless those actions are
explicitly present in the notes. Never include a retracted fact. If the notes
are insufficient, say so clearly without completing the missing procedure.
"""

_FINAL_REQUEST = re.compile(
    r"^\s*(?:/conclude|final\s+recipe)\s*[.!?]?\s*$",
    re.IGNORECASE,
)

def _is_final_request(message: str) -> bool:
    return _FINAL_REQUEST.fullmatch(message) is not None

def _message_text(content) -> str:
    """Return plain text from string or content-block model responses."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(part for part in parts if part)
    return str(content)

def conclude(notes: list[str], ingredients: list[str]) -> str:
    """Create the final recipe from curated state in a history-free query.

    The chat agent and its checkpoint are deliberately not invoked here. The
    writer receives only these two lists, so conversational history cannot
    supply retracted facts, off-topic text, or conventional recipe knowledge.
    """
    clean_notes = [note.strip() for note in notes if note.strip()]
    clean_ingredients = [item.strip() for item in ingredients if item.strip()]
    ingredient_text = (
        "\n".join(f"- {item}" for item in clean_ingredients)
        if clean_ingredients
        else "- None recorded separately; use ingredient facts from the notes."
    )
    note_text = (
        "\n".join(f"- {note}" for note in clean_notes)
        if clean_notes
        else "- No preparation notes recorded."
    )
    response = model.invoke(
        [
            {"role": "system", "content": FINAL_PROMPT},
            {
                "role": "user",
                "content": (
                    "Recorded ingredients:\n"
                    f"{ingredient_text}\n\n"
                    "Recorded notes:\n"
                    f"{note_text}"
                ),
            },
        ]
    )
    return _message_text(response.content)