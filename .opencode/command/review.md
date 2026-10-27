---
description: Review current uncommitted changes as a senior Django reviewer
agent: django-reviewer
subtask: true
---
Review the current changes.

Status: !`git status --short`

Diff: !`git diff HEAD`

Focus (if provided): $ARGUMENTS
