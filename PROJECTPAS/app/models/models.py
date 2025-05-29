from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'creator' or 'student'
    
    # Relationships
    flashcard_decks = db.relationship('FlashcardDeck', backref='creator', cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='student', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FlashcardDeck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Relationships
    flashcards = db.relationship('Flashcard', backref='deck', cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='deck', cascade='all, delete-orphan')

class Flashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.Text, nullable=False)  # Question or term
    back = db.Column(db.Text, nullable=False)   # Answer or definition
    deck_id = db.Column(db.Integer, db.ForeignKey('flashcard_deck.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Optional fields for enhanced learning
    hint = db.Column(db.String(255))
    difficulty = db.Column(db.Integer, default=1)  # 1-5 scale

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('flashcard_deck.id', ondelete='CASCADE'), nullable=False)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)
    
    # Study statistics
    cards_reviewed = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
