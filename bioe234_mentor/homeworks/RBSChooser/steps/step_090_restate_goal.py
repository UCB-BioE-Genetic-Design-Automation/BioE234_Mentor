from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "090"
KEY = "RESTATE_GOAL"
TITLE = "Project overview and download data"
NEXT_STEP = "100"
HASH_MODE = "json"


def render(state: Dict[str, Any]) -> str:
    return (
        "We are now transitioning from LLM workflow skills to building RBSChooser2.\n\n"
        "# Selection of Ribosome Binding Sites (RBS)\n"
        "This project guides you through the synthetic biology challenge of selecting an RBS that effectively expresses a foreign gene. "
        "Using raw experimental data and AI assistance, you will create an RBSChooser function that processes genetic data to predict well expressing transcripts.\n\n"
        "### Learning Objectives\n"
        "* Understand synthetic biology principles related to RBS functionality.\n"
        "* Learn to tackle genomics and proteomics problems.\n"
        "* Utilize an LLM for coding assistance and script refinement.\n"
        "* Apply the function as object pattern for efficient data preprocessing.\n"
        "* Engage in a multi objective optimization problem.\n\n"
        "# Implementing initiate\n\n"
        "The central insights behind our implementation of RBSChooser are:\n\n"
        "1. Naturally occurring 5' UTR sequences are evolutionarily optimized to work.\n"
        "2. Proteomics data can empirically define strongly expressing genes.\n"
        "3. A primary source of failure can be anticipated with secondary structure prediction.\n\n"
        "For this approach, we will use gene sequences and proteomics data from E. coli K12 isolate MG1655.\n\n"
        "## Download the source data\n"
        "Run the following code in the next code cell:\n\n"
        "```python\n"
        "# Install gdown if not already installed\n"
        "!pip install -q gdown\n\n"
        "file_urls = [\n"
        "    'https://drive.google.com/uc?id=1U7AKYm2n0O1KDOdcYcJCYvrZQw5Ul_TZ',\n"
        "    'https://drive.google.com/uc?id=1gALv5ZIoWCXWGk4U93pAiJUwbwTCCti6'\n"
        "]\n\n"
        "for url in file_urls:\n"
        "    !gdown {url}\n"
        "```\n\n"
        "After the downloads finish, run `!ls -1` and submit the two downloaded file names as a comma separated string.\n\n"
        "Submission (copy and edit):\n"
        "```python\n"
        "mentor.submit_display('RESTATE_GOAL', 'FILE1,FILE2')\n"
        "```"
    )


def shape_check(answer: Any) -> Tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "Submit the two downloaded file names as a comma separated string."

    parts = [p.strip() for p in answer.split(",") if p.strip()]
    if len(parts) != 2:
        return False, "Submit exactly two file names, separated by a single comma."

    return True, ""


def validate(answer: Any, state: Dict[str, Any]):
    from pathlib import Path

    parts = [p.strip() for p in str(answer).split(",") if p.strip()]

    missing = [name for name in parts if not Path(name).exists()]
    if missing:
        return False, f"I could not find these file(s) in the notebook runtime: {', '.join(missing)}", {
            "submitted": parts,
            "cwd": str(Path.cwd()),
        }

    return True, "Downloads found. Proceeding.", {
        "files": parts,
    }
