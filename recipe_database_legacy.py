# recipe_database.py
import os
import psycopg
import json
from datetime import datetime

class RecipeDatabase:
    """
    Database implementation using PostgreSQL (Supabase)

    Requires DATABASE_URL environment variable to be set.
    Example: postgresql://user:password@host:port/database
    """
    def __init__(self):
        # Get database URL from environment variable
        raw_url = os.environ.get('DATABASE_URL')
        if not raw_url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Remove pgbouncer parameter if present (not supported by psycopg)
        self.database_url = raw_url.replace('?pgbouncer=true', '')

        # Test connection
        self._test_connection()

    def _get_connection(self):
        """Create a new database connection"""
        return psycopg.connect(self.database_url)

    def _test_connection(self):
        """Test that we can connect to the database"""
        try:
            conn = self._get_connection()
            conn.close()
        except Exception as e:
            raise Exception(f"Failed to connect to database: {str(e)}")

    def save_recipe(self, recipe_data):
        """
        Save a recipe and all its related data to the database
        Returns the ID of the saved recipe
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Save recipe metadata
                cur.execute(
                    """
                    INSERT INTO recipes (title, source_url, date_added)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        recipe_data.get('title', 'Untitled Recipe'),
                        recipe_data.get('source_url', ''),
                        datetime.now()
                    )
                )
                recipe_id = cur.fetchone()[0]

                # Save ingredients
                if 'ingredients' in recipe_data and recipe_data['ingredients']:
                    for ingredient in recipe_data['ingredients']:
                        cur.execute(
                            """
                            INSERT INTO ingredients (recipe_id, ingredient)
                            VALUES (%s, %s)
                            """,
                            (recipe_id, ingredient)
                        )

                # Save directions
                if 'directions' in recipe_data and recipe_data['directions']:
                    for step_number, direction in enumerate(recipe_data['directions'], 1):
                        cur.execute(
                            """
                            INSERT INTO directions (recipe_id, step_number, direction)
                            VALUES (%s, %s, %s)
                            """,
                            (recipe_id, step_number, direction)
                        )

                # Save grocery list
                if 'grocery_list' in recipe_data and recipe_data['grocery_list']:
                    for category, items in recipe_data['grocery_list'].items():
                        cur.execute(
                            """
                            INSERT INTO grocery_lists (recipe_id, category, items)
                            VALUES (%s, %s, %s)
                            """,
                            (recipe_id, category, json.dumps(items))
                        )

                conn.commit()
                return str(recipe_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_all_recipes(self):
        """
        Return a list of all saved recipes (metadata only)
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, source_url, date_added
                    FROM recipes
                    ORDER BY date_added DESC
                    """
                )
                columns = [desc[0] for desc in cur.description]
                recipes = [dict(zip(columns, row)) for row in cur.fetchall()]
                # Convert to list of dicts and ensure id is string
                return [
                    {
                        'id': str(recipe['id']),
                        'title': recipe['title'],
                        'source_url': recipe['source_url'],
                        'date_added': recipe['date_added'].strftime('%Y-%m-%d %H:%M:%S') if recipe['date_added'] else ''
                    }
                    for recipe in recipes
                ]
        finally:
            conn.close()

    def get_recipe_by_id(self, recipe_id):
        """
        Get a complete recipe with all its details by ID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Get recipe metadata
                cur.execute(
                    """
                    SELECT id, title, source_url, date_added
                    FROM recipes
                    WHERE id = %s
                    """,
                    (recipe_id,)
                )
                columns = [desc[0] for desc in cur.description]
                row = cur.fetchone()

                if not row:
                    return None

                recipe = dict(zip(columns, row))
                recipe['id'] = str(recipe['id'])
                recipe['date_added'] = recipe['date_added'].strftime('%Y-%m-%d %H:%M:%S') if recipe['date_added'] else ''

                # Get ingredients
                cur.execute(
                    """
                    SELECT ingredient
                    FROM ingredients
                    WHERE recipe_id = %s
                    ORDER BY id
                    """,
                    (recipe_id,)
                )
                recipe['ingredients'] = [row[0] for row in cur.fetchall()]

                # Get directions
                cur.execute(
                    """
                    SELECT direction
                    FROM directions
                    WHERE recipe_id = %s
                    ORDER BY step_number
                    """,
                    (recipe_id,)
                )
                recipe['directions'] = [row[0] for row in cur.fetchall()]

                # Get grocery list
                cur.execute(
                    """
                    SELECT category, items
                    FROM grocery_lists
                    WHERE recipe_id = %s
                    ORDER BY id
                    """,
                    (recipe_id,)
                )
                recipe['grocery_list'] = {
                    row[0]: json.loads(row[1])
                    for row in cur.fetchall()
                }

                return recipe
        finally:
            conn.close()

    def recipe_exists(self, source_url):
        """
        Check if a recipe with the given source URL already exists
        Returns the recipe ID if found, otherwise None
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id FROM recipes
                    WHERE source_url = %s
                    LIMIT 1
                    """,
                    (source_url,)
                )
                result = cur.fetchone()
                return str(result[0]) if result else None
        finally:
            conn.close()

    def delete_recipe(self, recipe_id):
        """
        Delete a recipe and all its related data
        Returns True if successful, False otherwise
        """
        if not recipe_id:
            return False

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Delete recipe (CASCADE will delete related rows)
                cur.execute(
                    """
                    DELETE FROM recipes
                    WHERE id = %s
                    """,
                    (recipe_id,)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
