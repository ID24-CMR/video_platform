# Git and Review Conventions

- Branches: `feature/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.
- Commits: Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`), imperative mood, <72 char subject.
- Never commit: `.env`, `staticfiles/`, `media/`, `*.sqlite3`, `__pycache__/`, secrets.
- Never force-push shared branches. Never run `git reset --hard` without explicit user approval.
- One migration set per PR where possible; never rewrite migrations that are on `main`.
- PR description: what/why, migration impact, test evidence, rollback plan.
- Review order: (1) blocking issues, (2) performance, (3) design, (4) nits labelled optional.
