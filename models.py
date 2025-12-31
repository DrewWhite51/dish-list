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


class RateLimit(db.Model):
    """Track rate limit attempts per IP address"""
    __tablename__ = 'rate_limits'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IPv6 max length
    endpoint = db.Column(db.String(100), nullable=False)
    window_start = db.Column(db.DateTime, nullable=False, index=True)
    request_count = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.Index('idx_ip_endpoint_window', 'ip_address', 'endpoint', 'window_start'),
    )

    def __repr__(self):
        return f'<RateLimit {self.ip_address} {self.endpoint} {self.request_count}/{self.window_start}>'


class ApiUsage(db.Model):
    """Track daily OpenAI API usage and costs"""
    __tablename__ = 'api_usage'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    request_count = db.Column(db.Integer, default=0)
    estimated_cost = db.Column(db.Numeric(10, 4), default=0)
    tokens_used = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<ApiUsage {self.date} requests={self.request_count} cost=${self.estimated_cost}>'


class BlockedIp(db.Model):
    """Track permanently blocked IPs for abuse patterns"""
    __tablename__ = 'blocked_ips'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True, index=True)
    reason = db.Column(db.String(500))
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    blocked_until = db.Column(db.DateTime, nullable=True)  # NULL = permanent

    def __repr__(self):
        return f'<BlockedIp {self.ip_address} reason={self.reason}>'
