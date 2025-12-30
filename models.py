# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    source_url = db.Column(db.String(1000), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    prep_time = db.Column(db.String(100), nullable=True)
    cook_time = db.Column(db.String(100), nullable=True)

    # Relationships
    ingredients = db.relationship('Ingredient', backref='recipe', lazy=True, cascade='all, delete-orphan')
    directions = db.relationship('Direction', backref='recipe', lazy=True, cascade='all, delete-orphan')
    grocery_lists = db.relationship('GroceryList', backref='recipe', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Recipe {self.id}: {self.title}>'

    def to_dict(self):
        """Convert recipe to dictionary format"""
        return {
            'id': str(self.id),
            'title': self.title,
            'source_url': self.source_url,
            'date_added': self.date_added.strftime('%Y-%m-%d %H:%M:%S') if self.date_added else '',
            'prep_time': self.prep_time or '',
            'cook_time': self.cook_time or '',
            'ingredients': [ing.ingredient for ing in self.ingredients],
            'directions': [dir.direction for dir in sorted(self.directions, key=lambda x: x.step_number)],
            'grocery_list': {gl.category: gl.get_items() for gl in self.grocery_lists}
        }

    def to_dict_minimal(self):
        """Convert recipe to minimal dictionary (metadata only)"""
        return {
            'id': str(self.id),
            'title': self.title,
            'source_url': self.source_url,
            'date_added': self.date_added.strftime('%Y-%m-%d %H:%M:%S') if self.date_added else ''
        }


class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    ingredient = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Ingredient {self.id} for Recipe {self.recipe_id}>'


class Direction(db.Model):
    __tablename__ = 'directions'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Direction {self.step_number} for Recipe {self.recipe_id}>'


class GroceryList(db.Model):
    __tablename__ = 'grocery_lists'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(200), nullable=False)
    items = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f'<GroceryList {self.category} for Recipe {self.recipe_id}>'

    def get_items(self):
        """Get items as a list"""
        return self.items if isinstance(self.items, list) else []
