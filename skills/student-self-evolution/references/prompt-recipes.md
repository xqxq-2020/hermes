# Prompt Recipes

Use these prompts as-is or with light edits.

## 1. Analyze New Evidence Only

```text
Use $student-self-evolution to read MEMORY.md, USER.md, and the latest files in data/.
Do analysis only.
Separate direct evidence, inference, and cohort pattern.
Return:
1. current judgment
2. evidence basis
3. next teaching move
4. whether MEMORY.md or USER.md should change
```

## 2. Update Both Files

```text
Use $student-self-evolution to read MEMORY.md, USER.md, and the newest real learning evidence in data/.
Update both markdown files if the new evidence is stable enough.
Keep the writing PPT-style: short headers, short bullets, conclusion-evidence-action.
Do not mix cohort evidence into individual profile.
```

## 3. Generate the Next Micro-Teaching Loop

```text
Use $student-self-evolution to read the current MEMORY.md and USER.md.
Then generate the next 10-minute micro-teaching loop.
Output:
- goal
- warm-up
- one correction focus
- transfer sentence pattern
- exit check
Keep difficulty at roughly 80 percent success probability.
```

## 4. Produce Write-Back Suggestions Without Editing

```text
Use $student-self-evolution to inspect MEMORY.md, USER.md, and data/.
Do not edit files.
Instead, output:
- suggested update for MEMORY.md
- suggested update for USER.md
- reason for each suggestion
- what evidence is still too weak to persist
```

## 5. Resolve Conflicts

```text
Use $student-self-evolution to compare the current MEMORY.md and USER.md against the newest evidence in data/.
Find conflicts between old profile statements and new direct evidence.
Only recommend overwrite if the new evidence is repeated or cross-day.
```

## 6. Run the Script First

```text
Use $student-self-evolution.
Run the scripted brief first from skills/student-self-evolution/scripts/build_evolution_brief.py against the current workspace.
Then use that brief to decide whether MEMORY.md and USER.md should be updated.
```

## 7. Focus on Oral English Only

```text
Use $student-self-evolution to focus only on oral-evaluation evidence.
Ignore resource-library files unless they contain direct student behavior.
Update the student portrait and give the next pronunciation-first teaching loop.
```

## 8. Focus on Cohort Strategy Only

```text
Use $student-self-evolution to focus on cohort-level textbook vocabulary evidence.
Do not rewrite USER.md as if the cohort were one student.
Update only the durable teaching strategy in MEMORY.md and output the next cohort-facing drill plan.
```
