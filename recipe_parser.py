# recipe_parser.py
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse():
    url = request.form.get('recipe_url')
    if not url:
        return jsonify({"error": "No URL provided"})
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    result = parse_recipe(url)
    return render_template('result.html', recipe=result)

if __name__ == '__main__':
    app.run(debug=True)