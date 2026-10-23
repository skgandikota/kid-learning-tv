"""Speech input adapter contract; core play never requires speech recognition."""


class InputAdapter:
    name = "manual-parent-assist"

    def available(self) -> bool:
        return True

    def submit(self, text: str):
        return text
