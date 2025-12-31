# Pared Documentation

Welcome to the Pared recipe parser documentation!

## What is Pared?

Pared is a lightweight web application that parses recipes from any URL and helps you build your personal recipe collection. Save recipes, search your collection, and generate grocery lists with ease.

## Quick Links

- **[Getting Started](getting-started.md)** - Installation and setup guide
- **[Security & Abuse Protection](security.md)** - Rate limiting, SSRF protection, and budget controls
- **[Database & ORM](orm-migration.md)** - SQLAlchemy ORM and migrations
- **[Deployment](deployment.md)** - Deploy to Render + Supabase ($0/month)
- **[Development](development.md)** - Contributing and development workflow
- **[API Reference](api-reference.md)** - Routes and models documentation

## Features

- **Recipe Parsing**: Extract ingredients and directions from any recipe website
- **Recipe Storage**: PostgreSQL database with SQLAlchemy ORM
- **Search**: Find recipes by title with full-text search
- **Abuse Protection**: Rate limiting (20/hour), SSRF protection, and daily budget controls
- **Admin Dashboard**: Real-time API usage monitoring and cost tracking
- **Modern UI**: Clean, responsive design with TailwindCSS v4
- **Free Hosting**: Deploy on Render + Supabase for $0/month

## Technology Stack

- **Backend**: Flask (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: TailwindCSS v4
- **Deployment**: Render.com + Supabase
- **Migrations**: Flask-Migrate (Alembic)

## Contributing

Contributions are welcome! Please see the [Development Guide](development.md) for details on setting up your development environment.

## License

This project is open source and available under the MIT License.
