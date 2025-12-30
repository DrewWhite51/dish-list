# API Reference

Complete reference for routes, models, and database schema.

## Routes

### Homepage

```
GET /
```

Displays the homepage with a recipe URL input form and list of recently saved recipes.

**Response**: HTML page with recipe parser form

---

### Parse Recipe

```
POST /parse
```

Parses a recipe from the provided URL.

**Form Data**:
- `recipe_url` (string, required) - URL of the recipe to parse

**Response**:
- If recipe already exists: Redirect to `/recipe/<id>`
- If successful: HTML page showing parsed ingredients and directions for confirmation
- If error: HTML page with error message

**Example**:
```html
<form action="/parse" method="POST">
  <input type="text" name="recipe_url" value="https://example.com/recipe">
  <button type="submit">Parse Recipe</button>
</form>
```

---

### Save Recipe

```
POST /save
```

Saves a parsed recipe to the database.

**Form Data**:
- `title` (string, required) - Recipe title
- `source_url` (string, required) - Original recipe URL
- `ingredients` (array of strings) - List of ingredients
- `directions` (array of strings) - List of cooking directions

**Response**: Redirect to `/recipe/<id>`

---

### View Recipe

```
GET /recipe/<int:recipe_id>
```

Displays a single recipe with all details.

**Parameters**:
- `recipe_id` (integer) - Recipe ID

**Response**: HTML page showing recipe details

**Error**: 404 if recipe not found

---

### List All Recipes

```
GET /recipes
```

Shows all saved recipes, ordered by date added (newest first).

**Response**: HTML page with recipe list

---

### Search Recipes

```
GET /search?q=<query>
```

Search for recipes by title (case-insensitive).

**Query Parameters**:
- `q` (string, required) - Search query

**Response**: HTML page with search results

**Example**: `/search?q=chicken`

---

### Edit Recipe

```
GET /edit/<int:recipe_id>
POST /edit/<int:recipe_id>
```

Display and update recipe.

**Parameters**:
- `recipe_id` (integer) - Recipe ID

**GET Response**: HTML form with current recipe data

**POST Form Data**:
- `title` (string) - Updated title
- `source_url` (string) - Updated source URL
- `ingredients` (array) - Updated ingredients
- `directions` (array) - Updated directions

**POST Response**: Redirect to `/recipe/<id>`

---

### Delete Recipe

```
POST /delete/<int:recipe_id>
```

Deletes a recipe and all related data (ingredients, directions, grocery lists).

**Parameters**:
- `recipe_id` (integer) - Recipe ID

**Response**: Redirect to `/recipes`

---

### Generate Grocery List

```
POST /generate_grocery_list/<int:recipe_id>
```

Creates a grocery list from recipe ingredients.

**Parameters**:
- `recipe_id` (integer) - Recipe ID

**Response**: Redirect to `/recipe/<id>`

---

## Database Models

### Recipe

Stores recipe metadata.

**Table**: `recipes`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing ID |
| `title` | String(500) | Not Null | Recipe title |
| `source_url` | String(1000) | Not Null | Original recipe URL |
| `date_added` | DateTime | Not Null, Default: now | When recipe was added |

**Relationships**:
- `ingredients` - One-to-many with Ingredient (cascade delete)
- `directions` - One-to-many with Direction (cascade delete)
- `grocery_lists` - One-to-many with GroceryList (cascade delete)

**Methods**:

```python
recipe.to_dict()
# Returns full recipe as dictionary with all related data

recipe.to_dict_minimal()
# Returns recipe metadata only (id, title, source_url, date_added)
```

**Example**:

```python
from models import Recipe, db

# Create new recipe
recipe = Recipe(
    title="Chocolate Chip Cookies",
    source_url="https://example.com/cookies"
)
db.session.add(recipe)
db.session.commit()

# Query recipes
all_recipes = Recipe.query.all()
recent = Recipe.query.order_by(Recipe.date_added.desc()).limit(10).all()
search = Recipe.query.filter(Recipe.title.ilike('%chocolate%')).all()
```

---

### Ingredient

Stores recipe ingredients.

**Table**: `ingredients`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing ID |
| `recipe_id` | Integer | Foreign Key → recipes.id | Recipe this ingredient belongs to |
| `ingredient` | Text | Not Null | Ingredient text |

**Relationships**:
- `recipe` - Many-to-one with Recipe

**Example**:

```python
from models import Ingredient, db

# Add ingredient to recipe
ingredient = Ingredient(
    recipe_id=recipe.id,
    ingredient="2 cups all-purpose flour"
)
db.session.add(ingredient)
db.session.commit()

# Access via recipe
for ing in recipe.ingredients:
    print(ing.ingredient)
```

---

### Direction

Stores cooking directions/steps.

**Table**: `directions`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing ID |
| `recipe_id` | Integer | Foreign Key → recipes.id | Recipe this direction belongs to |
| `step_number` | Integer | Not Null | Step number for ordering |
| `direction` | Text | Not Null | Direction text |

**Relationships**:
- `recipe` - Many-to-one with Recipe

**Example**:

```python
from models import Direction, db

# Add direction to recipe
direction = Direction(
    recipe_id=recipe.id,
    step_number=1,
    direction="Preheat oven to 350°F"
)
db.session.add(direction)
db.session.commit()

# Access via recipe (sorted by step_number)
sorted_directions = sorted(recipe.directions, key=lambda x: x.step_number)
```

---

### GroceryList

Stores grocery lists generated from recipes.

**Table**: `grocery_lists`

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Auto-incrementing ID |
| `recipe_id` | Integer | Foreign Key → recipes.id | Recipe this list belongs to |
| `category` | String(200) | Not Null | Category name (e.g., "Items") |
| `items` | JSON | Not Null | Array of item strings |

**Relationships**:
- `recipe` - Many-to-one with Recipe

**Methods**:

```python
grocery_list.get_items()
# Returns items as a list
```

**Example**:

```python
from models import GroceryList, db

# Create grocery list
grocery_list = GroceryList(
    recipe_id=recipe.id,
    category="Dairy",
    items=["2 cups milk", "1 stick butter"]
)
db.session.add(grocery_list)
db.session.commit()
```

---

## Database Schema

```sql
-- Recipes table
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    source_url VARCHAR(1000) NOT NULL,
    date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Ingredients table
CREATE TABLE ingredients (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient TEXT NOT NULL
);

-- Directions table
CREATE TABLE directions (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    direction TEXT NOT NULL
);

-- Grocery lists table
CREATE TABLE grocery_lists (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    category VARCHAR(200) NOT NULL,
    items JSON NOT NULL
);
```

---

## Error Responses

### 404 Not Found

Returned when a recipe ID doesn't exist.

**Example**: `GET /recipe/999` (non-existent ID)

### Parsing Errors

When recipe parsing fails, the result template shows an error message.

**Common errors**:
- `403 Forbidden` - Website blocks scraping
- `Connection error` - Network issues
- `Request timed out` - Website took too long to respond

---

## Example Usage

### Complete Recipe Creation Flow

```python
from models import Recipe, Ingredient, Direction, db

# 1. Create recipe
recipe = Recipe(
    title="Chocolate Cake",
    source_url="https://example.com/cake"
)
db.session.add(recipe)
db.session.flush()  # Get ID without committing

# 2. Add ingredients
ingredients = [
    "2 cups flour",
    "1 cup sugar",
    "1/2 cup cocoa powder"
]
for ing_text in ingredients:
    ing = Ingredient(recipe_id=recipe.id, ingredient=ing_text)
    db.session.add(ing)

# 3. Add directions
directions = [
    "Preheat oven to 350°F",
    "Mix dry ingredients",
    "Bake for 30 minutes"
]
for step_num, dir_text in enumerate(directions, 1):
    dir = Direction(recipe_id=recipe.id, step_number=step_num, direction=dir_text)
    db.session.add(dir)

# 4. Commit everything
db.session.commit()

# 5. Retrieve and display
saved_recipe = Recipe.query.get(recipe.id)
print(saved_recipe.to_dict())
```

---

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |

**Format**: `postgresql://user:password@host:port/database`

**Example**: `postgresql://postgres:pass@localhost:5432/recipes`

### SQLAlchemy Configuration

Configured in `recipe_parser.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,      # Test connections before using
    'pool_recycle': 300,        # Recycle connections after 5 minutes
}
```

---

## Further Reading

- **[Getting Started](getting-started.md)** - Setup guide
- **[ORM Migration Guide](orm-migration.md)** - Database migrations
- **[Development Guide](development.md)** - Contributing
- **[Deployment Guide](deployment.md)** - Deploy to production
