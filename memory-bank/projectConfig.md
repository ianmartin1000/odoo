# Project Configuration

## Banyan Memory Bank

This section is auto-managed by `/bmb:init`. Do not edit manually.

- **Banyan Version**: 2.2.1
- **Initialized**: 2026-08-27
- **Last Updated**: 2026-08-27

## Git & Branching (v2)

```yaml
metadata_branch: banyan
protected_branches: [banyan]
pr_target: banyan
sync_automation: none
archive_strategy: local-merge
worktree_root: ~/banyan-wt/odoo/
```

## Agent Backends

```yaml
backends:
  plan:                  anthropic
  tdd:                   anthropic
  code-review:           anthropic
  creative-architecture: anthropic
  creative-uiux:         anthropic
  creative-algorithm:    anthropic
  creative-user-journey: anthropic
  creative-critique:     codex
  auto-final-review:     anthropic
  availability:          auto
```

Codex companion not detected on this machine — all seams run on Anthropic; `creative-critique` will self-enable if Codex is installed later (see `context/agent-backends.md`).

## Team

```yaml
team:
  # <git-email>: <friendly first name>
  ian.martin@simunix.com: Ian
```

## UAT

No UAT configuration yet — this project has no detected web/UI surface for `/bmb:uat` at this time. Run `/bmb:uat-init` to configure if needed later.

## Notes

- This is a personal fork (`DaKaZ/odoo`) of the Odoo ERP framework, used for local development. Working branch: `banyan`. Recent history is shallow (single squashed "local docker setup" commit) — this repo was likely re-initialized/re-cloned rather than carrying full upstream history.
