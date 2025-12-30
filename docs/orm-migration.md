# SQLAlchemy ORM Migration Summary

## What Was Changed

The application has been migrated from a custom PostgreSQL wrapper to **SQLAlchemy ORM** with **Flask-Migrate** for database migrations.

## Benefits

### 1. **Object-Relational Mapping (ORM)**
- Database records are now Python objects (Recipe, Ingredient, Direction, GroceryList)
- No more manual SQL queries - use Python methods instead
- Type hints and IDE autocomplete for database fields

### 2. **Database Migrations**
- Schema changes are tracked in version-controlled migration files
- Easy to roll back changes if needed
- Automatic migration application during deployment
- No more manual SQL scripts

### 3. **Better Code Quality**
- Cleaner, more maintainable code
- Relationships between models are explicit and typed
- Cascade deletes handled automatically by the ORM

### 4. **Development Workflow**
- Change models.py → Generate migration → Apply migration
- No need to manually write CREATE TABLE or ALTER TABLE statements
- Database schema is always in sync with code

## Files Changed

### New Files
- **models.py** - SQLAlchemy ORM models (Recipe, Ingredient, Direction, GroceryList)
- **migrations/** - Database migration files (Alembic)
- **ORM_MIGRATION.md** - This documentation

### Modified Files
- **recipe_parser.py** - Updated all routes to use SQLAlchemy ORM instead of custom database wrapper
- **requirements.txt** - Added SQLAlchemy, Flask-SQLAlchemy, Flask-Migrate
- **render.yaml** - Added `flask db upgrade` to build command
- **README.md** - Added database migrations section

### Renamed Files
- **recipe_database.py** → **recipe_database_legacy.py** - Old implementation (no longer used)

## Database Models

### Recipe Model
```python
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    source_url = db.Column(db.String(1000), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    ingredients = db.relationship('Ingredient', backref='recipe', cascade='all, delete-orphan')
    directions = db.relationship('Direction', backref='recipe', cascade='all, delete-orphan')
    grocery_lists = db.relationship('GroceryList', backref='recipe', cascade='all, delete-orphan')
```

### Ingredient Model
```python
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'))
    ingredient = db.Column(db.Text, nullable=False)
```

### Direction Model
```python
class Direction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'))
    step_number = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.Text, nullable=False)
```

### GroceryList Model
```python
class GroceryList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'))
    category = db.Column(db.String(200), nullable=False)
    items = db.Column(db.JSON, nullable=False)
```

## Code Examples

### Before (Custom Wrapper)
```python
# Old way
recipes = db.get_all_recipes()
recipe = db.get_recipe_by_id(recipe_id)
recipe_id = db.save_recipe(recipe_data)
db.delete_recipe(recipe_id)
```

### After (SQLAlchemy ORM)
```python
# New way - much cleaner!
recipes = Recipe.query.order_by(Recipe.date_added.desc()).all()
recipe = Recipe.query.get_or_404(recipe_id)

# Save recipe
recipe = Recipe(title=title, source_url=source_url)
db.session.add(recipe)
db.session.commit()

# Delete recipe (cascade deletes ingredients/directions automatically)
db.session.delete(recipe)
db.session.commit()

# Search recipes
results = Recipe.query.filter(Recipe.title.ilike(f'%{query}%')).all()
```

## Migration Commands

### Initial Setup (Already Done)
```bash
# Initialize migrations directory
flask --app recipe_parser db init

# Create initial migration
flask --app recipe_parser db migrate -m "Initial migration"

# Apply migration to database
flask --app recipe_parser db upgrade
```

### Future Schema Changes

1. **Modify models.py** - Add/remove fields or models
2. **Generate migration**:
   ```bash
   flask --app recipe_parser db migrate -m "Add new field to Recipe"
   ```
3. **Review migration** in `migrations/versions/`
4. **Apply migration**:
   ```bash
   flask --app recipe_parser db upgrade
   ```

### Rollback if Needed
```bash
# Rollback the last migration
flask --app recipe_parser db downgrade

# Rollback to specific version
flask --app recipe_parser db downgrade <revision_id>
```

## Deployment

Migrations are automatically applied during Render deployment via the build command:

```yaml
buildCommand: pip install -r requirements.txt && npm install && npm run build:css && rm -rf node_modules && flask --app recipe_parser db upgrade
```

This ensures the database schema is always up-to-date with the code.

## Bug Fixes Included

### 1. Fixed pgbouncer Parameter Error
**Problem**: Supabase connection strings include `?pgbouncer=true` which psycopg/SQLAlchemy don't recognize.

**Solution**: Strip the parameter before connecting:
```python
database_url = database_url.replace('?pgbouncer=true', '')
```

### 2. Fixed psycopg2 vs psycopg Driver Issue
**Problem**: SQLAlchemy defaults to psycopg2 driver, but we're using psycopg v3.

**Solution**: Replace connection string protocol:
```python
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
```

### 3. Fixed Python 3.13 Compatibility
**Problem**: SQLAlchemy 2.0.23 has compatibility issues with Python 3.13.

**Solution**: Updated to SQLAlchemy >= 2.0.35 in requirements.txt.

## Testing

The application has been tested and verified:
-  Database connection works with Supabase PostgreSQL
-  Migrations apply successfully
-  Application starts without errors
-  All routes updated to use ORM models

## Next Steps

1. **Test the application** locally to ensure all features work
2. **Deploy to Render** with the DATABASE_URL environment variable
3. **Future enhancements** can easily add new fields via migrations

## Example: Adding a New Field

Let's say you want to add a `prep_time` field to recipes:

1. **Edit models.py**:
   ```python
   class Recipe(db.Model):
       # ... existing fields ...
       prep_time = db.Column(db.Integer, nullable=True)  # minutes
   ```

2. **Generate migration**:
   ```bash
   flask --app recipe_parser db migrate -m "Add prep_time to Recipe"
   ```

3. **Review the generated migration** in `migrations/versions/`

4. **Apply migration**:
   ```bash
   flask --app recipe_parser db upgrade
   ```

5. **Update templates/forms** to display/edit the new field

6. **Commit** both the model changes and migration file

That's it! The ORM handles all the SQL for you.

## Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

**Migration completed successfully!** 
