"""Short, untimed picture adventures with server-owned turns."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from itertools import combinations
import random
import uuid

from app.quiz_catalog import get_items


def icon(item_id, name, image):
    return {"id": item_id, "name": name, "image": image}


ART = {
    item["id"]: item for category in ("animals", "fruits", "vegetables", "birds")
    for item in get_items(category)
}
for name in ("Cup", "Book", "Ball", "Eye", "Mouth", "Arm", "Leg"):
    ART[name.lower()] = icon(name.lower(), name, f"/static/images/typing-{name.lower()}.svg")
for name in ("Circle", "Square", "Triangle", "Rectangle", "Monster", "Vehicle", "Bag", "Robot", "Adventure"):
    ART[name.lower()] = icon(name.lower(), name, f"/static/images/adventure-{name.lower()}.svg")

GAMES = (
    {"id": "rescue", "name": "Hero Rescue", "image": ART["dog"]["image"]},
    {"id": "monster", "name": "Feed the Monster", "image": ART["monster"]["image"]},
    {"id": "vehicle", "name": "Build a Hero Vehicle", "image": ART["vehicle"]["image"]},
    {"id": "hiding", "name": "Who's Hiding?", "image": ART["rabbit"]["image"]},
    {"id": "bag", "name": "Pack the Adventure Bag", "image": ART["bag"]["image"]},
    {"id": "path", "name": "Finish the Magic Path", "image": ART["adventure"]["image"]},
    {"id": "robot", "name": "Silly Body Robot", "image": ART["robot"]["image"]},
)
GAME_IDS = tuple(item["id"] for item in GAMES)
NUMBERS = ("Zero", "One", "Two", "Three", "Four", "Five")


def default_settings():
    return {"enabled": list(GAME_IDS), "rescue_max": 3, "bag_size": 2, "spoken": True}


def validate_settings(value):
    if not isinstance(value, dict) or set(value) != {"enabled", "rescue_max", "bag_size", "spoken"}:
        raise ValueError("Choose valid adventure settings.")
    enabled = value["enabled"]
    if not isinstance(enabled, list) or not all(isinstance(item, str) and item in GAME_IDS for item in enabled):
        raise ValueError("Choose games from the adventure list.")
    if len(set(enabled)) != len(enabled):
        raise ValueError("Choose each game only once.")
    if type(value["rescue_max"]) is not int or value["rescue_max"] not in (3, 5):
        raise ValueError("Counting can go up to three or five.")
    if type(value["bag_size"]) is not int or value["bag_size"] not in (2, 3):
        raise ValueError("Remember two or three items.")
    if type(value["spoken"]) is not bool:
        raise ValueError("Choose whether spoken instructions are on.")
    return deepcopy(value)


def task(prompt, choices, target, success, *, quantity=1, **details):
    return {
        "prompt": prompt, "choices": choices, "target": target,
        "success": success, "quantity": quantity, **details,
    }


PLANS = {
    "rescue": [
        task(f"Rescue {NUMBERS[n].lower()} {'puppy' if n == 1 else 'puppies'}. Click each puppy to help!",
             [f"puppy-{i}" for i in range(5)], "puppy", f"You rescued {NUMBERS[n].lower()} {'puppy' if n == 1 else 'puppies'}!",
             quantity=n) for n in range(1, 6)
    ],
    "monster": [
        task("I'm hungry! Feed me something red.", ["apple", "banana", "broccoli"], "apple", "A red apple! Yum!"),
        task("Feed me something yellow.", ["banana", "grapes", "tomato"], "banana", "A yellow banana! Yum!"),
        task("Feed me something green.", ["broccoli", "strawberry", "orange"], "broccoli", "Green broccoli! Crunch!"),
        task("Feed me a fruit.", ["pear", "carrot", "potato"], "pear", "A pear is a fruit! Yum!"),
        task("Feed me a vegetable.", ["carrot", "apple", "banana"], "carrot", "A carrot is a vegetable! Crunch!"),
    ],
    "vehicle": [
        task("Find a circle for our wheels.", ["circle", "square", "triangle"], "circle", "Round wheels!"),
        task("Find a rectangle for the vehicle body.", ["rectangle", "triangle", "circle"], "rectangle", "A rectangle body!"),
        task("Find a square for the window.", ["square", "rectangle", "circle"], "square", "A square window!"),
        task("Find a triangle for our flag.", ["triangle", "square", "circle"], "triangle", "A triangle flag! Ready to drive!"),
    ],
    "hiding": [
        task("I have long ears. Who is hiding?", ["rabbit", "cat", "cow"], "rabbit", "A rabbit! Look at those long ears!", clue="rabbit"),
        task("I have a long trunk. Who is hiding?", ["elephant", "dog", "lion"], "elephant", "An elephant! What a long trunk!", clue="elephant"),
        task("I say meow. Who is hiding?", ["cat", "dog", "pig"], "cat", "A cat! Meow!", clue="cat"),
        task("I have a big mane. Who is hiding?", ["lion", "rabbit", "cow"], "lion", "A lion! What a lovely mane!", clue="lion"),
        task("I say moo. Who is hiding?", ["cow", "cat", "elephant"], "cow", "A cow! Moo!", clue="cow"),
    ],
    "path": [
        task("Apple, banana, apple, banana. What comes next?", ["apple", "banana", "grapes"], "apple", "Apple! The pattern repeats!", sequence=["apple", "banana", "apple", "banana"]),
        task("Cat, dog, cat, dog. What comes next?", ["dog", "cat", "rabbit"], "cat", "Cat! The pattern repeats!", sequence=["cat", "dog", "cat", "dog"]),
        task("Circle, square, circle, square. What comes next?", ["square", "triangle", "circle"], "circle", "Circle! The pattern repeats!", sequence=["circle", "square", "circle", "square"]),
        task("Banana, apple, banana, apple. What comes next?", ["banana", "apple", "orange"], "banana", "Banana! You found the pattern!", sequence=["banana", "apple", "banana", "apple"]),
        task("Duck, duck, rabbit, duck, duck. What comes next?", ["duck", "rabbit", "cat"], "rabbit", "Rabbit! Two ducks, then a rabbit!", sequence=["duck", "duck", "rabbit", "duck", "duck"]),
    ],
    "robot": [
        task("Give the robot two eyes. Click the eye twice.", ["eye", "mouth", "leg"], "eye", "Two eyes! I can see!", quantity=2),
        task("Give the robot one mouth.", ["mouth", "arm", "eye"], "mouth", "One mouth! Hello, friend!"),
        task("Give the robot two arms. Click the arm twice.", ["arm", "eye", "leg"], "arm", "Two arms! Wave hello!", quantity=2),
        task("Give the robot two legs. Click the leg twice.", ["leg", "mouth", "arm"], "leg", "Two legs! Let's do a silly dance!", quantity=2),
    ],
}
BAG_ITEMS = ("apple", "cup", "book", "ball", "banana", "carrot")
BAG_PLANS = {
    size: [
        task("Remember: " + ", ".join(ART[item]["name"].lower() for item in group) + ". Look carefully, then pack the bag!",
             list(BAG_ITEMS), list(group), "Everything is packed! Ready for our adventure!",
             quantity=size, memory=list(group))
        for group in combinations(BAG_ITEMS, size)
    ] for size in (2, 3)
}
HINT = "Let's try another picture. You can do it!"
PACK = "Now pack the bag. Which things did we need?"
FINISH = "Lovely playing! You did it!"
TEXTS = {
    text for tasks in [*PLANS.values(), *BAG_PLANS.values()] for item in tasks
    for text in (item["prompt"], item["success"])
} | {HINT, PACK, FINISH, *NUMBERS[1:]}
AUDIO = {
    hashlib.sha256(text.encode()).hexdigest()[:20]:
    " ".join(text.translate(str.maketrans(".,!?:", "     ")).split())
    for text in TEXTS
}


def audio_key(text):
    return hashlib.sha256(text.encode()).hexdigest()[:20]


class AdventureGame:
    def __init__(self, game_id, settings):
        if game_id not in GAME_IDS or game_id not in settings["enabled"]:
            raise ValueError("That adventure is not enabled. Choose another game.")
        self.id = game_id
        self.name = next(game["name"] for game in GAMES if game["id"] == game_id)
        self.spoken = settings["spoken"]
        self.tasks = deepcopy(
            random.sample(BAG_PLANS[settings["bag_size"]], 4) if game_id == "bag"
            else PLANS[game_id][:settings["rescue_max"]] if game_id == "rescue"
            else PLANS[game_id]
        )
        if game_id in {"monster", "hiding"}:
            random.shuffle(self.tasks)
        for item in self.tasks:
            random.shuffle(item["choices"])
        self.index = 0
        self.picked = []
        self.token = uuid.uuid4().hex
        self.phase = "preview" if game_id == "bag" else "play"

    @property
    def current(self):
        return self.tasks[self.index]

    def command(self, action, token, choice=None):
        if token != self.token:
            raise ValueError("That adventure turn has changed. Try the current picture.")
        if action == "next":
            if self.phase != "success":
                raise ValueError("Finish this little adventure first.")
            if self.index + 1 == len(self.tasks):
                self.phase = "finished"
            else:
                self.index += 1
                self.picked = []
                self.phase = "preview" if self.id == "bag" else "play"
            self.token = uuid.uuid4().hex
            return None
        if action == "remember" and self.id == "bag" and self.phase == "play":
            self.picked = []
            self.phase = "preview"
        elif action == "ready" and self.phase == "preview":
            self.phase = "play"
        elif action == "pick" and self.phase == "play":
            item = self.current
            if not isinstance(choice, str) or choice not in item["choices"]:
                raise ValueError("Choose one of these pictures.")
            if self.id in {"rescue", "bag"} and choice in self.picked:
                raise ValueError("That picture is already safe. Choose another.")
            correct = choice.startswith("puppy-") if self.id == "rescue" else (
                choice in item["target"] if self.id == "bag" else choice == item["target"]
            )
            if not correct:
                return HINT
            self.picked.append(choice)
            if len(self.picked) == item["quantity"]:
                self.phase = "success"
            self.token = uuid.uuid4().hex
            return item["success"] if self.phase == "success" else NUMBERS[len(self.picked)]
        else:
            raise ValueError("Choose a picture or an adventure control.")
        self.token = uuid.uuid4().hex
        return None

    def snapshot(self):
        item = self.current
        prompt = FINISH if self.phase == "finished" else (
            item["success"] if self.phase == "success" else
            PACK if self.id == "bag" and self.phase == "play" else item["prompt"]
        )
        choices = [
            {**ART["dog" if key.startswith("puppy-") else key], "id": key,
             "name": "Puppy" if key.startswith("puppy-") else ART[key]["name"],
             "picked": key in self.picked and self.id in {"bag", "rescue"}}
            for key in item["choices"]
        ]
        built = {}
        if self.id in {"vehicle", "robot"}:
            built = {task["target"]: task["quantity"] for task in self.tasks[:self.index]}
            if self.picked:
                built[item["target"]] = len(self.picked)
        return {
            "id": self.id, "name": self.name, "token": self.token,
            "index": self.index, "phase": self.phase, "spoken": self.spoken,
            "prompt": prompt, "audio": audio_key(prompt), "choices": choices,
            "collected": len(self.picked), "quantity": item["quantity"],
            "last_choice": self.picked[-1] if self.picked else None,
            "sequence": [ART[key] for key in item.get("sequence", [])],
            "memory": [ART[key] for key in item.get("memory", [])] if self.phase == "preview" else [],
            "clue": ART[item["clue"]] if "clue" in item else None,
            "built": built,
        }
