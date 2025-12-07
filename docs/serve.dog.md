# Behavior: Serve

## Condition

- `@User` wants to view DOG documentation in a web browser
- `@User` has a directory with `.dog.md` files

## Description

The `@User` runs the `dog serve` command with an optional path. The `#CLI` invokes `#Server` to start a local web server that renders all `&DogDocument` files as HTML pages.

Key features:
- Hot-reload support for automatic refresh on file changes
- Color-coded reference links (red=Actor, blue=Behavior, purple=Component, green=Data)
- MoMA-inspired minimalist design with Inter font
- Automatic favicon discovery (favicon.png or dog.png)
- Renders index.dog.md as homepage when present

## Outcome

- Web server starts at specified host:port (default: 127.0.0.1:8000)
- Documents accessible at /doc/{name} routes
- Homepage shows index.dog.md content or document list
- Reference links convert to clickable colored links
- Exit on Ctrl+C

## Notes

- Uses FastAPI and uvicorn for serving
- Hot-reload enabled by default (disable with --no-reload)
- Cross-references like `@User` become clickable links
- Relative .dog.md links automatically converted to /doc/ routes
