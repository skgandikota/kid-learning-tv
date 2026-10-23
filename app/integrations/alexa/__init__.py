"""Alexa is a disabled placeholder; no network listener or credentials are used."""


class AlexaAdapter:
    enabled = False

    def handle_event(self, event: dict) -> dict:
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError("An Alexa event must contain a string type.")
        return {"accepted": False, "reason": "Alexa integration is disabled."}
