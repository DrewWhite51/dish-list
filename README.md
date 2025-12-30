# Pared

> A lightweight recipe parser that extracts ingredients and directions from any recipe URL

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/ez-recipe)

## Features

- 🍳 **Parse Recipes** - Extract ingredients and directions from any recipe website
- 💾 **PostgreSQL Storage** - Persistent storage with SQLAlchemy ORM
- 🔍 **Search** - Find recipes by title
- ✨ **Modern UI** - Clean, responsive design with TailwindCSS v4
- 🆓 **Free Hosting** - Deploy on Render + Supabase for $0/month

## Quick Start

```bash
# 1. Clone and install dependencies
git clone https://github.com/YOUR_USERNAME/ez-recipe.git
cd ez-recipe
pip install -r requirements.txt
npm install

# 2. Build CSS
npm run build:css

# 3. Set up database
cp .env.example .env
# Edit .env and add your Supabase DATABASE_URL

# 4. Run migrations and start app
flask --app recipe_parser db upgrade
python application.py
```

Visit `http://localhost:5000` 🎉

## Tech Stack

- **Backend**: Flask (Python 3.10+)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Frontend**: TailwindCSS v4
- **Deployment**: Render.com + Supabase

## Documentation

📚 **[Full Documentation](docs/)** - Detailed guides and references

- **[Getting Started](docs/getting-started.md)** - Complete setup guide
- **[Deployment Guide](docs/deployment.md)** - Deploy to Render + Supabase ($0/month)
- **[ORM & Migrations](docs/orm-migration.md)** - Database schema management
- **[Development Guide](docs/development.md)** - Contributing and workflows
- **[API Reference](docs/api-reference.md)** - Routes and models

### View Documentation Locally

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve documentation at http://localhost:8000
mkdocs serve
```

## Deployment

Deploy for free using Render + Supabase:

1. **[Set up Supabase](docs/deployment.md#supabase-setup)** - Free PostgreSQL database
2. **[Deploy to Render](docs/deployment.md#render-deployment)** - Free web hosting
3. **Done!** - Your recipe parser is live at `https://your-app.onrender.com`

See the **[Deployment Guide](docs/deployment.md)** for detailed instructions.

## Project Structure

```
ez-recipe/
├── application.py          # Entry point (loads .env)
├── recipe_parser.py        # Flask app and routes
├── models.py               # SQLAlchemy ORM models
├── requirements.txt        # Python dependencies
├── migrations/             # Database migrations
├── templates/              # HTML templates
├── static/                 # CSS and assets
└── docs/                   # Documentation
```

## Contributing

Contributions welcome! Please see the [Development Guide](docs/development.md) for setup instructions.

## License

MIT License - feel free to use this project however you'd like!

---

**Need help?** Check out the [documentation](docs/) or open an issue.
