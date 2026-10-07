"""
Automated check. Run the server first, then:

    uv run python scripts/grade.py --scenario scenarios/practice.json

The grader sends the scripted conversation and the conclusion request. Only the
latest assistant reply is graded. A passing reply must contain every required
ingredient and required recipe passage, and none of the forbidden additions.
"""
import argparse
import json
import re
import sys
import uuid
from collections.abc import Iterable
from typing import Any

import httpx

NEGATION_WORDS = r"no|not|without|omit(?:ted)?|skip(?:ped)?|free[ -]of|never|remove(?:d)?|exclude(?:d)?"


def _term_pattern(term: str) -> re.Pattern[str]:
    """Build a case-insensitive whole-term matcher with a simple plural form."""
    return re.compile(rf"(?<!\w){re.escape(term)}(?:s)?(?!\w)", re.I)


def mentioned(term: str, text: str) -> bool:
    """Return True when ``term`` has at least one non-negated occurrence."""
    term_pattern = _term_pattern(term)
    for match in term_pattern.finditer(text):
        before = text[max(0, match.start() - 60):match.start()]
        # Negation does not leak from a previous sentence or list item.
        before = re.split(r"[.!?;\n]", before)[-1]
        after = re.split(r"[.!?;\n]", text[match.end():match.end() + 30])[0]
        negated_before = re.search(
            rf"\b(?:{NEGATION_WORDS})\b(?:\W+\w+){{0,3}}\W*$",
            before,
            re.I,
        )
        negated_after = re.match(
            rf"\W+(?:is\W+|was\W+|should\W+be\W+)?(?:{NEGATION_WORDS})\b",
            after,
            re.I,
        )
        if not negated_before and not negated_after:
            return True
    return False


def _passages(text: str) -> list[str]:
    """Split a recipe into sentence/step-sized passages without splitting lists."""
    return [
        part.strip()
        for part in re.split(r"(?:\r?\n)+|(?<=[.!?;])\s+", text)
        if part.strip()
    ]


def _alternative_matches(alternative: Any, passage: str) -> bool:
    if isinstance(alternative, str):
        return mentioned(alternative, passage)
    if isinstance(alternative, list) and all(isinstance(term, str) for term in alternative):
        return all(mentioned(term, passage) for term in alternative)
    raise ValueError(
        "Each required passage alternative must be a string or a list of strings"
    )


def passage_present(alternatives: Any, text: str) -> bool:
    """Check whether one allowed alternative occurs within one recipe passage."""
    if isinstance(alternatives, str):
        alternatives = [alternatives]
    if not isinstance(alternatives, list):
        raise ValueError("Required passage definitions must be strings or lists")

    return any(
        _alternative_matches(alternative, passage)
        for passage in _passages(text)
        for alternative in alternatives
    )


def latest_reply(responses: Iterable[dict[str, Any]]) -> str:
    """Extract only the reply from the most recent server response."""
    responses = list(responses)
    if not responses:
        raise ValueError("The server returned no responses")
    reply = responses[-1].get("reply")
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("The latest server response has no non-empty 'reply'")
    return reply


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--scenario", default="scenarios/practice.json")
    args = ap.parse_args()

    with open(args.scenario, encoding="utf-8") as scenario_file:
        sc = json.load(scenario_file)

    sid = str(uuid.uuid4())
    responses: list[dict[str, Any]] = []
    with httpx.Client(base_url=args.url, timeout=120) as client:
        def send(msg: str) -> dict[str, Any]:
            response = client.post(
                "/agent/query",
                json={"session_id": sid, "message": msg},
            )
            response.raise_for_status()
            payload = response.json()
            responses.append(payload)
            return payload

        for message in sc["messages"]:
            print(f"> {message}")
            send(message)

        print(f"> {sc['final_message']}")
        final_output = send(sc["final_message"])

    # Grade only the newest reply. Earlier assistant messages may mention
    # suggestions or corrections and must not affect the final result.
    recipe = latest_reply(responses)
    notes = final_output["notes"]

    print("\n--- NOTES ---")
    for note in notes:
        print(" -", note)
    print("\n--- LATEST REPLY ---\n" + recipe + "\n")

    results = []  # (label, points earned, points possible)

    required_ingredients = sc.get("required_ingredients", sc.get("required", {}))
    ingredient_hits = [
        name
        for name, variants in required_ingredients.items()
        if any(mentioned(variant, recipe) for variant in variants)
    ]

    required_passages = sc.get("required_passages", {})
    ingredient_points = 35 if required_passages else 50
    results.append((
        f"required ingredients in latest reply ({len(ingredient_hits)}/{len(required_ingredients)})",
        ingredient_points * len(ingredient_hits) / max(1, len(required_ingredients)),
        ingredient_points,
    ))
    missing_ingredients = [
        name for name in required_ingredients if name not in ingredient_hits
    ]
    for name in missing_ingredients:
        print(f"  missing ingredient: {name}")

    passage_hits = [
        name
        for name, alternatives in required_passages.items()
        if passage_present(alternatives, recipe)
    ]
    missing_passages = [name for name in required_passages if name not in passage_hits]
    if required_passages:
        results.append((
            f"required passages in latest reply ({len(passage_hits)}/{len(required_passages)})",
            15 * len(passage_hits) / len(required_passages),
            15,
        ))
        for name in missing_passages:
            print(f"  missing passage: {name}")

    forbidden_hits = [term for term in sc.get("forbidden", []) if mentioned(term, recipe)]
    # Extra ingredients are a hard failure: the assignment explicitly requires
    # a final recipe based only on the saved facts.
    results.append((
        f"no forbidden/additional ingredients in latest reply {forbidden_hits or ''}",
        25 if not forbidden_hits else 0,
        25,
    ))

    bad_notes = [
        term
        for term in sc.get("forbidden", [])
        if any(mentioned(term, note) for note in notes)
    ]
    results.append((
        f"removed/unmentioned items not in notes {bad_notes or ''}",
        10 if not bad_notes else 0,
        10,
    ))

    normalized_notes = [re.sub(r"\W+", " ", note.casefold()).strip() for note in notes]
    duplicate_count = len(normalized_notes) - len(set(normalized_notes))
    results.append((
        f"no duplicate notes ({duplicate_count} duplicates)",
        5 if duplicate_count == 0 else 0,
        5,
    ))

    noisy_notes = [
        note
        for note in notes
        if any(re.search(pattern, note, re.I) for pattern in sc.get("noise", []))
    ]
    results.append((f"no chit-chat in notes {noisy_notes or ''}", 5 if not noisy_notes else 0, 5))

    note_range = sc.get("note_count_range", [1, 20])
    notes_in_range = note_range[0] <= len(notes) <= note_range[1]
    results.append((
        f"notes not empty or bloated ({len(notes)} notes; expected {note_range[0]}-{note_range[1]})",
        5 if notes_in_range else 0,
        5,
    ))

    total = sum(result[1] for result in results)
    critical_ok = not missing_ingredients and not missing_passages and not forbidden_hits
    print("--- RESULT ---")
    for label, earned, possible in results:
        print(f"[{'OK' if earned == possible else '..'}] {earned:5.1f}/{possible:<3} {label}")
    if not critical_ok:
        print("\nCRITICAL FAIL: the latest reply is incomplete or contains extra ingredients.")
    print(f"\nSCORE: {total:.0f}/100")
    sys.exit(0 if total >= 80 and critical_ok else 1)


if __name__ == "__main__":
    main()
