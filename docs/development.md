# Development Guide

This guide covers development workflows, contributing guidelines, and best practices.

## Development Setup

See the [Getting Started](getting-started.md) guide for initial setup instructions.

## Styling with TailwindCSS v4

Pared uses TailwindCSS v4 with a custom design system.

### Color Palette

The app uses OKLCH color space for vibrant, perceptually uniform colors:

- **Primary**: Bold orange (`oklch(0.70 0.20 35)`) - Energy and appetite appeal
- **Accents**: Warm coral tones for interactive elements
- **Base**: Clean grays for minimalist design

### Making Style Changes

1. Edit `static/globals.css`
2. Run the watch command:
   ```bash
   npm run watch:css
   ```
3. Refresh your browser to see changes

### Custom Styles

All custom styles are defined in `static/globals.css`:

```css
@import "tailwindcss";

/* Custom theme configuration */
@theme {
  --color-primary: oklch(0.70 0.20 35);
  --color-accent: oklch(0.75 0.15 40);
  /* ... */
}
```

## Database Development

### ORM Models

All database models are defined in `models.py`:

- **Recipe** - Recipe metadata (title, source_url, date_added)
- **Ingredient** - Recipe ingredients
- **Direction** - Cooking instructions
- **GroceryList** - Shopping lists

### Adding a New Field

Example: Add a `prep_time` field to recipes

1. **Edit models.py**:
   ```python
   class Recipe(db.Model):
       # ... existing fields ...
       prep_time = db.Column(db.Integer, nullable=True)  # minutes
   ```

2. **Create migration**:
   ```bash
   flask --app recipe_parser db migrate -m "Add prep_time to Recipe"
   ```

3. **Review** the generated migration in `migrations/versions/`

4. **Apply migration**:
   ```bash
   flask --app recipe_parser db upgrade
   ```

5. **Update templates** to display/edit the new field

### Database Queries

Use SQLAlchemy ORM for database operations:

```python
# Get all recipes
recipes = Recipe.query.order_by(Recipe.date_added.desc()).all()

# Get recipe by ID
recipe = Recipe.query.get_or_404(recipe_id)

# Search recipes
results = Recipe.query.filter(Recipe.title.ilike(f'%{query}%')).all()

# Create new recipe
recipe = Recipe(title=title, source_url=source_url)
db.session.add(recipe)
db.session.commit()

# Delete recipe (cascade deletes related ingredients/directions)
db.session.delete(recipe)
db.session.commit()
```

See the [ORM Migration Guide](orm-migration.md) for more details.

## Recipe Parsing

### How It Works

The recipe parser uses multiple strategies to extract data:

1. **Schema.org structured data** (JSON-LD)
2. **HTML element patterns** (class/id names containing "ingredient", "direction", etc.)
3. **Fallback heuristics** for non-standard sites

### Adding New Parsing Logic

Edit the `parse_recipe_html()` function in `recipe_parser.py`:

```python
def parse_recipe_html(url):
    # ... existing parsing logic ...

    # Add new parsing method
    if not ingredients:
        # Try custom parsing logic
        ingredients = custom_ingredient_extractor(soup)

    return {
        "title": title,
        "ingredients": ingredients,
        "directions": directions,
        "source_url": url
    }
```

### Testing Recipe Parsing

1. Run the app locally
2. Enter a recipe URL on the homepage
3. Review extracted ingredients and directions
4. Fix parsing logic if needed

## Code Style

### Python

- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

### HTML/Templates

- Use Jinja2 template inheritance
- Keep templates organized and DRY
- Use TailwindCSS utility classes (avoid custom CSS)

### Database Migrations

- **Always** create migrations for schema changes
- Write descriptive migration messages
- Review migrations before applying
- Commit migrations to version control

## Testing

### Manual Testing

1. **Parse recipes** from various websites
2. **Save and edit** recipes
3. **Search** functionality
4. **Grocery list** generation
5. **Mobile responsiveness**

### Future: Automated Tests

Consider adding:

- Unit tests for parsing logic
- Integration tests for routes
- Database migration tests

## Git Workflow

### Branching

```bash
# Create feature branch
git checkout -b feature/add-prep-time

# Make changes and commit
git add .
git commit -m "Add prep_time field to Recipe model"

# Push to GitHub
git push origin feature/add-prep-time
```

### Commit Messages

Write clear, descriptive commit messages:

-  `Add prep_time field to Recipe model`
-  `Fix recipe parsing for AllRecipes.com`
-  `Update deployment guide with Supabase setup`
- ❌ `Fix bug`
- ❌ `Update stuff`

## Deployment Testing

Before deploying to production:

1. **Test locally** with production environment variables
2. **Run migrations** in test database
3. **Build CSS** for production
4. **Test on mobile** devices

## Performance Considerations

### Database

- Use indexes for frequently queried fields
- Avoid N+1 queries (use `joinedload` or `selectinload`)
- Batch operations when possible

### CSS

- Build CSS with minification for production
- Remove unused Tailwind classes (done automatically)

### Recipe Parsing

- Parsing can be slow (5-15 seconds for complex sites)
- Consider adding a loading indicator
- Cache parsed results if re-parsing same URL

## Common Tasks

### Add a New Route

1. **Define route** in `recipe_parser.py`:
   ```python
   @app.route('/my-route')
   def my_route():
       return render_template('my_template.html')
   ```

2. **Create template** in `templates/my_template.html`

3. **Add navigation link** if needed

### Add a New Model

1. **Define model** in `models.py`:
   ```python
   class MyModel(db.Model):
       __tablename__ = 'my_table'

       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(200), nullable=False)
   ```

2. **Create migration**:
   ```bash
   flask --app recipe_parser db migrate -m "Add MyModel"
   flask --app recipe_parser db upgrade
   ```

3. **Use in routes** via ORM queries

### Update Dependencies

```bash
# Python dependencies
pip install --upgrade package-name
pip freeze > requirements.txt

# Node dependencies
npm update
```

## Troubleshooting Development Issues

### Port Already in Use

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Database Migration Conflicts

```bash
# Reset migrations ( destroys data)
rm -rf migrations/
flask --app recipe_parser db init
flask --app recipe_parser db migrate -m "Initial migration"
flask --app recipe_parser db upgrade
```

### CSS Not Rebuilding

```bash
# Clear npm cache
rm -rf node_modules
npm install
npm run build:css
```

## Resources

- **[Flask Documentation](https://flask.palletsprojects.com/)**
- **[SQLAlchemy Docs](https://docs.sqlalchemy.org/)**
- **[TailwindCSS v4 Docs](https://tailwindcss.com/docs)**
- **[Flask-Migrate Docs](https://flask-migrate.readthedocs.io/)**
- **[BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)**

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Questions?** Open an issue or check the [Getting Started](getting-started.md) guide.
