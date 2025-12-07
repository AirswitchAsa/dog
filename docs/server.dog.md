# Component: Server

## Description

FastAPI-based web server that renders `&DogDocument` files as HTML pages. Provides a local documentation browser with color-coded reference links and hot-reload support. Uses marko for Markdown-to-HTML conversion.

## State

- docs_path: root directory containing .dog.md files
- docs: list of loaded DogDocument instances
- docs_by_name: lookup map for fast document retrieval
- favicon_path: optional path to favicon.png or dog.png

## Events

- load_docs: reload all documents from disk
- index_route: serve homepage (index.dog.md or document list)
- doc_route: serve individual document as HTML
- favicon_route: serve favicon if available

## Notes

- Uses Inter font with MoMA-inspired minimalist design
- Reference sigils (@, !, #, &) converted to colored links
- Relative .dog.md links converted to /doc/ routes
- Hot-reload via watchfiles monitors docs directory
