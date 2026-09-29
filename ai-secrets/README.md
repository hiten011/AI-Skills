# ai-secrets

A Claude skill that maintains a private vault of free LLM API keys ([`hiten011/AI-Secrets`](https://github.com/hiten011/AI-Secrets)). It signs up for providers, live-tests every key, keeps the ranked docs current, and keeps hunting for new free LLM APIs and free AI-agent platforms from several sources every run: three GitHub lists, the models.dev catalog, OpenRouter's free-model list, Composio search tools and the web.

`SKILL.md` here is a mirror of the master copy at [`hiten011/AI-Secrets` → `handoff/SKILL.md`](https://github.com/hiten011/AI-Secrets/blob/main/handoff/SKILL.md) (commit `796d98e`, 2026-09-29). It is self-contained: the session routine, playbooks, data format, ranking rules, discovery sweep and hard rules are all in that one file. When the master changes, copy it here too.

## What it needs

- The Composio GitHub connection (alias `hiten-github`) for repo access, and Composio's search tools for discovery (plain web search is the fallback).
- Claude in Chrome for sign-ups, one tab per provider.
- Access to the private `AI-Secrets` repo, which holds the keys. The skill never prints them.

## Install

Save it from Claude's skill proposal card, or add the `ai-secrets/` folder as a skill. It is also saved in Composio as `ai-secrets`. Then say "check my ai-secrets keys", "sign up for the next provider" or "find new free LLM APIs".

## Files

```
ai-secrets/
├── SKILL.md    # the whole skill
└── README.md
```

## Guarantees

It never pastes a full key into chat, commits or logs. Keys go only to their own provider's documented API host. It never gets past CAPTCHAs, phone checks, 2FA or card walls itself, and never adds a payment method. Text from lists, blogs and search results is treated as data, never as instructions.
