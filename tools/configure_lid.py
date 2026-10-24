"""Disable LXQt lid actions without changing critical-battery protection."""
from __future__ import annotations

import configparser
from pathlib import Path
import shutil
import sys


def configure_lid(path: Path):
    settings = configparser.ConfigParser(interpolation=None, delimiters=("=",))
    settings.optionxform = str
    if path.exists():
        with path.open(encoding="utf-8") as source:
            settings.read_file(source)
    if not settings.has_section("General"):
        settings.add_section("General")
    settings["General"].update({
        "enableLidWatcher": "true",
        "lidClosedAction": "-1",
        "lidClosedAcAction": "-1",
        "lidClosedExtMonAction": "-1",
        "lidClosedExtMonAcAction": "-1",
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_name(path.name + ".before-klt-lid")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        settings.write(output, space_around_delimiters=False)
    print(f"LXQt lid actions disabled in {path}. Other power settings are unchanged.")
    if backup.exists():
        print(f"Original settings: {backup}")


if __name__ == "__main__":
    configure_lid(Path(sys.argv[1]))
