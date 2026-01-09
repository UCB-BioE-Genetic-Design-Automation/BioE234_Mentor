

# RBSChooser homework

## What students learn

This homework introduces a workflow for using an LLM to help write code while staying in control of the result.

Students learn to:
- Write prompts that are specific enough to avoid accidental requirements and arbitrary outputs
- Notice that an LLM will invent function interfaces unless you explicitly define them
- Extract and describe a function signature (name, inputs, outputs) and understand why signatures matter for program architecture
- Recognize non-determinism and test for it with a simple experiment
- Begin thinking about correctness as properties that can be checked, not as "it looks reasonable"

The later parts of the homework build toward an RBS chooser implementation, but the early exchanges focus on general skills for LLM-assisted coding.

## How the tutorial works

The tutorial runs one step at a time inside a Google Colab notebook.

- The student runs `mentor.display()` to see the current instruction.
- Each step shows exactly what to run next using `mentor.submit_display(KEY, answer)`.
- The mentor records submissions in a local JSON state file in the notebook runtime.
- Some steps validate only the shape of the answer, while others check a small correctness condition.

Students use Gemini in a separate browser tab. The student copy/pastes prompts into Gemini, then copy/pastes results back into Colab for submission.

## Exchanges and flow

The exchange scripts live in `bioe234_mentor/homeworks/RBSChooser/steps/`.

### step_010_passcode

Collect the student passcode and validate it against a whitelist.

### step_020_open_gemini

Have the student open Gemini, paste a Gemini chat URL to confirm they are in the right place, and share the Colab notebook.

### step_030_abstract_prompt

Demonstrate that vague prompts lead to arbitrary choices. The student uses a simple, generic prompt and submits the function code Gemini produces.

### step_040_signature

Introduce the idea of a function signature and why it matters. The student asks Gemini to describe the signature of their generated function and submits it as YAML.

### step_050_determinism

Introduce determinism and why it matters for debugging and testing. The student evaluates whether an example function is deterministic and submits the result.

### step_060_correctness

Introduce correctness as checkable properties. This begins the transition into RBSChooser2-specific evaluation.

### step_070_overspecifying

Demonstrate that if you state a wrong constraint confidently, Gemini will incorporate it. Teach students to write requirements that reflect what they actually want.

### step_080_logic_sanity_checks

Teach students to read code critically by identifying edge cases, hidden assumptions, and failure modes.

### step_090_restate_goal

Have the student restate the RBSChooser2 goal in plain language to align on what will be built and what will be evaluated.

### step_100_choose_signature

Have the student propose a deliberate signature for the real RBSChooser2 function rather than accepting an invented interface.

### step_110_architecture_outline

Outline a decomposition into testable pieces (for example initiate, run, scoring helpers, and utilities).

### step_120_download_data

Introduce reproducible data access in Colab and download or locate the provided datasets.

### step_130_load_and_inspect

Load the dataset(s) with pandas and perform basic sanity checks.

### step_140_prune_options

Apply the assignment pruning rule to reduce to a high-quality subset.

### step_150_merge_datasets

Join/merge inputs needed for scoring and confirm expected row counts.

### step_160_define_option_object

Define a consistent internal representation for an RBS option and create a few example objects.

### step_170_implement_initiate

Implement and test `initiate()` so it returns a deterministic state object used by later steps.

### step_180_define_objectives

Define the scoring objective(s) and how tradeoffs are handled.

### step_190_implement_run

Implement and test `run()` for a single CDS input.

### step_200_test_determinism_run

Verify `run()` is deterministic and teach how to structure a reproducible test.

### step_210_min_correctness_checks

Add minimal invariants that can be checked automatically (for example spacing rules and alphabet constraints).

### step_220_utr_challenge

Run the 5' UTR challenge portion of the assignment and summarize outputs.

### step_230_final_submission

Print the final submission package for bCourses (passcode, hashes, and key results).

## Development notes

- Step scripts are plain Python files. Each file defines constants (STEP_ID, KEY, TITLE, NEXT_STEP) and three functions: `render(state)`, `shape_check(answer)`, and optionally `validate(answer, state)`.
- The mentor loads steps dynamically and renders the step body using a small markdown-to-HTML renderer.
- The goal is to keep the mentor strict about step order and lightweight about grading, while still nudging students toward good software practices.