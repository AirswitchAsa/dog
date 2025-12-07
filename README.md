# **`.dog.md`**

**Documentation Oriented Grammar (DOG)**

---

## **1. Overview**

`.dog.md` is a Markdown-native specification format used to describe system concepts in sphaere.
A `.dog.md` file defines exactly one primitive type — **Project**, **Actor**, **Behavior**, **Component**, or **Data** — using light structural conventions embedded in standard Markdown.

DOG is designed to serve simultaneously as:

* **Human-readable system documentation**
* **A structured LLM knowledge base**
* **A behavioral reference library for AI-assisted testing**

The format preserves Markdown compatibility while adding minimal, machine-checkable structure.

---

## **2. Rationale**

The design of `.dog.md` adheres to the following principles:

### **Markdown-native**

The format avoids custom DSLs or fenced code blocks. Everything remains valid Markdown so files can be rendered anywhere without special tooling.

### **Light structure, high semantic value**

DOG introduces predictable headings and cross-referencing conventions that allow LLMs to reliably understand system concepts without imposing rigid schemas or formal semantics.

### **Unified source of truth**

`.dog.md` files act as a central repository for:

* Product documentation
* Concept definitions
* Expected behavior descriptions
* Developer references
* AI grounding context
* Behavior-driven testing narratives

This ensures that human authors, AI coding agents, and AI test agents work from the same conceptual base.

### **Flat taxonomy**

Primitive types are equal, with no hierarchies or dot grammar. Concepts link to each other through explicit naming, enabling clear cross-referencing and easy incremental evolution.

### **Simple semantic linting**

DOG relies on minimal validation: resolving cross-references, checking allowed sections, and detecting name mismatches. Deeper logical constraints are intentionally left to authors and AI reasoning.

---

## **3. Primitive Types and Allowed Structure**

Each file must start with a level-one Markdown heading:

```
# Project: <Name>
# Actor: <Name>
# Behavior: <Name>
# Component: <Name>
# Data: <Name>
```

All other content is optional and expressed using Markdown sections.
All primitives support a `## Notes` section for short annotations.

---

## **3.1 Project**

Represents the root document of a documentation set.
Provides a high-level description and an index of all DOG concepts.
This file may be generated or updated automatically by tooling.

**Format:**

```
# Project: <Name>

## Description
<freeform text>

## Actors
- <actor name>

## Behaviors
- <behavior name>

## Components
- <component name>

## Data
- <data name>

## Notes
- <short note>
```

---

## **3.2 Actor**

Represents an initiating or participating entity—human or service.

**Format:**

```
# Actor: <Name>

## Description
<free text>

## Notes
- <short note>
```

---

## **3.3 Behavior**

Describes an expected system response, state transition, or effect.
Behaviors rely on inline references for Actors, Components, Data, and other Behaviors.

**Inline reference conventions (using sigils inside backticks):**

| Syntax | Meaning |
| ------ | ------- |
| `` `@actor` `` | Actor reference |
| `` `!behavior` `` | Behavior reference |
| `` `#component` `` | Component reference |
| `` `&data` `` | Data reference |

The linter validates referenced names and annotated types.

**Format:**

```
# Behavior: <Name>

## Condition
- <prerequisite or context>

## Description
<free text with inline references>

## Outcome
- <expected effects or state changes>

## Notes
- <short note>
```

---

## **3.4 Component**

Represents a subsystem, UI element, or logical unit of the application.

**Format:**

```
# Component: <Name>

## Description
<free text>

## State
- <state field>

## Events
- <event name>

## Notes
- <short note>
```

---

## **3.5 Data**

Represents application-level domain entities and their fields.

**Format:**

```
# Data: <Name>

## Description
<free text>

## Fields
- field_name: <optional note>

## Notes
- <short note>
```

---

## **4. Inline Reference Rules**

DOG uses sigils inside backticks to annotate referenced concept types:

| Syntax | Meaning |
| ------ | ------- |
| `` `@Name` `` | Actor reference |
| `` `!Name` `` | Behavior reference |
| `` `#Name` `` | Component reference |
| `` `&Name` `` | Data reference |

This approach allows normal Markdown formatting (*italic*, **bold**, `code`) without triggering reference detection.

The linter checks:

* referenced names exist
* referenced types match their sigil annotation
* unknown names produce warnings

---

## **5. Section Rules**

Allowed sections vary by primitive type but always follow Markdown `##` syntax.
Unrecognized sections produce linter warnings but are not prohibited.

All primitives may include:

```
## Notes
- <short annotation>
```

---

## **6. Summary**

`.dog.md` (Documentation Oriented Grammar) provides a minimal, Markdown-compatible structure for defining system concepts across sphaere. It is designed to:

* Facilitate human-readable documentation
* Serve as a stable knowledge base for LLM agents
* Provide clear expectations for behavior-driven AI testing
* Enable lightweight semantic linting without enforcing rigid formalism
* Scale incrementally as the system grows

DOG maintains a balance between free natural language and predictable structure, ensuring both humans and AI systems can effectively interpret and utilize the specifications.
