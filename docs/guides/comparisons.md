# DOG vs other specs

DOG is not another behavioral or interface spec format. It is a thin connective layer over the slices of the system you already describe.

## At a glance

| Category                | Examples                  | What they describe                                  | DOG's relationship                                                                       |
| ----------------------- | ------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Behavior specs          | Gherkin, Cucumber, BDD    | Executable behavior examples (Given/When/Then)      | DOG describes the durable concept graph around those behavior examples.                  |
| Interface specs         | OpenAPI                   | HTTP contracts, endpoints, schemas                  | DOG connects API contracts to actors, behaviors, components, and data.                   |
| Event/API specs         | AsyncAPI                  | Message-driven contracts, events, topics            | DOG explains what those events mean in the project concept graph and what they affect.  |
| Architecture docs       | C4 model                  | System / container / component / code structure     | DOG is a queryable, lintable concept map — not a visual diagram.                         |
| Decision docs           | ADRs                      | Why a decision was made, tradeoffs, consequences    | ADRs explain *why*. DOG records what the system currently *means*.                       |
| Feature spec workflows  | Spec Kit, Kiro            | Requirements / design / tasks for a specific change | DOG turns planning into persistent concept diffs that survive implementation.            |
| Tests                   | unit, integration, e2e    | Whether behavior actually holds                     | DOG does not prove behavior. It tells agents which behaviors and components to inspect. |
| Agent instruction files | AGENTS.md, Cursor Rules   | How the agent should work                           | These tell agents *how to work*. DOG tells agents *what the system means*.               |

## The core idea

Existing specs each describe one slice:

```text
Gherkin describes behavior examples.
OpenAPI describes HTTP contracts.
AsyncAPI describes event contracts.
C4 describes architectural shape.
ADRs describe decisions.
Spec Kit / Kiro describe a feature workflow.
```

DOG connects those slices into a small, durable concept graph:

```text
@Actor      who interacts with the system
!Behavior   what the system does
#Component  what implements it
&Data       what information is stored or passed
```

> DOG does not replace your specs. It makes them navigable by agents.

## Behavior specs (Gherkin / BDD)

Gherkin describes *examples* of behavior — concrete inputs and outcomes — and is often executable. DOG describes the *concepts* those examples touch: the actors, the behaviors as named units of system meaning, the components that implement them, the data that flows through.

A `.feature` file says *"when a user logs in with valid credentials, a session is created"*. The DOG `!Login` behavior says what the system promises about login in general, references `@User`, `&Credentials`, `&Session`, and the `#AuthService` that implements it. The two complement each other: BDD tests that login actually works; DOG helps an agent know that login exists, what depends on it, and what to inspect when changing it.

## Interface specs (OpenAPI, AsyncAPI)

OpenAPI and AsyncAPI describe *contracts at boundaries* — endpoints, payloads, status codes, events, topics. They are excellent for code generation and consumer integration. They do not, by design, describe domain meaning, internal components, or who initiates a flow.

DOG complements these by tying the contract to the rest of the project. The `POST /sessions` endpoint maps to `!Login`, called by `@User`, implemented by `#AuthService`, producing `&Session`. An agent reading the OpenAPI spec alone sees the contract; an agent reading DOG sees the contract *plus* what changes if you touch it.

## Architecture docs (C4)

C4 describes architecture as a series of nested visual diagrams. DOG describes the same conceptual structure as queryable Markdown.

If C4 is "the picture of the system", DOG is "the index of the system" — searchable by name, traversable by reference, lintable for consistency. The two are not in conflict; the C4 diagram and `dog graph` output describe overlapping things at different fidelity.

## Decision docs (ADRs)

ADRs answer *"why did we decide this?"*. DOG answers *"what does this currently mean?"*. They serve different audiences across time: ADRs are read mostly by humans understanding the past; DOG is read mostly by agents planning the present.

ADRs do not need replacing. DOG just makes sure the *consequences* an ADR refers to are findable in the concept graph.

## Feature spec workflows (Spec Kit, Kiro)

Spec Kit and Kiro guide an agent through a structured spec-then-plan-then-implement workflow for a single feature. The workflow is rigorous, but the artifacts are usually disposable — once the feature ships, the spec rarely gets reread.

DOG proposes a different shape for the same workflow:

```text
brainstorm → update DOG docs → review the DOG docs diff → implement → dog lint
```

The diff is the plan. The diff merges into a graph that the next task starts from. There is no separate spec artifact to maintain or discard.

## Agent instruction files (AGENTS.md, Cursor Rules)

These tell agents how to work — coding conventions, commit format, review style. DOG tells agents what the system *is*. They sit at different layers and combine well:

```text
Agent instruction files tell agents how to work.
DOG gives agents the system knowledge to work on.
```

A repo can comfortably use both: an `AGENTS.md` for project conventions, plus a DOG docset for the concept graph.

## Summary

> Existing specs describe slices of the system. DOG connects those slices into a durable concept graph.

DOG is the connective tissue between behavioral specs, interface contracts, architecture docs, and implementation — abstract enough to survive implementation churn, structured enough for agents to query, lint, and reason over.
