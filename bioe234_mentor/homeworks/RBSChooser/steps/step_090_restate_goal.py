from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "090"
KEY = "RESTATE_GOAL"
TITLE = "Project overview and download data"
NEXT_STEP = "100"
HASH_MODE = "json"
SUBMIT_STUB = "mentor.submit_display('RESTATE_GOAL', 'FILE1,FILE2')"


def render(state: Dict[str, Any]) -> str:
    return (
        "<p>We are now transitioning from LLM workflow skills to building RBSChooser2.</p>"
        "<h2>Selection of Ribosome Binding Sites (RBS)</h2>"
        "<p>"
        "This project guides you through the synthetic biology challenge of selecting an RBS that effectively expresses a foreign gene. "
        "Using raw experimental data and AI assistance, you will create an RBSChooser function that processes genetic data to predict well expressing transcripts."
        "</p>"
        "<h3>Learning Objectives</h3>"
        "<ul>"
        "<li>Understand synthetic biology principles related to RBS functionality.</li>"
        "<li>Learn to tackle genomics and proteomics problems.</li>"
        "<li>Utilize an LLM for coding assistance and script refinement.</li>"
        "<li>Apply the function as object pattern for efficient data preprocessing.</li>"
        "<li>Engage in a multi objective optimization problem.</li>"
        "</ul>"
        "<h2>Implementing initiate</h2>"
        "<p>The central insights behind our implementation of RBSChooser are:</p>"
        "<ol>"
        "<li>Naturally occurring 5' UTR sequences are evolutionarily optimized to work.</li>"
        "<li>Proteomics data can empirically define strongly expressing genes.</li>"
        "<li>A primary source of failure can be anticipated with secondary structure prediction.</li>"
        "</ol>"
        "<p>For this approach, we will use gene sequences and proteomics data from E. coli K12 isolate MG1655.</p>"
        "<h2>Download the source data</h2>"
        "<p>Run the following code in the next code cell:</p>"
        "<pre><code>"
        "# Install gdown if not already installed\n"
        "!pip install -q gdown\n\n"
        "file_urls = [\n"
        "    'https://drive.google.com/uc?id=1U7AKYm2n0O1KDOdcYcJCYvrZQw5Ul_TZ',\n"
        "    'https://drive.google.com/uc?id=1gALv5ZIoWCXWGk4U93pAiJUwbwTCCti6'\n"
        "]\n\n"
        "for url in file_urls:\n"
        "    !gdown {url}\n"
        "</code></pre>"
        "<p>After the downloads finish, run <code>!ls -1</code> and submit the two downloaded file names as a comma separated string.</p>"
        "<p><b>Submission (copy and edit):</b></p>"
        "<pre><code>"
        "mentor.submit_display('RESTATE_GOAL', 'FILE1,FILE2')\n"
        "</code></pre>"
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
