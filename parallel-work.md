# Parallel Work Instructions

When multiple agents work on the same repo simultaneously, follow this workflow to avoid conflicts and enable real-time user review.

---

## Setup (Before Starting Work)

### 1. Check If You Need a Feature Branch
- **Ask the user** if you should create a feature branch or work directly on the current branch.
- If a feature branch is needed, create one with a name relevant to your work:
  ```bash
  git checkout -b {descriptive-branch-name}
  ```

### 2. Confirm Your Agent Name
- **Do not start work if you aren't confident in your agent name.**
- Check session context or ask the user to confirm.
- Use a consistent, recognizable name for all your branches and commits.

### 3. Create Your Agent Workspace
```bash
mkdir -p ~/agentic-repos
```

### 4. Clone the Origin Repo
```bash
git clone /path/to/origin/repo ~/agentic-repos/{origin-repo-name}-{agent-name}
cd ~/agentic-repos/{origin-repo-name}-{agent-name}
```

### 5. Create Your Feature Branch
```bash
git checkout -b {agent-name}/{short-feature-description}
```

---

## Working

- **All changes go in your cloned repo**, never directly in the origin repo.
- **Run test harnesses from your cloned repo**, not the origin.
- Test before every commit:
  ```bash
  python -m py_compile jbrowse.py
  python -m py_compile tools/svg_screenshot_poc.py
  python tools/svg_screenshot_poc.py --item otter
  ```
- Sign your documentation changes — when editing release-specific docs, add your agent name or tag at the top of your subsection.

---

## Pushing / Merging

### DO NOT Push Without Being Asked
- The plan is to push branches back to origin and do merging on the origin side.
- **The user wants to review in real time** — you must wait until explicitly requested.
- When asked to push:
  ```bash
  git push origin {your-branch-name}
  ```
- After pushing, notify the user and wait for merge instructions.

---

## Documentation Rules

- **Sign your work** in release-specific documentation files. Add a comment or header like:
  ```markdown
  ## [Your Agent Name] — [Short Description]
  ```
- **Tag your sections** so it's clear who did what during review.
- Never modify another agent's sections without discussion.

---

## Safety Rules

- **NEVER accidentally use the wrong repo.** Always `pwd` and `git remote -v` to confirm you're in your agent workspace.
- **ALL changes in new repo only.** Test harnesses, edits, commits — everything happens in `~/agentic-repos/{repo}-{agent}`.
- **Never push to origin without explicit user request.**
