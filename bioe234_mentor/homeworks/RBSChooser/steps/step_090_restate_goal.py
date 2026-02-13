from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "090"
KEY = "RESTATE_GOAL"
TITLE = "Project overview and download data"
NEXT_STEP = "100"
HASH_MODE = "json"
SUBMIT_STUB = "mentor.submit_display('RESTATE_GOAL', 'PUT_THE_TXT_FILENAME_HERE')"


def render(state: Dict[str, Any]) -> str:
    return (
        "In the previous exchange we showed how you can use the LLM to analyze and discuss the logical content of the function. "
        "For the remainder of this tutorial, I will describe the behavior the function should have that you will turn in as your last submit_display call.\n\n"
        "It starts with two data files found through Google searches:\n"
        "• proteomics dataset: found by browsing the PAX-db website and clicking the download button: https://pax-db.org/dataset/511145/2297923011. "
        "This data quantifies which genes in the cell give rise to the most protein, and we will use it to identify a subset of highly expressed genes.\n"
        "• mg1655 genome: Downloaded genome sequence for MG1655 from https://www.ncbi.nlm.nih.gov/nuccore/U00096.2. "
        "We will use that sequence to pull out the native rbs and cds for these highly expressed genes.\n\n"
        "I uploaded the two files to Google Drive. In the block below, download both files from the drive into Colab. "
        "For your submission, submit the file name of the txt file (the proteomics data).\n\n"
        "```python\n"
        "!pip install -q gdown\n"
        "file_urls = [\n"
        "  'https://drive.google.com/uc?id=1U7AKYm2n0O1KDOdcYcJCYvrZQw5Ul_TZ',\n"
        "  'https://drive.google.com/uc?id=1gALv5ZIoWCXWGk4U93pAiJUwbwTCCti6'\n"
        "]\n"
        "for url in file_urls:\n"
        "  !gdown {url}\n"
        "```\n\n"
        "After the downloads finish, click the folder icon on the left sidebar (Files) and look for the downloaded TXT file. "
        "Submit the exact name of the proteomics TXT file."
    )


def shape_check(answer: Any) -> Tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "Submit the exact name of the downloaded proteomics TXT file."

    name = answer.strip()
    if name != "511145-WHOLE_ORGANISM-integrated.txt":
        return False, "Submit the exact filename."

    return True, ""


def validate(answer: Any, state: Dict[str, Any]):
    from pathlib import Path

    name = str(answer).strip()

    expected = "511145-WHOLE_ORGANISM-integrated.txt"
    if name != expected:
        return False, f"Submit the exact filename.", {}

    if not Path(expected).exists():
        return False, (
            "I could not find the expected TXT file in the notebook runtime. "
            "Make sure the download cell ran successfully and the file appears in the Colab Files panel."
        ), {
            "expected": expected,
            "cwd": str(Path.cwd()),
        }

    return True, "Downloads found. Proceeding.", {
        "file": expected,
    }
