"""In-memory note store (single user, no sessions) plus small utility helpers. Provided, do not edit."""
from datetime import datetime

_INGREDIENTS: list[str] = []
_NOTES: list[str] = []

# --- General utilities --------------------------------------------------------

def get_current_time() -> str:
    return datetime.now().isoformat(timespec="seconds")


def count_words(text: str) -> int:
    """Return the number of words in a text."""
    return len(text.split())


def summarize_text(text: str) -> str:
    """Return a very short summary placeholder."""
    return text[:80]


def reverse_text(text: str) -> str:
    """Reverse a string."""
    return text[::-1]


def contains_keyword(text: str, keyword: str) -> bool:
    """Check whether a keyword appears in text."""
    return keyword.lower() in text.lower()


def calculate(a: float, b: float, operation: str) -> float:
    """Perform a simple arithmetic operation."""
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        return a / b
    raise ValueError("Unknown operation")


# --- Ingredients --------------------------------------------------------------

def add_ingredient(ingredient: str) -> None:
    """Add an ingredient to the list."""
    _INGREDIENTS.append(ingredient)


def remove_ingredients(keyword: str) -> int:
    """Remove every ingredient containing `keyword` (case-insensitive).

    Returns how many ingredients were removed.
    """
    before = len(_INGREDIENTS)
    _INGREDIENTS[:] = [i for i in _INGREDIENTS if keyword.lower() not in i.lower()]
    return before - len(_INGREDIENTS)


def get_ingredients() -> list[str]:
    """Return a copy of the current ingredient list."""
    return list(_INGREDIENTS)


# --- Notes --------------------------------------------------------------------

def add_note(text: str) -> None:
    _NOTES.append(text)


def remove_notes(keyword: str) -> int:
    """Remove every note containing `keyword` (case-insensitive). Returns how many were removed."""
    before = len(_NOTES)
    _NOTES[:] = [n for n in _NOTES if keyword.lower() not in n.lower()]
    return before - len(_NOTES)


def get_notes() -> list[str]:
    """Return a copy of the current notes."""
    return list(_NOTES)


def search_notes(keyword: str) -> list[str]:
    """Return notes containing keyword, case-insensitive."""
    return [n for n in _NOTES if keyword.lower() in n.lower()]


def clear_notes() -> int:
    """Remove all notes and return how many were removed."""
    count = len(_NOTES)
    _NOTES.clear()
    return count


def note_exists(text: str) -> bool:
    """Check whether an exact note (ignoring case and surrounding spaces) already exists."""
    target = text.strip().lower()
    return any(n.strip().lower() == target for n in _NOTES)


def add_note_once(text: str) -> bool:
    """Add a note only if an identical note is not already stored.

    Returns True if added, False if it already existed.
    """
    if note_exists(text):
        return False
    add_note(text)
    return True


def count_notes() -> int:
    """Return the number of stored notes."""
    return len(_NOTES)