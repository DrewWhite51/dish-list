# recipe_parser.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
from bs4 import BeautifulSoup
import re
from recipe_database import RecipeDatabase

app = Flask(__name__)
db = RecipeDatabase()  # Initialize the database with default path

def parse_recipe(url):
    """
    Parse a recipe URL to extract ingredients and directions
    """
    try:
        # Make request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract ingredients - look for common patterns in recipe websites
        ingredients = []
        
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
        
        # Method 1: Look for elements with 'direction', 'instruction', or 'step' in class or id
        direction_elements = soup.find_all(class_=lambda c: c and any(x in c.lower() for x in ['direction', 'instruction', 'step']))
        if not direction_elements:
            direction_elements = soup.find_all(id=lambda i: i and any(x in i.lower() for x in ['direction', 'instruction', 'step']))
        
        for element in direction_elements:
            direction_text = element.get_text().strip()
            if direction_text and len(direction_text) < 500:  # Reasonable length for a direction
                directions.append(direction_text)
        
        # Method 2: Look for schema.org structured data
        if not directions:
            if recipe_schema:
                try:
                    if not 'schema_data' in locals():
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
    
    except Exception as e:
        return {
            "error": str(e),
            "ingredients": [],
            "directions": [],
            "source_url": url
        }

# Routes
@app.route('/')
def index():
    # Get all saved recipes to display on the homepage
    recipes = db.get_all_recipes()
    return render_template('index.html', recipe=None, recipes=recipes)

@app.route('/parse', methods=['POST'])
def parse():
    url = request.form.get('recipe_url')
    if not url:
        return jsonify({"error": "No URL provided"})
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Check if this recipe URL already exists in the database
    existing_recipe_id = db.recipe_exists(url)
    if existing_recipe_id:
        # Recipe already exists, redirect to its page
        return redirect(url_for('view_recipe', recipe_id=existing_recipe_id))
    
    # Parse the recipe
    result = parse_recipe(url)
    
    # Pass to template for confirmation before saving
    return render_template('result.html', recipe=result)

@app.route('/save', methods=['POST'])
def save_recipe():
    # Extract recipe data from form
    recipe_data = {
        'title': request.form.get('title'),
        'source_url': request.form.get('source_url'),
        'ingredients': request.form.getlist('ingredients'),
        'directions': request.form.getlist('directions'),
        'grocery_list': {}  # Initialize empty grocery list, can be populated later
    }
    
    # Check if recipe already exists
    existing_recipe_id = db.recipe_exists(recipe_data['source_url'])
    if existing_recipe_id:
        # Redirect to existing recipe
        return redirect(url_for('view_recipe', recipe_id=existing_recipe_id))
    
    # Save new recipe
    recipe_id = db.save_recipe(recipe_data)
    
    # Redirect to the saved recipe
    return redirect(url_for('view_recipe', recipe_id=recipe_id))

@app.route('/recipe/<recipe_id>')
def view_recipe(recipe_id):
    # Get recipe from database
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        return "Recipe not found", 404
    
    return render_template('recipe.html', recipe=recipe)

@app.route('/recipes')
def list_recipes():
    # Get all recipes from database
    recipes = db.get_all_recipes()
    return render_template('recipes.html', recipes=recipes)

@app.route('/delete/<recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    success = db.delete_recipe(recipe_id)
    if success:
        # Redirect to recipes list after deletion
        return redirect(url_for('list_recipes'))
    else:
        # If deletion failed, return to the recipe page with an error
        return redirect(url_for('view_recipe', recipe_id=recipe_id, error="Failed to delete recipe"))

@app.route('/edit/<recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    # Get existing recipe
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        return "Recipe not found", 404
    
    if request.method == 'POST':
        # Update recipe data
        recipe_data = {
            'id': recipe_id,
            'title': request.form.get('title'),
            'source_url': request.form.get('source_url'),
            'ingredients': request.form.getlist('ingredients'),
            'directions': request.form.getlist('directions'),
            'grocery_list': recipe.get('grocery_list', {})  # Preserve existing grocery list
        }
        
        # Update recipe in database (you would need to add an update method to RecipeDatabase)
        # For now, we'll delete and re-save
        db.delete_recipe(recipe_id)
        new_recipe_id = db.save_recipe(recipe_data)
        
        return redirect(url_for('view_recipe', recipe_id=new_recipe_id))
    
    # Show edit form
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/generate_grocery_list/<recipe_id>', methods=['POST'])
def generate_grocery_list(recipe_id):
    # Get recipe from database
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        return "Recipe not found", 404
    
    # Create a simple list of ingredients without categorization
    grocery_list = {
        'Items': recipe['ingredients']  # Just store all ingredients in a single list
    }
    
    # Update the recipe with the grocery list
    recipe['grocery_list'] = grocery_list
    
    # Save updated recipe
    db.delete_recipe(recipe_id)
    new_recipe_id = db.save_recipe(recipe)
    
    return redirect(url_for('view_recipe', recipe_id=new_recipe_id))


@app.route('/search', methods=['GET'])
def search_recipes():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('list_recipes'))
    
    # Simple implementation - get all recipes and filter (for a real app, you'd want to optimize this)
    all_recipes = db.get_all_recipes()
    results = []
    
    for recipe in all_recipes:
        if query.lower() in recipe['title'].lower():
            results.append(recipe)
    
    return render_template('search_results.html', recipes=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)