# Commit message guidelines

This project uses a short, structured commit message style to make the
history easy to scan. The suggested format is:

```
<type>(<scope>): <short summary>

Optional longer description.

Footer (e.g., BREAKING CHANGE: ... or references)
```

Common types:

- feat: a new feature
- fix: a bug fix
- docs: documentation only changes
- style: formatting, missing semicolons, etc (no code changes)
- refactor: code change that neither fixes a bug nor adds a feature
- perf: code change that improves performance
- test: adding or updating tests
- chore: build process or auxiliary tools

Examples:

```
feat(cleaning): add clean_path public alias

Provide a small helper to run cleaning from a path and write output.

```

```
fix(compare): handle non-DataFrame inputs with a TypeError

Add validation in `compare_countries` to raise a helpful error when
called with the wrong argument type.

```

Tips:

- Keep the subject line under 50 characters.
- Use the imperative mood: "fix", "add", "remove".
- If a change includes multiple logical pieces, prefer multiple commits.
