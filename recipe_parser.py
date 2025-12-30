# recipe_parser.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from dotenv import load_dotenv
from models import db, Recipe, Ingredient, Direction, GroceryList
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

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


def parse_recipe(url):
    """
    Parse a recipe URL using GPT-4o-mini for robust extraction.
    """
    from robust_parser import parse_recipe_robust
    return parse_recipe_robust(url)


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
    prep_time = request.form.get('prep_time', '')
    cook_time = request.form.get('cook_time', '')
    ingredients_list = request.form.getlist('ingredients')
    directions_list = request.form.getlist('directions')

    # Check if recipe already exists
    existing_recipe = Recipe.query.filter_by(source_url=source_url).first()
    if existing_recipe:
        # Redirect to existing recipe
        return redirect(url_for('view_recipe', recipe_id=existing_recipe.id))

    # Create new recipe
    recipe = Recipe(title=title, source_url=source_url, prep_time=prep_time, cook_time=cook_time)
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
        recipe.prep_time = request.form.get('prep_time', '')
        recipe.cook_time = request.form.get('cook_time', '')

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