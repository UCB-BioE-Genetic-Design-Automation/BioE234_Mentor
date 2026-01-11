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

Purpose
- Transition from LLM workflow skills to building RBSChooser2.
- Align on what will be built and what will be evaluated.

Student actions
- Restate the goal of RBSChooser2 in plain language.
- Include what the input is, what the output is, and what the output must not include.

Submission
- `mentor.submit_display(KEY, text)`

Validation
- Shape check only.
- Non-empty text.

Notes
- We do not grade biological correctness here. We grade clarity and alignment with the contract.

### step_100_choose_signature

Purpose
- Lock the function interface before any implementation.

Student actions
- Write a one-line function signature for RBSChooser2 (name, inputs, outputs).
- Keep it consistent with the restated goal from step 090.

Submission
- `mentor.submit_display(KEY, yaml_text)`

Validation
- Syntax-only YAML validation.
- Required fields present (name, inputs, outputs).

Notes
- This signature becomes the contract used for later automated checks.

### step_110_architecture_outline

Purpose
- Decompose the problem into testable pieces.

Student actions
- Outline a small module structure (functions and responsibilities).
- Identify where data loading, preprocessing, scoring, and selection happen.

Submission
- `mentor.submit_display(KEY, yaml_or_bullets)`

Validation
- Shape check only.
- Must name at least two components (for example initiate and run).

Notes
- The outline should be implementable in Colab without hidden dependencies.

### step_120_download_data

Purpose
- Ensure every student starts from the same datasets.

Student actions
- Run the provided cell that downloads or locates datasets.
- Confirm files exist in expected paths.

Submission
- `mentor.submit_display(KEY, "ok")`

Validation
- Deterministic file existence checks.
- Optional hash checks for known files.

Notes
- This step prevents silent failures later due to missing data.

### step_130_load_and_inspect

Purpose
- Build the habit of inspecting data before using it.

Student actions
- Load dataset(s) with pandas.
- Report basic sanity checks (columns present, row count, missing values).

Submission
- `mentor.submit_display(KEY, yaml_text)`

Validation
- Shape check only.
- Must include at least row_count and a short note about missingness.

Notes
- We do not enforce exact counts here unless the dataset is fixed and stable.

### step_140_prune_options

Purpose
- Reduce the option space to a high quality subset using the assignment rule.

Student actions
- Apply the pruning rule to the dataset.
- Report the before and after counts.

Submission
- `mentor.submit_display(KEY, yaml_text)`

Validation
- Shape check only.
- Must include before_count and after_count.

Notes
- Later steps may enforce expected ranges once the dataset is finalized.

### step_150_merge_datasets

Purpose
- Combine inputs needed for scoring into one consistent table.

Student actions
- Perform required merges/joins.
- Report final row count and confirm required columns exist.

Submission
- `mentor.submit_display(KEY, yaml_text)`

Validation
- Shape check only.
- Must include row_count and a list of key columns.

Notes
- This step catches common join mistakes early.

### step_160_define_option_object

Purpose
- Define a consistent internal representation for an RBS option.

Student actions
- Define a small Python structure (dataclass or dict schema) for one option.
- Show one example instance.

Submission
- `mentor.submit_display(KEY, code_text)`

Validation
- Shape check only.
- Non-empty text that looks like Python code.

Notes
- This object is used by initiate and run.

### step_170_implement_initiate

Purpose
- Implement `initiate()` to build a deterministic state object used for selection.

Student actions
- Implement initiate.
- Run a small check that the returned state is deterministic across runs.

Submission
- `mentor.submit_display(KEY, "ok")`

Validation
- Deterministic checks that required keys exist in the returned state.

Notes
- `initiate()` should not do per-CDS work.

### step_180_define_objectives

Purpose
- Make the scoring objective explicit before coding selection logic.

Student actions
- Write a plain-language description of what run should optimize.
- Include any tie-break rules.

Submission
- `mentor.submit_display(KEY, text)`

Validation
- Shape check only.
- Non-empty text.

Notes
- This becomes the reference when students justify design choices later.

### step_190_implement_run

Purpose
- Implement `run()` to choose an RBS for a given CDS using the prepared state.

Student actions
- Implement run.
- Run on a provided test CDS and show the chosen option.

Submission
- `mentor.submit_display(KEY, "ok")`

Validation
- Deterministic checks on output type and alphabet constraints.
- Must return an upstream-only RBS string.

Notes
- Biological optimality is not graded here. Basic invariants are.

### step_200_test_determinism_run

Purpose
- Confirm the selection logic is repeatable.

Student actions
- Run run() multiple times on the same CDS.
- Confirm identical output.

Submission
- `mentor.submit_display(KEY, "ok")`

Validation
- Deterministic expected output for a fixed test CDS and fixed state.

Notes
- If the algorithm uses randomness, it must be seeded in the state.

### step_210_min_correctness_checks

Purpose
- Add a small set of invariants that catch obvious mistakes.

Student actions
- Add checks for alphabet, upstream-only output, and basic spacing rules.
- Run the checks on a few example CDS inputs.

Submission
- `mentor.submit_display(KEY, "ok")`

Validation
- Deterministic invariant checks.

Notes
- These checks should be fast and not require an LLM.

### step_220_utr_challenge

Purpose
- Evaluate behavior on a small challenge set that stresses context effects.

Student actions
- Run the provided challenge driver.
- Summarize outcomes in one short paragraph.

Submission
- `mentor.submit_display(KEY, text)`

Validation
- Shape check only.
- Non-empty text.

Notes
- Instructors review this manually.

### step_230_final_submission

Purpose
- Produce a final record for instructors to review.

Student actions
- Run the final cell to print the submission package.
- Paste it into bCourses.

Submission
- No new submission. This step prints the final package.

Validation
- The mentor report includes passcode and SHA1 fingerprints for prior submissions.

Notes
- Instructors review the report manually.