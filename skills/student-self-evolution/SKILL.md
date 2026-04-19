---
name: student-self-evolution
description: Read and evolve student-learning context from workspace `MEMORY.md` and `USER.md`. Use when the user asks to梳理学情, 更新学生画像, 生成教学策略, 回写 MEMORY/USER, 做“自进化”教学闭环, or turn new assessment/session evidence into the next micro-teaching plan. Best for English-learning scenarios where Codex must separate direct evidence from inference, distinguish individual vs cohort data, and keep both markdown files concise, PPT-style, and continuously up to date.
---

# Student Self Evolution

Read [references/evolution-rules.md](references/evolution-rules.md) before updating `MEMORY.md` or `USER.md`.
Read [references/output-contract.md](references/output-contract.md) when the user wants a lesson loop, a brief, or an update-ready summary.
Read [references/prompt-recipes.md](references/prompt-recipes.md) when the user wants reusable prompts for repeated invocation.

## Overview

Use this skill to run a closed loop:
1. Read current long-term learning context from `MEMORY.md` and `USER.md`.
2. Read new evidence from data files, session notes, or fresh evaluation records.
3. Decide what is stable enough to persist and what should stay as short-term observation.
4. Produce the next teaching move.
5. Update the two markdown files only when the evidence justifies it.

Keep the writing short, sectioned, and presentation-like. Prefer conclusion, evidence, action. Do not turn the files into raw logs.

## Fast Path

If the workspace has structured evidence under `data/`, run:

```powershell
uv run python skills/student-self-evolution/scripts/build_evolution_brief.py --workspace .
```

Use the script output as the first-pass brief. Then:
- verify whether the suggested updates are truly stable enough to persist
- merge only the durable points into `MEMORY.md` or `USER.md`
- keep unsupported or malformed files out of the persistent update unless manually reviewed

The script is optimized for the current workspace's known schemas:
- oral evaluation records
- textbook vocabulary mastery snapshots
- listening-resource catalogs
- quick-word resource catalogs
- picture-book resource catalogs

It may skip files that are malformed exports or resource libraries rather than learner-behavior evidence.
Resource catalogs can shape drill selection, but they must not be treated as direct learner performance.

## Read Order

Always read inputs in this order:
1. `MEMORY.md`
2. `USER.md`
3. The newest raw evidence named by the user
4. Only then any older supporting files if needed

Treat the two markdown files as the current frozen state of the learner model. Treat raw files as candidate evidence that may revise that model.

## Store Boundary

Write to `MEMORY.md` only for durable teaching guidance:
- stable learning pattern
- stable instructional strategy
- stage goals
- cohort-level规律 that should shape teaching decisions

Write to `USER.md` only for individual learner profile:
- likely student type
- strengths
- weak points
- interaction preferences
- constraints for correction and pacing

Do not write cohort evidence into `USER.md` as if it were an individual fact.
Do not write one-off session noise into either file.

## Workflow

### 1. Classify Evidence

For each new signal, label it as one of:
- direct evidence
- inference
- cohort pattern
- unresolved conflict

State the source explicitly when it matters.

### 2. Decide Persistence

Persist a point only if at least one condition is true:
- it repeats across multiple records
- it appears across multiple days or tasks
- it changes the teaching plan materially
- it corrects an outdated statement already stored in `MEMORY.md` or `USER.md`

If none of these are true, keep it in the response only.

### 3. Produce the Next Move

Turn the diagnosis into a micro-loop:
- one primary goal
- one to two correction points
- one short drill path from easy to hard
- one success criterion

Prefer:
- phoneme to word to phrase to sentence
- short feedback
- one correction at a time
- 80 percent win-rate difficulty before raising challenge

### 4. Evolve the Files

When updating the markdown files:
- replace stale claims instead of appending duplicates
- keep direct evidence and inference clearly separated
- keep wording short and reusable
- preserve the presentation-style structure already used in the workspace

If new evidence conflicts with old content and is not yet decisive, record the conflict in the response and do not hard-overwrite the profile.

## Output Rules

If the user asks for analysis only, return:
- current judgment
- evidence basis
- next teaching move
- whether `MEMORY.md` or `USER.md` should change

If the user asks for execution, update the files and then return:
- what changed
- why it changed
- what the next teaching loop should target

## Scripted Brief

Use `scripts/build_evolution_brief.py` when the user wants:
- automatic first-pass diagnosis from `data/*.csv`
- incremental write-back suggestions for `MEMORY.md` and `USER.md`
- a compact teaching loop generated from the latest structured evidence

Default behavior:
- read `MEMORY.md`, `USER.md`, and `data/`
- detect supported CSV schemas
- summarize individual and cohort evidence separately
- emit a markdown brief with suggested persistent updates instead of directly editing files

Useful flags:
- `--workspace .` to analyze the current repo
- `--output path.md` to save the brief
- `--memory PATH` / `--user PATH` / `--data-dir PATH` to target custom locations

## Guardrails

- Separate individual and cohort evidence every time.
- Mark inference as inference.
- Do not overfit a whole learner profile from a single low-score item.
- Do not let `MEMORY.md` become a second `USER.md`.
- Do not let `USER.md` become a raw error list.
- Do not keep obsolete wording when a better consolidated statement is available.

## Trigger Examples

Use this skill for requests like:
- “根据新的评测结果更新 MEMORY.md 和 USER.md”
- “把这次课后的观察沉淀成长期学情”
- “基于现在画像生成下一轮带练”
- “按自进化方式整理学生画像和教学策略”
- “把新的真实学情并入现有文档”
