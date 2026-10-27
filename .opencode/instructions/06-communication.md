# Communication Style

- Be concise. Lead with the answer or the diff, not a preamble.
- State assumptions in one line; ask a question only if the answer changes the design.
- Explain trade-offs briefly: seniors are judged on decisions.
- When you change a model, always state the migration implication ("adds nullable column, safe on large tables" vs "needs 3-step deploy").
- When you cannot verify (no DB, no network), say so explicitly rather than claiming success.
- Do not invent API signatures for newer package versions; inspect the installed package or docs.
