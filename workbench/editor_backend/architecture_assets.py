"""Read-only architecture assets shared with the installed Vivid skill."""
import os
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]

def architecture_root():
    configured = os.environ.get('VIVID_ARCHITECTURE_ROOT')
    if configured:
        return Path(configured).expanduser().resolve()
    bundled = WEB.parent / 'architecture'
    if (bundled / 'catalog.json').is_file():
        return bundled.resolve()
    skills = Path.home() / '.codex/skills'
    installed = skills / 'vivid-illustration-skill/architecture'
    legacy = skills / 'vivid-figures-skill/architecture'
    if not (installed / 'catalog.json').is_file() and (legacy / 'catalog.json').is_file():
        return legacy.resolve()
    return installed.resolve()

def architecture_file(relative):
    root = architecture_root()
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise FileNotFoundError('Architecture resource unavailable')
    return target
