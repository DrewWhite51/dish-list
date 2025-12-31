# recipe_parser.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from dotenv import load_dotenv
from models import db, Recipe, Ingredient, Direction, GroceryList, RateLimit, ApiUsage, BlockedIp
from flask_migrate import Migrate
from protection import (
    require_rate_limit,
    validate_url_for_ssrf,
    record_api_usage,
    get_client_ip,
    check_rate_limit
)
from datetime import datetime, timedelta

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
    'connect_args': {'prepare_threshold': None}  # Disable prepared statements for pgbouncer
}

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Rate limiting configuration
app.config['RATE_LIMIT_PER_HOUR'] = int(os.getenv('RATE_LIMIT_PER_HOUR', '20'))
app.config['RATE_LIMIT_ENABLED'] = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
app.config['DAILY_BUDGET_USD'] = float(os.getenv('DAILY_BUDGET_USD', '5.00'))
app.config['COST_PER_REQUEST'] = float(os.getenv('COST_PER_REQUEST', '0.0015'))
app.config['BUDGET_ALERT_THRESHOLD'] = float(os.getenv('BUDGET_ALERT_THRESHOLD', '0.8'))


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
@require_rate_limit
def parse():
    url = request.form.get('recipe_url')
    if not url:
        return jsonify({"error": "No URL provided"})

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # SSRF validation
    is_valid, error_msg = validate_url_for_ssrf(url)
    if not is_valid:
        return render_template('result.html', recipe={
            'error': error_msg,
            'title': '',
            'ingredients': [],
            'directions': [],
            'prep_time': '',
            'cook_time': '',
            'source_url': url
        })

    # Check if this recipe URL already exists in the database
    existing_recipe = Recipe.query.filter_by(source_url=url).first()
    if existing_recipe:
        # Recipe already exists, redirect to its page
        return redirect(url_for('view_recipe', recipe_id=existing_recipe.id))

    # Parse the recipe
    result = parse_recipe(url)

    # Record API usage
    if 'error' not in result:
        record_api_usage()

    # If parsing failed, show error page
    if 'error' in result:
        return render_template('result.html', recipe=result)

    # Automatically save the parsed recipe to database
    recipe = Recipe(
        title=result.get('title', 'Untitled Recipe'),
        source_url=url,
        prep_time=result.get('prep_time', ''),
        cook_time=result.get('cook_time', '')
    )
    db.session.add(recipe)
    db.session.flush()  # Get the recipe ID before committing

    # Add ingredients
    for ingredient_text in result.get('ingredients', []):
        if ingredient_text.strip():
            ingredient = Ingredient(recipe_id=recipe.id, ingredient=ingredient_text)
            db.session.add(ingredient)

    # Add directions
    for step_number, direction_text in enumerate(result.get('directions', []), 1):
        if direction_text.strip():
            direction = Direction(recipe_id=recipe.id, step_number=step_number, direction=direction_text)
            db.session.add(direction)

    db.session.commit()

    # Redirect directly to the recipe detail page
    return redirect(url_for('view_recipe', recipe_id=recipe.id))

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

@app.route('/search', methods=['GET'])
def search_recipes():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('list_recipes'))

    # Search for recipes by title
    results = Recipe.query.filter(Recipe.title.ilike(f'%{query}%')).order_by(Recipe.date_added.desc()).all()
    results_data = [recipe.to_dict_minimal() for recipe in results]

    return render_template('search_results.html', recipes=results_data, query=query)


@app.route('/admin/usage')
def admin_usage():
    """
    Admin dashboard for API usage monitoring.
    WARNING: In production, protect this route with authentication!
    """
    from datetime import date, timedelta

    today = date.today()
    today_usage = ApiUsage.query.filter_by(date=today).first()

    # Create default if no usage yet
    if not today_usage:
        today_usage = ApiUsage(
            date=today,
            request_count=0,
            estimated_cost=0,
            tokens_used=0
        )

    # Get last 7 days of usage
    week_ago = today - timedelta(days=7)
    weekly_usage = ApiUsage.query.filter(
        ApiUsage.date >= week_ago
    ).order_by(ApiUsage.date.desc()).all()

    # Count active IPs in last hour
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    active_ips = db.session.query(RateLimit.ip_address).filter(
        RateLimit.window_start >= hour_ago
    ).distinct().count()

    # Count blocked IPs
    blocked_ips_count = BlockedIp.query.count()

    return render_template('admin_usage.html',
                         today_usage=today_usage,
                         daily_budget=app.config['DAILY_BUDGET_USD'],
                         active_ips=active_ips,
                         blocked_ips_count=blocked_ips_count,
                         weekly_usage=weekly_usage)


# Error handlers for rate limiting and abuse protection
@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit exceeded"""
    ip = get_client_ip()
    allowed, retry_seconds, remaining = check_rate_limit(ip, endpoint='/parse')
    return render_template('rate_limit.html',
                         retry_after=retry_seconds,
                         ip_address=ip), 429


@app.errorhandler(403)
def forbidden(e):
    """Handle blocked IP"""
    return render_template('blocked.html'), 403


@app.errorhandler(503)
def service_unavailable(e):
    """Handle budget exceeded"""
    return render_template('budget_exceeded.html'), 503


if __name__ == '__main__':
    app.run(debug=True)