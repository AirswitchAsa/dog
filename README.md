# DOG

<p align="center">
  <img src="dog.png" alt="DOG" width="200">
</p>

**Documentation Oriented Grammar** — a typed, lintable concept graph of your project, written in plain Markdown.

DOG turns agent planning into persistent project knowledge. Instead of asking coding agents to repeatedly read the repo, write a disposable spec, write a disposable plan, and then implement, DOG keeps a small concept graph of actors, behaviors, components, and data that agents can query, diff, and lint.

> The DOG docs diff is the plan.

Available on [PyPI](https://pypi.org/project/dog-cli/) and as prebuilt binaries on [Releases](https://github.com/AirswitchAsa/dog/releases/latest).

---

## Install

**Agent skill** — recommended. Teaches Claude Code, Cursor, Codex, and similar agents to use DOG automatically:

```bash
npx skills add https://github.com/AirswitchAsa/dog/tree/main/skills/dog
```

**CLI** — prebuilt binary for macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/AirswitchAsa/dog/main/scripts/install.sh | sh
```

Or `pip install dog-cli` / `uv add dog-cli`. See the [install guide](docs/guides/install.md) for Windows, Intel macOS, and building from source.

---

## A tiny example

A `.dog.md` file defines exactly one primitive — Actor, Behavior, Component, or Data — with a few required sections and typed cross-references:

```markdown
# Behavior: Login

## Condition

A `@User` submits valid `&Credentials` to `#AuthService`.

## Description

Authenticates the user and starts a session.

## Outcome

A `&Session` is created and returned to the user.

## Notes

- Failed attempts are rate-limited.
```

Now an agent can navigate the project as a graph:

```bash
dog get "!Login" --depth 1   # read the spec with referenced primitives inlined
dog refs "#AuthService"      # impact analysis: what depends on AuthService?
dog lint docs                # validate structure and references
```

See the [getting-started guide](docs/guides/getting-started.md) for the primitive types, sigils, and required sections, or the [CLI reference](docs/guides/cli.md) for all commands.

---

## The workflow

```text
brainstorm change
  → update DOG concept docs
  → review the DOG docs diff
  → implement against that diff
```

The output of understanding is a durable map of the system, not a plan that gets thrown away after one task. See the [agent workflow guide](docs/guides/agent-workflow.md) for how this works inside Claude Code, Cursor, and other agents.

---

## How DOG relates to other specs

DOG does not replace your existing specs. It connects them.

| You already have                | DOG's role                                                              |
| ------------------------------- | ----------------------------------------------------------------------- |
| Gherkin / BDD scenarios         | Describes the durable concept graph around those behavior examples.    |
| OpenAPI / AsyncAPI contracts    | Connects API and event contracts to actors, behaviors, and data.       |
| C4 diagrams                     | Provides a queryable, lintable concept map instead of static visuals.  |
| ADRs                            | ADRs explain *why*. DOG describes what the system currently *means*.   |
| Spec Kit / Kiro feature specs   | Concept diffs that survive implementation, instead of disposable plans. |

See [comparisons](docs/guides/comparisons.md) for the full picture.

---

## Does it actually work?

A controlled eval against the [`crates/warp_cli`](https://github.com/warpdotdev/warp/tree/main/crates/warp_cli) subsystem of [warpdotdev/warp](https://github.com/warpdotdev/warp): same agent (`claude-sonnet-4-6`), 5 information-retrieval tasks, 3 trials per condition. Condition A gets warp source only; condition B adds an authored DOG docset and the dog skill.

| | A (baseline) | B (with DOG) |
|---|---|---|
| Concept recall (mean) | 0.957 | **0.991** |
| File recall (mean) | 0.733 | **0.967** |
| Hallucination rate | 0/15 | 0/15 |
| Tool calls per task (mean) | 19.7 | **12.7** |

B matches or beats A on concept recall on every task, doubles file recall on the two tasks where A struggled to cite the right file, and uses ~35% fewer tool calls on average. Zero hallucinations in either condition.

The DOG docs were authored in a **separate Claude Code session** with no shared context with the eval runner, and ground truth was sourced from the Rust code rather than from the docs — so B doesn't get credit for echoing its own docs back.

Full methodology, per-task analysis, raw transcripts, and limitations: [AirswitchAsa/dog-eval-warp](https://github.com/AirswitchAsa/dog-eval-warp).

---

## Docs

- [Getting started](docs/guides/getting-started.md) — primitives, sigils, your first `.dog.md`
- [Install guide](docs/guides/install.md) — binaries, PyPI, building from source
- [CLI reference](docs/guides/cli.md) — every command and flag
- [Agent workflow](docs/guides/agent-workflow.md) — concept-diff workflow, skill install, system-prompt fallback
- [Comparisons](docs/guides/comparisons.md) — DOG vs Gherkin, OpenAPI, C4, ADRs, Spec Kit, Kiro
- [Evaluation](https://github.com/AirswitchAsa/dog-eval-warp) — controlled eval on a real Rust codebase
- [Philosophy](docs/guides/philosophy.md) — design principles
- [Example docset](docs/) — DOG dogfooding itself

---

## License

MIT
