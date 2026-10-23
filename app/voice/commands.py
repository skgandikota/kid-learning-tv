"""Turn-specific English vocabulary and voice intents."""
from __future__ import annotations

from app.games.avocado import normalize


HOME_COMMANDS = {
    "avocado": ("start_avocado", None),
    "play avocado": ("start_avocado", None),
    "memory": ("start_memory", None),
    "memory chain": ("start_memory", None),
    "play memory": ("start_memory", None),
    "ask rocky": ("rocky_request", None),
    "rocky": ("rocky_request", None),
    "letters": ("activity", "letter-b"),
    "numbers": ("activity", "count-blue-blocks"),
    "colours": ("activity", "find-yellow"),
    "colors": ("activity", "find-yellow"),
    "animals": ("activity", "animal-fact"),
    "story": ("activity", "story-time"),
    "music": ("activity", "clap-five"),
}
NUMBERS = dict(zip(("one", "two", "three", "four", "five"), ("1", "2", "3", "4", "5")))


def memory_items(text: str, items: list[str]):
    """Parse spoken lists using longest vocabulary matches, without guessing."""
    tokens = normalize(text).split()
    labels = sorted(((normalize(item).split(), item) for item in items), key=lambda entry: -len(entry[0]))
    filler = {"and", "a", "an", "the", "i", "went", "to", "shop", "bought"}
    result = []
    index = 0
    while index < len(tokens):
        for words, item in labels:
            if tokens[index:index + len(words)] == words:
                result.append(item)
                index += len(words)
                break
        else:
            if tokens[index] not in filler:
                raise ValueError("I didn't quite hear that list. Say the items once more.")
            index += 1
    if not result:
        raise ValueError("Say the items in your list once more.")
    return result


def vocabulary(runtime):
    state = runtime.state
    if state["locked"] or state["paused"] or state.get("break_mode"):
        return []
    if state["screen"] == "home" and not runtime.learning_game:
        return list(HOME_COMMANDS)
    if state["screen"] == "learning" and runtime.learning_game:
        game = runtime.learning_game
        if game.completed or game.activity_id == "matching-pairs":
            return []
        return list(NUMBERS) if game.activity_id == "count-objects" else list(game.options)
    if state["game_state"] == "confirmation" and runtime.avocado:
        return ["yes", "no", "yes please", "no thank you"]
    if state["screen"] == "avocado" and state["game_state"] == "child_turn" and runtime.avocado:
        labels = []
        for item in runtime.avocado.entries:
            labels.extend([item["name"], *item.get("aliases", []), *item.get("pronunciation", [])])
        return [normalize(item) for item in labels]
    if state["screen"] == "memory" and state["game_state"] == "child_turn" and runtime.memory:
        return [normalize(item) for item in runtime.memory.category["items"]] + ["and", "i went to the shop and bought"]
    if state["screen"] in {"activity", "round-complete", "nickname"} and not runtime.learning_game:
        return ["home", "go home", "avocado", "memory"]
    return []
