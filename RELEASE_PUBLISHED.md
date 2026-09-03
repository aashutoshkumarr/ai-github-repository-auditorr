# Release Marker: v0.1.0 — Production-ready Auditor Platform

This file marks finalization activities performed in the repository for v0.1.0.

What was done

- Annotated tag v0.1.0 created and pushed to origin.
- RELEASE_DRAFT.md added with full release notes.
- Branch master pushed to origin.

How to publish the release (two options)

1) Publish from GitHub UI (recommended):
   - Open: https://github.com/ashutoshranaa/ai-github-repository-auditor/releases/new?tag=v0.1.0
   - Paste the contents of RELEASE_DRAFT.md into the release notes textarea (or copy from the file in the repo).
   - Mark as Draft or Publish immediately.

2) Publish using gh (locally or in CI):
   - gh auth login --with-token < ~/.token-file
   - gh release create v0.1.0 --title "v0.1.0 — Production-ready Auditor Platform" --notes-file RELEASE_DRAFT.md --draft

Security reminder

Several personal access tokens were used in this session. Revoke any tokens you do not intend to keep immediately in GitHub -> Settings -> Developer settings -> Personal access tokens.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
