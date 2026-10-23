# Game modules

Game logic is implemented in `app/games/`; presentation and controls are served through the browser app.

## Avocado

`AvocadoGame` selects unused answers from the chosen content category, normalizes manual text input, recognizes names/aliases/plural variants, and requests confirmation for sufficiently close matches. Repeated answers are reported; retry counts and optional nicknames are local game settings. It does not perform speech recognition.

## Memory Chain

`MemoryGame` extends a sequence from a local memory category. Levels define sequence bounds and whether pictures are initially visible. The child enters the remembered sequence manually; retry behavior and round completion are managed locally.

## Activities and events

Prompt activities are loaded from `content/activities/prompts.json`. Event constants live in `app/games/base.py`; `app/events/bus.py` publishes bounded in-process updates used by the UI and parent controls. The project also includes simulated Ask Rocky behavior; it is not an Alexa connection.

This is a description of the current modules, not a guarantee of a stable external game plugin API.
