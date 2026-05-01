# CLI Reference

Use `dog --help` and `dog <command> --help` for the latest options. If `dog` is not installed, run any command with:

```bash
uvx --from dog-cli dog <command>
```

## Query commands

These return JSON by default — convenient for agents and scripts. Pass `-o text` for human-readable output.

### `dog search <query>`

Local hybrid retrieval over primitive names, sections, content, and references.

```bash
dog search "login" -p docs
dog search "#auth" -p docs
dog search "rare term" -p docs --all
dog search "rare term" -p docs --min-score 0
dog search "login" -p docs -o text
```

| Option           | Purpose                                  |
| ---------------- | ---------------------------------------- |
| `--path`, `-p`   | File or directory (default `.`)          |
| `--limit`, `-l`  | Max results (default `10`)               |
| `--output`, `-o` | `json` or `text`                         |
| `--min-score`    | Relevance threshold                      |
| `--all`          | Include low-confidence matches           |

### `dog get <name>`

Fetch a primitive by case-insensitive name. Sigils filter by type.

```bash
dog get "@User" -p docs
dog get "!Login" -p docs --depth 1
dog get "#AuthService" -p docs -o text
```

| Option           | Purpose                                       |
| ---------------- | --------------------------------------------- |
| `--path`, `-p`   | File or directory (default `.`)               |
| `--output`, `-o` | `json` or `text`                              |
| `--depth`        | Inline referenced documents up to N hops      |

### `dog list [sigil]`

List primitives, optionally filtered by type.

```bash
dog list -p docs
dog list "!" -p docs
dog list "@" -p docs -o text
```

Sigils: `@` Actors, `!` Behaviors, `#` Components, `&` Data.

### `dog refs <name>`

Reverse reference lookup — what depends on this primitive? Essential for impact analysis before cross-cutting changes.

```bash
dog refs "#AuthService" -p docs
dog refs "@User" -p docs -o text
```

## Operational commands

These keep conventional CLI-oriented output defaults.

### `dog lint <path>`

Validate structure, required sections, and references. Use as a quality gate.

```bash
dog lint docs
```

### `dog format <path>`

Normalize whitespace. Pass `--check` to dry-run.

```bash
dog format docs
dog format --check docs
```

### `dog index <path> --name "<project>"`

Generate a `Project: ...` index file from the primitives in the docset.

```bash
dog index docs --name "My Project"
```

### `dog graph`

Emit DOT for dependency visualization.

```bash
dog graph -p docs | dot -Tpng -o graph.png
dog graph "!Login" -p docs
```

### `dog export`

Bulk-export the docset as a single JSON document.

```bash
dog export -p docs > context.json
```

### `dog serve <path>`

Browser viewer with hot-reload and color-coded references.

```bash
dog serve docs
```

## Quality gate

Before declaring documentation work complete:

```bash
dog lint docs
dog format --check docs
```
