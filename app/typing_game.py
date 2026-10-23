"""Curated sound groups: letters such as SH are sounded together, not guessed by TTS."""
from __future__ import annotations

import uuid

from app.quiz_catalog import get_items


def lesson(name, groups, *, category="heroes", picture=None, blend=True):
    parts = [{"letters": letters.upper(), "sound": sound} for letters, sound in groups]
    word = name.upper()
    if "".join(part["letters"] for part in parts) != word.replace(" ", ""):
        raise ValueError(f"Sound groups do not spell {name}.")
    item_id = name.lower().replace(" ", "-")
    return {
        "id": item_id, "name": name, "word": word,
        "category": category, "groups": parts, "blend": blend,
        "image": picture or f"/static/images/typing-{item_id}.png",
    }


# eSpeak NG's English phoneme mnemonics, with word-specific vowels and digraphs.
LESSONS = [
    lesson("Flash", [("f", "f"), ("l", "l"), ("a", "a"), ("sh", "S")]),
    lesson("Batman", [("b", "b"), ("a", "a"), ("t", "t"), ("m", "m"), ("a", "a"), ("n", "n")]),
    lesson("Superman", [("s", "s"), ("u", "u:"), ("p", "p"), ("er", "3:"), ("m", "m"), ("a", "a"), ("n", "n")], blend=False),
    lesson("Wonder Woman", [("w", "w"), ("o", "V"), ("n", "n"), ("d", "d"), ("er", "@"), ("w", "w"), ("o", "U"), ("m", "m"), ("a", "@"), ("n", "n")], blend=False),
    lesson("Robin", [("r", "r"), ("o", "0"), ("b", "b"), ("i", "I"), ("n", "n")]),
    lesson("Aquaman", [("a", "a"), ("qu", "kw"), ("a", "@"), ("m", "m"), ("a", "a"), ("n", "n")], blend=False),
    lesson("Iron Man", [("iron", "aI@n"), ("m", "m"), ("a", "a"), ("n", "n")], blend=False),
    lesson("Captain America", [("c", "k"), ("a", "a"), ("p", "p"), ("t", "t"), ("ai", "I"), ("n", "n"), ("a", "@"), ("m", "m"), ("e", "E"), ("r", "r"), ("i", "I"), ("c", "k"), ("a", "@")], blend=False),
    lesson("Thor", [("th", "T"), ("or", "O:")]),
    lesson("Hulk", [("h", "h"), ("u", "V"), ("l", "l"), ("k", "k")]),
    lesson("Black Widow", [("b", "b"), ("l", "l"), ("a", "a"), ("ck", "k"), ("w", "w"), ("i", "I"), ("d", "d"), ("ow", "@U")], blend=False),
    lesson("Hawkeye", [("h", "h"), ("aw", "O:"), ("k", "k"), ("eye", "aI")], blend=False),
    lesson("Spider Man", [("s", "s"), ("p", "p"), ("i", "aI"), ("d", "d"), ("er", "@"), ("m", "m"), ("a", "a"), ("n", "n")], blend=False),
    lesson("Black Panther", [("b", "b"), ("l", "l"), ("a", "a"), ("ck", "k"), ("p", "p"), ("a", "a"), ("n", "n"), ("th", "T"), ("er", "@")], blend=False),
    lesson("Ant Man", [("a", "a"), ("n", "n"), ("t", "t"), ("m", "m"), ("a", "a"), ("n", "n")]),
    lesson("Wasp", [("w", "w"), ("a", "0"), ("s", "s"), ("p", "p")]),
    lesson("Vision", [("v", "v"), ("i", "I"), ("si", "Z"), ("o", "@"), ("n", "n")], blend=False),
    lesson("Scarlet Witch", [("s", "s"), ("c", "k"), ("ar", "A:"), ("l", "l"), ("e", "@"), ("t", "t"), ("w", "w"), ("i", "I"), ("tch", "tS")], blend=False),
    lesson("Doctor Strange", [("d", "d"), ("o", "0"), ("c", "k"), ("t", "t"), ("or", "@"), ("s", "s"), ("t", "t"), ("r", "r"), ("a", "eI"), ("n", "n"), ("ge", "dZ")], blend=False),
    lesson("Captain Marvel", [("c", "k"), ("a", "a"), ("p", "p"), ("t", "t"), ("ai", "I"), ("n", "n"), ("m", "m"), ("ar", "A:"), ("v", "v"), ("e", "@"), ("l", "l")], blend=False),
    lesson("Falcon", [("f", "f"), ("a", "O:"), ("l", "l"), ("c", "k"), ("o", "@"), ("n", "n")], blend=False),
    lesson("Thanos", [("th", "T"), ("a", "a"), ("n", "n"), ("o", "0"), ("s", "s")]),
    lesson("Joker", [("j", "dZ"), ("o", "@U"), ("k", "k"), ("er", "@")], blend=False),
    lesson("Venom", [("v", "v"), ("e", "E"), ("n", "n"), ("o", "@"), ("m", "m")], blend=False),
    lesson("Woody", [("w", "w"), ("oo", "U"), ("d", "d"), ("y", "i")]),
    lesson("Buzz Lightyear", [("b", "b"), ("u", "V"), ("zz", "z"), ("l", "l"), ("igh", "aI"), ("t", "t"), ("y", "j"), ("ear", "i@")], blend=False),
]


def picture(category, item_id):
    return next(item["image"] for item in get_items(category) if item["id"] == item_id)


for name, groups, image in [
    ("Ant", [("a", "a"), ("n", "n"), ("t", "t")], "/static/images/typing-ant.svg"),
    ("Apple", [("a", "a"), ("pp", "p"), ("le", "@l")], picture("fruits", "apple")),
    ("Cat", [("c", "k"), ("a", "a"), ("t", "t")], picture("animals", "cat")),
    ("Dog", [("d", "d"), ("o", "0"), ("g", "g")], picture("animals", "dog")),
    ("Pig", [("p", "p"), ("i", "I"), ("g", "g")], picture("animals", "pig")),
    ("Hen", [("h", "h"), ("e", "E"), ("n", "n")], picture("birds", "chicken")),
    ("Duck", [("d", "d"), ("u", "V"), ("ck", "k")], picture("birds", "duck")),
    ("Fish", [("f", "f"), ("i", "I"), ("sh", "S")], "/static/images/typing-fish.svg"),
]:
    LESSONS.append(lesson(name, groups, category="words", picture=image))

for name, groups, blend in [
    ("Table", [("t", "t"), ("a", "eI"), ("b", "b"), ("le", "@l")], False),
    ("Chair", [("ch", "tS"), ("air", "e@")], True),
    ("Bed", [("b", "b"), ("e", "E"), ("d", "d")], True),
    ("Cup", [("c", "k"), ("u", "V"), ("p", "p")], True),
    ("Book", [("b", "b"), ("oo", "U"), ("k", "k")], True),
    ("Ball", [("b", "b"), ("a", "O:"), ("ll", "l")], True),
    ("Head", [("h", "h"), ("ea", "E"), ("d", "d")], True),
    ("Hair", [("h", "h"), ("air", "e@")], True),
    ("Eye", [("eye", "aI")], False),
    ("Ear", [("ear", "i@")], False),
    ("Nose", [("n", "n"), ("ose", "@Uz")], False),
    ("Mouth", [("m", "m"), ("ou", "aU"), ("th", "T")], True),
    ("Tooth", [("t", "t"), ("oo", "u:"), ("th", "T")], True),
    ("Hand", [("h", "h"), ("a", "a"), ("n", "n"), ("d", "d")], True),
    ("Foot", [("f", "f"), ("oo", "U"), ("t", "t")], True),
    ("Arm", [("ar", "A:"), ("m", "m")], True),
    ("Leg", [("l", "l"), ("e", "E"), ("g", "g")], True),
]:
    LESSONS.append(lesson(
        name, groups, category="words", blend=blend,
        picture=f"/static/images/typing-{name.lower()}.svg",
    ))


def get_lesson(item_id):
    item = next((item for item in LESSONS if item["id"] == item_id), None)
    if item is None:
        raise ValueError("Choose a name from Hero Typing.")
    return item


def sound_step(item, position):
    """Return the group only when its final letter has been typed."""
    end = 0
    for index, group in enumerate(item["groups"]):
        end += len(group["letters"])
        if end == position:
            return {
                "group": group, "sound": group["sound"],
                "blend": "".join(part["sound"] for part in item["groups"][:index + 1])
                if item["blend"] and index > 0 else None,
            }
    return None


class TypingGame:
    def __init__(self, item_id):
        self.item = get_lesson(item_id)
        self.token = uuid.uuid4().hex
        self.position = 0

    def type_key(self, token, position, key):
        if token != self.token or type(position) is not int or position != self.position:
            raise ValueError("That typing turn has changed. Try the highlighted letter.")
        if not isinstance(key, str) or len(key) != 1 or not key.isascii() or not key.isalpha():
            raise ValueError("Press one letter key.")
        target = self.item["word"].replace(" ", "")
        if self.position >= len(target):
            raise ValueError("This name is finished. Choose Next.")
        if key.upper() != target[self.position]:
            return False
        self.position += 1
        return True

    def snapshot(self):
        item = {key: value for key, value in self.item.items() if key != "groups"}
        item["groups"] = [part["letters"] for part in self.item["groups"]]
        return {
            "token": self.token, "position": self.position, "item": item,
            "complete": self.position == len(self.item["word"].replace(" ", "")),
        }
