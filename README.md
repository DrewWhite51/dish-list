# Pared

Parse food recipes from URLs and create grocery lists.

## Features

- **Recipe Parsing**: Extracts ingredients and directions from recipe websites
- **Recipe Storage**: Save and manage your recipe collection
- **Search**: Find recipes by title
- **Modern UI**: Clean, responsive design with TailwindCSS
- **Dark Mode Support**: Automatic dark mode styling
- **Lightweight**: Only 3 Python dependencies

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install CSS dependencies and build styles
npm install
npm run build:css

# Run the app
python application.py
```

Access at `http://localhost:5000`

## Requirements

- Python 3.13+
- Flask, requests, beautifulsoup4
- Node.js (for TailwindCSS build process)

## What You Can Do

- **Parse Recipes**: Enter any recipe URL to extract ingredients and directions
- **Save & Organize**: Build your recipe collection
- **Search**: Find recipes by title
- **Edit Recipes**: Modify saved recipes as needed

## Project Structure

```
ez-recipe/
├── application.py          # Entry point
├── recipe_parser.py        # Routes and parsing logic
├── recipe_database.py      # CSV storage
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies
├── tailwind.config.js      # TailwindCSS configuration
├── templates/              # HTML templates with TailwindCSS classes
├── static/
│   ├── globals.css         # TailwindCSS source file with custom styles
│   └── output.css          # Compiled CSS (generated)
└── db/                     # Recipe storage (auto-created)
```

## Styling & Design

The application uses a modern design system powered by TailwindCSS with:

- **Bold orange primary color** for energy and appetite appeal
- **Warm coral accents** for interactive elements
- **Clean minimalist base** with subtle grays
- **Full dark mode support** with automatic theme switching
- **Responsive design** that works on mobile, tablet, and desktop

### Development Workflow

When making style changes:

```bash
# Watch for CSS changes during development
npm run watch:css

# Build for production (minified)
npm run build:css
```

## How It Works

The app uses HTML-based parsing to extract recipe data from websites. It looks for structured data (schema.org markup) and common recipe patterns to identify ingredients and cooking directions.

## License

MIT
