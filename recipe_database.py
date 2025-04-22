# recipe_database.py
import csv
import os
import uuid
from datetime import datetime
import json

class RecipeDatabase:
    """
    Database implementation using CSV files as storage
    """
    def __init__(self, db_path='db'):
        # Ensure database directory exists
        self.db_path = db_path
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        # Create necessary files if they don't exist
        self.recipes_file = os.path.join(db_path, 'recipes.csv')
        self.ingredients_file = os.path.join(db_path, 'ingredients.csv')
        self.directions_file = os.path.join(db_path, 'directions.csv')
        self.grocery_lists_file = os.path.join(db_path, 'grocery_lists.csv')
        
        self._initialize_files()
    
    def _initialize_files(self):
        """Create database files with headers if they don't exist"""
        # Recipes file: id, title, source_url, date_added
        if not os.path.exists(self.recipes_file):
            with open(self.recipes_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'title', 'source_url', 'date_added'])
        
        # Ingredients file: id, recipe_id, ingredient
        if not os.path.exists(self.ingredients_file):
            with open(self.ingredients_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'recipe_id', 'ingredient'])
        
        # Directions file: id, recipe_id, step_number, direction
        if not os.path.exists(self.directions_file):
            with open(self.directions_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'recipe_id', 'step_number', 'direction'])
        
        # Grocery lists file: id, recipe_id, category, items
        if not os.path.exists(self.grocery_lists_file):
            with open(self.grocery_lists_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'recipe_id', 'category', 'items'])
    
    def save_recipe(self, recipe_data):
        """
        Save a recipe and all its related data to the database
        Returns the ID of the saved recipe
        """
        # Generate a unique ID for the recipe
        recipe_id = str(uuid.uuid4())
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save recipe metadata
        with open(self.recipes_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                recipe_id,
                recipe_data.get('title', 'Untitled Recipe'),
                recipe_data.get('source_url', ''),
                current_date
            ])
        
        # Save ingredients
        if 'ingredients' in recipe_data and recipe_data['ingredients']:
            with open(self.ingredients_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for ingredient in recipe_data['ingredients']:
                    ingredient_id = str(uuid.uuid4())
                    writer.writerow([ingredient_id, recipe_id, ingredient])
        
        # Save directions
        if 'directions' in recipe_data and recipe_data['directions']:
            with open(self.directions_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for step_number, direction in enumerate(recipe_data['directions'], 1):
                    direction_id = str(uuid.uuid4())
                    writer.writerow([direction_id, recipe_id, step_number, direction])
        
        # Save grocery list
        if 'grocery_list' in recipe_data and recipe_data['grocery_list']:
            with open(self.grocery_lists_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for category, items in recipe_data['grocery_list'].items():
                    grocery_list_id = str(uuid.uuid4())
                    # Store items as a JSON string to preserve the array
                    items_json = json.dumps(items)
                    writer.writerow([grocery_list_id, recipe_id, category, items_json])
        
        return recipe_id
    
    def get_all_recipes(self):
        """
        Return a list of all saved recipes (metadata only)
        """
        recipes = []
        
        if not os.path.exists(self.recipes_file):
            return recipes
            
        with open(self.recipes_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                recipes.append(row)
                
        return recipes
    
    def get_recipe_by_id(self, recipe_id):
        """
        Get a complete recipe with all its details by ID
        """
        # Initialize the result structure
        recipe = None
        
        # Get recipe metadata
        with open(self.recipes_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['id'] == recipe_id:
                    recipe = row
                    recipe['ingredients'] = []
                    recipe['directions'] = []
                    recipe['grocery_list'] = {}
                    break
        
        if not recipe:
            return None
        
        # Get ingredients
        with open(self.ingredients_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['recipe_id'] == recipe_id:
                    recipe['ingredients'].append(row['ingredient'])
        
        # Get directions
        directions = []
        with open(self.directions_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['recipe_id'] == recipe_id:
                    directions.append((int(row['step_number']), row['direction']))
        
        # Sort directions by step number
        directions.sort(key=lambda x: x[0])
        recipe['directions'] = [direction for _, direction in directions]
        
        # Get grocery list
        with open(self.grocery_lists_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['recipe_id'] == recipe_id:
                    category = row['category']
                    items = json.loads(row['items'])
                    recipe['grocery_list'][category] = items
        
        return recipe
    
    def recipe_exists(self, source_url):
        """
        Check if a recipe with the given source URL already exists
        Returns the recipe ID if found, otherwise None
        """
        if not os.path.exists(self.recipes_file):
            return None
            
        with open(self.recipes_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['source_url'] == source_url:
                    return row['id']
                    
        return None
    
    def delete_recipe(self, recipe_id):
        """
        Delete a recipe and all its related data
        Returns True if successful, False otherwise
        """
        if not recipe_id:
            return False
            
        # Helper function to filter out rows for the deleted recipe
        def filter_rows(input_file, output_file, id_field='recipe_id'):
            temp_file = input_file + '.tmp'
            deleted = False
            
            with open(input_file, 'r', newline='', encoding='utf-8') as fin, \
                 open(temp_file, 'w', newline='', encoding='utf-8') as fout:
                
                reader = csv.reader(fin)
                writer = csv.writer(fout)
                
                # Write the header
                header = next(reader)
                writer.writerow(header)
                
                # Get index of the ID field
                id_index = header.index(id_field) if id_field in header else 1
                
                # Write all rows except those matching the recipe_id
                for row in reader:
                    if id_index < len(row) and row[id_index] != recipe_id:
                        writer.writerow(row)
                    else:
                        deleted = True
            
            # Replace the original file with the filtered one
            os.replace(temp_file, input_file)
            return deleted
        
        # Delete from recipes (use 'id' as the ID field)
        recipes_deleted = filter_rows(self.recipes_file, self.recipes_file, 'id')
        
        # Delete from related tables
        ingredients_deleted = filter_rows(self.ingredients_file, self.ingredients_file)
        directions_deleted = filter_rows(self.directions_file, self.directions_file)
        grocery_lists_deleted = filter_rows(self.grocery_lists_file, self.grocery_lists_file)
        
        return recipes_deleted