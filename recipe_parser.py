# recipe_parser.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from bs4 import BeautifulSoup
import re
import os
from models import db, Recipe, Ingredient, Direction, GroceryList
from flask_migrate import Migrate

app = Flask(__name__)

# Configure SQLAlchemy
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError("DATABASE_URL environment variable not set")

# Remove pgbouncer parameter if present (not supported by SQLAlchemy)
database_url = database_url.replace('?pgbouncer=true', '')

# Replace postgresql:// with postgresql+psycopg:// to use psycopg driver
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

def parse_recipe_html(url):
    """
    Traditional HTML-based recipe parsing.
    This is the original parsing method that looks for HTML patterns.
    """
    try:
        # Enhanced headers to look more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }
        
        # Use a session to maintain cookies
        import time
        session = requests.Session()
        
        # Add a small delay to be more respectful to servers
        time.sleep(1.5)
        
        # Make request to the URL with the session
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract ingredients - look for common patterns in recipe websites
        ingredients = []
        recipe_schema = None  # Initialize recipe_schema to None
        
        # Method 1: Look for elements with 'ingredient' in class or id
        ingredient_elements = soup.find_all(class_=lambda c: c and 'ingredient' in c.lower())
        if not ingredient_elements:
            ingredient_elements = soup.find_all(id=lambda i: i and 'ingredient' in i.lower())
        
        # Method 2: Look for <li> elements within lists that might contain ingredients
        if not ingredients:
            for element in ingredient_elements:
                ingredient_text = element.get_text().strip()
                if ingredient_text and len(ingredient_text) < 200:  # Reasonable length for an ingredient
                    ingredients.append(ingredient_text)
        
        # Method 3: Look for schema.org structured data (common in modern recipe sites)
        if not ingredients:
            recipe_schema = soup.find('script', {'type': 'application/ld+json'})
            if recipe_schema:
                import json
                try:
                    schema_data = json.loads(recipe_schema.string)
                    # Handle both direct and nested recipe formats
                    if isinstance(schema_data, list):
                        schema_data = schema_data[0]
                    
                    if '@type' in schema_data and schema_data['@type'] == 'Recipe':
                        if 'recipeIngredient' in schema_data:
                            ingredients = schema_data['recipeIngredient']
                    elif '@graph' in schema_data:
                        for item in schema_data['@graph']:
                            if '@type' in item and item['@type'] == 'Recipe':
                                if 'recipeIngredient' in item:
                                    ingredients = item['recipeIngredient']
                                    break
                except:
                    pass  # Continue if JSON parsing fails
        
        # Extract directions using similar methods
        directions = []
        schema_data = None  # Initialize schema_data to None
        
        # Method 1: Look for elements with 'direction', 'instruction', or 'step' in class or id
        direction_elements = soup.find_all(class_=lambda c: c and any(x in c.lower() for x in ['direction', 'instruction', 'step']))
        if not direction_elements:
            direction_elements = soup.find_all(id=lambda i: i and any(x in i.lower() for x in ['direction', 'instruction', 'step']))
        
        for element in direction_elements:
            direction_text = element.get_text().strip()
            if direction_text and len(direction_text) < 500:  # Reasonable length for a direction
                directions.append(direction_text)
        
        # Method 2: Look for schema.org structured data
        if not directions and recipe_schema:  # Only enter if recipe_schema exists
            try:
                if not schema_data:  # Only parse if schema_data is not already defined
                    schema_data = json.loads(recipe_schema.string)
                    if isinstance(schema_data, list):
                        schema_data = schema_data[0]
                
                if '@type' in schema_data and schema_data['@type'] == 'Recipe':
                    if 'recipeInstructions' in schema_data:
                        instructions = schema_data['recipeInstructions']
                        if isinstance(instructions, list):
                            for instruction in instructions:
                                if isinstance(instruction, str):
                                    directions.append(instruction)
                                elif isinstance(instruction, dict) and 'text' in instruction:
                                    directions.append(instruction['text'])
                elif '@graph' in schema_data:
                    for item in schema_data['@graph']:
                        if '@type' in item and item['@type'] == 'Recipe':
                            if 'recipeInstructions' in item:
                                instructions = item['recipeInstructions']
                                if isinstance(instructions, list):
                                    for instruction in instructions:
                                        if isinstance(instruction, str):
                                            directions.append(instruction)
                                        elif isinstance(instruction, dict) and 'text' in instruction:
                                            directions.append(instruction['text'])
                                break
            except:
                pass  # Continue if parsing fails
        
        # Clean up the extracted data
        ingredients = [re.sub(r'\s+', ' ', i).strip() for i in ingredients if i.strip()]
        
        # Clean up ingredients to remove duplicates and fragments
        ingredients = clean_ingredients(ingredients)
        
        directions = [re.sub(r'\s+', ' ', d).strip() for d in directions if d.strip()]
        
        # Try to extract recipe title
        title = ""
        title_element = soup.find('h1')
        if title_element:
            title = title_element.get_text().strip()
        
        return {
            "title": title,
            "ingredients": ingredients,
            "directions": directions,
            "source_url": url
        }
    
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response.status_code == 403:
            return {
                "error": f"Access denied (403 Forbidden). This website may not allow scraping: {url}",
                "ingredients": [],
                "directions": [],
                "source_url": url
            }
        else:
            return {
                "error": f"HTTP Error: {str(e)}",
                "ingredients": [],
                "directions": [],
                "source_url": url
            }
    except requests.exceptions.ConnectionError:
        return {
            "error": f"Connection error - could not connect to {url}",
            "ingredients": [],
            "directions": [],
            "source_url": url
        }
    except requests.exceptions.Timeout:
        return {
            "error": f"Request timed out for {url}",
            "ingredients": [],
            "directions": [],
            "source_url": url
        }
    except Exception as e:
        return {
            "error": str(e),
            "ingredients": [],
            "directions": [],
            "source_url": url
        }

def parse_recipe(url):
    """
    Parse a recipe URL to extract ingredients and directions using HTML parsing.
    """
    print(f"Using HTML parsing for {url}")
    return parse_recipe_html(url)


def clean_ingredients(ingredients):
    """
    Clean up ingredient list by removing duplicates and fragments.
    Prioritize longer, more complete ingredient descriptions.
    """
    if not ingredients:
        return []
        
    # Sort ingredients by length (descending) to prioritize complete descriptions
    sorted_ingredients = sorted(ingredients, key=len, reverse=True)
    
    # Initialize list for cleaned ingredients
    cleaned = []
    
    for ingredient in sorted_ingredients:
        # Skip very short ingredients (likely fragments)
        if len(ingredient) < 5:
            continue
            
        # Check if this ingredient is already a subset of an existing one
        is_subset = False
        for existing in cleaned:
            if ingredient.lower() in existing.lower():
                is_subset = True
                break
                
        if not is_subset:
            # Add to cleaned list if it's not a subset of an existing ingredient
            cleaned.append(ingredient)
    
    return cleaned


# Routes
@app.route('/')
def index():
    # Get all saved recipes to display on the homepage
    recipes = Recipe.query.order_by(Recipe.date_added.desc()).all()
    recipes_data = [recipe.to_dict_minimal() for recipe in recipes]
    return render_template('index.html', recipe=None, recipes=recipes_data)

@app.route('/parse', methods=['POST'])
def parse():
    url = request.form.get('recipe_url')
    if not url:
        return jsonify({"error": "No URL provided"})

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Check if this recipe URL already exists in the database
    existing_recipe = Recipe.query.filter_by(source_url=url).first()
    if existing_recipe:
        # Recipe already exists, redirect to its page
        return redirect(url_for('view_recipe', recipe_id=existing_recipe.id))

    # Parse the recipe
    result = parse_recipe(url)

    # Pass to template for confirmation before saving
    return render_template('result.html', recipe=result)

@app.route('/save', methods=['POST'])
def save_recipe():
    # Extract recipe data from form
    title = request.form.get('title')
    source_url = request.form.get('source_url')
    ingredients_list = request.form.getlist('ingredients')
    directions_list = request.form.getlist('directions')

    # Check if recipe already exists
    existing_recipe = Recipe.query.filter_by(source_url=source_url).first()
    if existing_recipe:
        # Redirect to existing recipe
        return redirect(url_for('view_recipe', recipe_id=existing_recipe.id))

    # Create new recipe
    recipe = Recipe(title=title, source_url=source_url)
    db.session.add(recipe)
    db.session.flush()  # Get the recipe ID before committing

    # Add ingredients
    for ingredient_text in ingredients_list:
        if ingredient_text.strip():
            ingredient = Ingredient(recipe_id=recipe.id, ingredient=ingredient_text)
            db.session.add(ingredient)

    # Add directions
    for step_number, direction_text in enumerate(directions_list, 1):
        if direction_text.strip():
            direction = Direction(recipe_id=recipe.id, step_number=step_number, direction=direction_text)
            db.session.add(direction)

    db.session.commit()

    # Redirect to the saved recipe
    return redirect(url_for('view_recipe', recipe_id=recipe.id))

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    # Get recipe from database
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe.html', recipe=recipe.to_dict())

@app.route('/recipes')
def list_recipes():
    # Get all recipes from database
    recipes = Recipe.query.order_by(Recipe.date_added.desc()).all()
    recipes_data = [recipe.to_dict_minimal() for recipe in recipes]
    return render_template('recipes.html', recipes=recipes_data)

@app.route('/delete/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        db.session.delete(recipe)
        db.session.commit()
        return redirect(url_for('list_recipes'))
    else:
        return redirect(url_for('view_recipe', recipe_id=recipe_id, error="Failed to delete recipe"))

@app.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    # Get existing recipe
    recipe = Recipe.query.get_or_404(recipe_id)

    if request.method == 'POST':
        # Update recipe metadata
        recipe.title = request.form.get('title')
        recipe.source_url = request.form.get('source_url')

        # Delete existing ingredients and directions
        Ingredient.query.filter_by(recipe_id=recipe_id).delete()
        Direction.query.filter_by(recipe_id=recipe_id).delete()

        # Add updated ingredients
        for ingredient_text in request.form.getlist('ingredients'):
            if ingredient_text.strip():
                ingredient = Ingredient(recipe_id=recipe_id, ingredient=ingredient_text)
                db.session.add(ingredient)

        # Add updated directions
        for step_number, direction_text in enumerate(request.form.getlist('directions'), 1):
            if direction_text.strip():
                direction = Direction(recipe_id=recipe_id, step_number=step_number, direction=direction_text)
                db.session.add(direction)

        db.session.commit()
        return redirect(url_for('view_recipe', recipe_id=recipe_id))

    # Show edit form
    return render_template('edit_recipe.html', recipe=recipe.to_dict())

@app.route('/generate_grocery_list/<int:recipe_id>', methods=['POST'])
def generate_grocery_list(recipe_id):
    # Get recipe from database
    recipe = Recipe.query.get_or_404(recipe_id)

    # Delete existing grocery lists
    GroceryList.query.filter_by(recipe_id=recipe_id).delete()

    # Create a simple list of ingredients without categorization
    ingredients = [ing.ingredient for ing in recipe.ingredients]
    grocery_list = GroceryList(recipe_id=recipe_id, category='Items', items=ingredients)
    db.session.add(grocery_list)
    db.session.commit()

    return redirect(url_for('view_recipe', recipe_id=recipe_id))


@app.route('/search', methods=['GET'])
def search_recipes():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('list_recipes'))

    # Search for recipes by title
    results = Recipe.query.filter(Recipe.title.ilike(f'%{query}%')).order_by(Recipe.date_added.desc()).all()
    results_data = [recipe.to_dict_minimal() for recipe in results]

    return render_template('search_results.html', recipes=results_data, query=query)


if __name__ == '__main__':
    app.run(debug=True)