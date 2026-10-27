# .opencode for Django 6.1 Project

Configuration for [OpenCode](https://opencode.ai) tailored to this stack: Django 6.1.2, PostgreSQL, whitenoise, gunicorn, Stripe 16, Pillow, requests.

## Install
Copy these into the root of your Django repository:

```
AGENTS.md
opencode.json
.opencode/
requirements.txt / requirements-dev.txt / .env.example   (if you do not have them)
```
Then run `opencode` in the repo root.

## Layout
```
.opencode/
├── README.md
├── instructions/    always-loaded rules (via opencode.json "instructions")
│   ├── 01-project-structure.md
│   ├── 02-coding-style.md
│   ├── 03-stack-and-dependencies.md
│   ├── 04-definition-of-done.md
│   ├── 05-git-and-review.md
│   └── 06-communication.md
├── agent/           invoke with @name
│   ├── django-architect.md   design before code
│   ├── django-reviewer.md    prioritized code review
│   ├── django-security.md    security audit
│   ├── django-tester.md      pytest-django tests
│   ├── django-migrations.md  zero-downtime migrations
│   ├── stripe-payments.md    payments + webhooks
│   └── django-debugger.md    root-cause debugging
├── command/         invoke with /name
│   ├── new-app  add-model  review  test  migrate  check-deploy
│   ├── perf-audit  add-stripe-webhook  deps-audit  release  explain
└── skill/           loaded on demand by agents
    ├── django-conventions        django-orm-performance
    ├── django-migrations         django-testing
    ├── django-security-deploy    django-settings-env
    ├── django-forms-views-templates  django-file-uploads
    ├── stripe-integration        whitenoise-static-media
    └── external-http-requests    django-background-tasks
```

## Examples
- `/new-app orders`
- `@django-architect design a subscription checkout with Stripe`
- `/add-model Invoice with user FK, amount_cents, status`
- `/review`, `/test`, `/check-deploy`

## Notes
- Folder names `agent/`, `command/`, `skill/` are the documented singular forms; plural names are also accepted by recent OpenCode versions.
- Adjust permissions in `opencode.json` to your risk tolerance.
- Pinned versions were provided by you; AGENTS.md tells the agent to verify APIs against installed packages instead of guessing.
