# DOG CLI Reference

Use `dog --help` and `dog <command> --help` for current options. If `dog` is not installed, prefer:

```bash
uvx --from dog-cli dog <command>
```

## Query Commands

These default to JSON for coding agents.

### `dog search <query>`

Local hybrid retrieval over DOG primitives, sections, content, and references.

```bash
dog search "login" -p docs
dog search "#auth" -p docs
dog search "low confidence" -p docs --all
dog search "low confidence" -p docs --min-score 0
dog search "login" -p docs -o text
```

Options:
- `--path`, `-p`: file or directory, default `.`
- `--limit`, `-l`: max results, default `10`
- `--output`, `-o`: `json` or `text`
- `--min-score`: relevance threshold
- `--all`: include low-confidence matches

### `dog get <name>`

Gets one primitive by case-insensitive name. Use sigils to filter type.

```bash
dog get "@User" -p docs
dog get "!Login" -p docs --depth 1
dog get "#AuthService" -p docs -o text
```

Options:
- `--path`, `-p`: file or directory, default `.`
- `--output`, `-o`: `json` or `text`
- `--depth`: include referenced documents up to N hops

### `dog list [sigil]`

Lists primitives, optionally filtered by type.

```bash
dog list -p docs
dog list "!" -p docs
dog list "@" -p docs -o text
```

Sigils:
- `@`: Actors
- `!`: Behaviors
- `#`: Components
- `&`: Data

### `dog refs <name>`

Reverse reference lookup for impact analysis.

```bash
dog refs "#AuthService" -p docs
dog refs "@User" -p docs -o text
```

## Operational Commands

These keep conventional CLI-oriented output defaults.

```bash
dog lint docs
dog format --check docs
dog index docs --name "Project Name"
dog graph "!Login" -p docs
dog export -p docs
dog serve docs
```

Use `dog lint docs` after documentation changes. Use `dog format --check docs` before finishing if docs should remain formatted.
