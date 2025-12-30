# Documentation

This directory contains the documentation for Pared, built with [MkDocs](https://www.mkdocs.org/) and the [Material theme](https://squidfunk.github.io/mkdocs-material/).

## Viewing Documentation

### Option 1: Local Development Server (Recommended)

```bash
# Install documentation dependencies
pip install -r requirements-docs.txt

# Start the development server
mkdocs serve
```

Then visit `http://localhost:8000` to view the documentation with live reload.

### Option 2: Build Static Site

```bash
# Build documentation to site/ directory
mkdocs build

# Serve the static site
cd site && python -m http.server 8000
```

### Option 3: Read Markdown Directly

All documentation is written in Markdown and can be read directly:

- [index.md](index.md) - Documentation homepage
- [getting-started.md](getting-started.md) - Setup guide
- [deployment.md](deployment.md) - Deployment instructions
- [development.md](development.md) - Development guide
- [orm-migration.md](orm-migration.md) - Database ORM guide
- [api-reference.md](api-reference.md) - API documentation

## Documentation Structure

```
docs/
├── README.md               # This file
├── index.md                # Documentation homepage
├── getting-started.md      # Installation and setup
├── deployment.md           # Deployment guide (Render + Supabase)
├── development.md          # Development workflows
├── orm-migration.md        # SQLAlchemy ORM and migrations
└── api-reference.md        # Routes and models reference
```

## Editing Documentation

1. Edit Markdown files in this directory
2. Run `mkdocs serve` to preview changes
3. Commit changes to git

### Adding New Pages

1. Create a new `.md` file in `docs/`
2. Add it to `nav` section in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Your New Page: your-new-page.md
```

## MkDocs Configuration

Configuration is in [`mkdocs.yml`](../mkdocs.yml) at the project root.

Key features enabled:

- **Material theme** with light/dark mode
- **Code syntax highlighting** with copy button
- **Search** functionality
- **Navigation tabs** and sections
- **Admonitions** (note, warning, info boxes)

## Building for Deployment

To deploy documentation to GitHub Pages:

```bash
# Build and deploy
mkdocs gh-deploy
```

This builds the docs and pushes to the `gh-pages` branch.

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)
