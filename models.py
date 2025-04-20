from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    decks = db.relationship('Deck', backref='owner', lazy='dynamic')

class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_studied = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cards_json = db.Column(db.Text, nullable=False)  # Store cards as JSON
    
    def get_cards(self):
        """Convert JSON string to Python object"""
        return json.loads(self.cards_json)
    
    def set_cards(self, cards):
        """Convert Python object to JSON string"""
        self.cards_json = json.dumps(cards)