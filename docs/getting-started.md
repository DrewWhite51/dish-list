# Getting Started

This guide will help you set up Dish List locally for development.

## Prerequisites

- Python 3.10 or higher
- Node.js 18+ (for TailwindCSS)
- A Supabase account (free) for PostgreSQL database

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ez-recipe.git
cd ez-recipe
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Install Node Dependencies

```bash
npm install
```

### 4. Build CSS

```bash
# Build TailwindCSS (production)
npm run build:css

# Or watch for changes during development
npm run watch:css
```

### 5. Set Up Database

#### Create Supabase Database

1. Go to [Supabase](https://supabase.com) and create a free account
2. Create a new project
3. Go to **Project Settings** → **Database**
4. Copy your connection string

#### Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your DATABASE_URL
# Example:
# DATABASE_URL=postgresql://postgres:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

#### Run Database Migrations

```bash
flask --app recipe_parser db upgrade
```

This will create all necessary database tables.

### 6. Run the Application

```bash
python application.py
```

Visit `http://localhost:5000` in your browser!

## What You Can Do

- **Parse a Recipe**: Enter any recipe URL on the homepage
- **Save Recipes**: Recipes are automatically saved to your database after parsing
- **View Collection**: Browse all saved recipes at `/recipes`
- **Search**: Use the search bar to find recipes by title
- **Generate Shopping Lists**: Create combined shopping lists from multiple recipes

## Development Workflow

### CSS Changes

If you're modifying styles in `static/globals.css`:

```bash
# Watch for CSS changes (auto-rebuild)
npm run watch:css
```

### Database Schema Changes

If you modify `models.py`:

```bash
# Create a new migration
flask --app recipe_parser db migrate -m "Description of changes"

# Apply the migration
flask --app recipe_parser db upgrade
```

See the [ORM Migration Guide](orm-migration.md) for more details.

## Project Structure

```
ez-recipe/
├── application.py              # Entry point (loads .env)
├── recipe_parser.py            # Flask app, routes, parsing logic
├── models.py                   # SQLAlchemy ORM models
│
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
│
├── migrations/                 # Database migrations (Alembic)
│   └── versions/               # Migration files
│
├── templates/                  # HTML templates (Jinja2)
│   ├── index.html             # Homepage
│   ├── result.html            # Parsed recipe preview
│   ├── recipe.html            # Recipe detail view
│   ├── recipes.html           # Recipe list
│   └── ...
│
├── static/                     # Static assets
│   ├── globals.css            # TailwindCSS source
│   └── output.css             # Compiled CSS (generated)
│
└── docs/                       # Documentation
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string from Supabase | Yes |

Example `.env` file:

```bash
DATABASE_URL=postgresql://postgres:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Note**: The application automatically strips the `?pgbouncer=true` parameter if present.

## Troubleshooting

### Database Connection Error

**Error**: `ValueError: DATABASE_URL environment variable not set`

**Solution**: Make sure you've created a `.env` file with your DATABASE_URL.

### Migration Error

**Error**: `Can't locate revision identified by 'xxxxx'`

**Solution**: Delete the `migrations/` directory and reinitialize:

```bash
rm -rf migrations/
flask --app recipe_parser db init
flask --app recipe_parser db migrate -m "Initial migration"
flask --app recipe_parser db upgrade
```

### CSS Not Updating

**Problem**: CSS changes aren't reflected in the browser

**Solution**: Rebuild CSS manually:

```bash
npm run build:css
```

Or use watch mode during development:

```bash
npm run watch:css
```

### Recipe Parsing Fails

**Error**: `403 Forbidden` or `Access denied`

**Reason**: Some recipe websites block scraping or require authentication.

**Solution**: This is expected behavior. Not all websites allow parsing. Try a different recipe URL.

## Next Steps

- **[Deploy your app](deployment.md)** - Deploy to Render + Supabase for free
- **[Learn about ORM](orm-migration.md)** - Understand the database structure
- **[Development guide](development.md)** - Contributing to the project
- **[API reference](api-reference.md)** - Explore routes and models

## Common Commands

```bash
# Start development server
python application.py

# Watch CSS changes
npm run watch:css

# Create migration
flask --app recipe_parser db migrate -m "Add field"

# Apply migration
flask --app recipe_parser db upgrade

# Rollback migration
flask --app recipe_parser db downgrade

# Run tests (if available)
pytest
```

---

**Questions?** Open an issue on GitHub or check the [Development Guide](development.md).
