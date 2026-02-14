---
name: ai-workflow-skills
description: Collection of language-agnostic AI workflow skills for coding agents. Includes git commit, changelog, rebase, TDD, multi-model collaboration, and CLI delegation skills. Use when browsing available skills or learning what this repository offers.
---

# AI Workflow Skills

This repository provides 15 language-agnostic skills for AI coding agents.

## Curated Skills (stable, standalone workflows)

| Skill | Description |
|-------|-------------|
| commit | Create git commits following project conventions |
| changelog | Generate changelog entries from branch commits |
| rebase | Rebase onto trunk with conflict resolution |
| tdd-fix | TDD bug-fix workflow with xfail tests |

## Experimental Skills (advanced, external tool dependencies)

### Multi-Model Collaboration
| Skill | Description |
|-------|-------------|
| multi-model-ask | Ask all models a question, synthesize best answer |
| multi-model-plan | Get plans from all models, synthesize best plan |
| multi-model-prompt | Compare implementations from multiple models |
| multi-model-execute | Synthesize best parts from all model implementations |
| multi-model-architecture | Generate architecture from all models |
| multi-model-review | Consensus-weighted multi-model code review |
| multi-model-fix-review | Fix review findings as atomic commits |

### CLI Delegation
| Skill | Description |
|-------|-------------|
| codex-cli | Delegate to OpenAI GPT via Codex CLI |
| gemini-cli | Delegate to Google Gemini CLI |
| cursor-cli | Delegate to Cursor's agent CLI |
| gpt-cli | Alias for codex-cli |

## Installation

```bash
npx skills add tony/ai-workflow-plugins
```

## Design Philosophy

All skills are language-agnostic — they discover project-specific tooling by reading AGENTS.md / CLAUDE.md at runtime.
