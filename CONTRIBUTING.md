# Contributing Guidelines

Short guidance to improve traceability and collaboration.

Branching

- Create short-lived feature branches for each task: `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.

Commit messages

- Use conventional, short prefixes: `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
- Make commits small and focused (one logical change per commit) to ease PR reviews.

Changelog policy

- After completing a milestone or merging to `main`, add an entry to `CHANGELOG.md` with the date and short summary.

Pull Requests

- Include a brief description of what changed and why, reference related issues, and list commands to reproduce critical steps.

Testing

- Add small unit tests for new modules under `tests/` and include setup/teardown if needed.
