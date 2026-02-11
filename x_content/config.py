"""YAML configuration loader."""

from pathlib import Path
from typing import Optional

import yaml


_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
_config: Optional[dict] = None

_DEFAULT_CONFIG: dict = {
    "claude": {
        "timeout": 120,
        "output_format": "json",
    },
    "optimization": {
        "variations": 3,
        "style": "professional",
        "lang": "auto",
        "max_chars": 280,
    },
    "display": {
        "bar_width": 24,
        "show_all_signals": False,
        "top_signals_count": 8,
    },
}


def load_config() -> dict:
    """Load and cache config.yaml with fallback to defaults."""
    global _config
    if _config is None:
        try:
            with open(_CONFIG_PATH) as f:
                _config = yaml.safe_load(f) or {}
        except (FileNotFoundError, PermissionError, yaml.YAMLError):
            _config = {}
        for key, value in _DEFAULT_CONFIG.items():
            if key not in _config:
                _config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    _config[key].setdefault(subkey, subvalue)
    return _config


def get(key: str, default=None):
    """Get a top-level config value."""
    return load_config().get(key, default)
