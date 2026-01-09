from pathlib import Path

HOMEWORK_SLUG = "RBSChooser"
TITLE = "RBS Chooser"


def steps_dir() -> Path:
    return Path(__file__).resolve().parent / "steps"


def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"
