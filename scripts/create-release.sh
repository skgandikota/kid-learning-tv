#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
cd "$SOURCE_DIR"
PYTHONPATH="$SOURCE_DIR" python3 tools/content_validator.py
tag="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
[[ "$tag" =~ ^[A-Za-z0-9._-]+$ ]] || die "Release label may contain only letters, numbers, dot, underscore, or hyphen."
out="${KLT_RELEASE_DIR:-$SOURCE_DIR/releases}"
install -d -m 0755 "$out"
archive="$out/kid-learning-tv-$tag.tar.gz"
[[ ! -e "$archive" ]] || die "Refusing to overwrite $archive."
tar -czf "$archive" --exclude='./.venv' --exclude='./var' --exclude='./releases' \
    --exclude='./.git' --exclude='./__pycache__' app config content tools scripts systemd kiosk docs \
    pyproject.toml requirements.lock README.md 2>/dev/null || die "Release package failed; check the project files."
info "Release archive created: $archive"
