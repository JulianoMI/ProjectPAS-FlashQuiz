from flask import render_template, redirect, url_for, flash, request, jsonify, session
from app import app, db
from app.models.models import User, FlashcardDeck, Flashcard, StudySession
from functools import wraps
from datetime import datetime

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in first.', 'warning')
            return redirect(url_for('views.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('views.index'))
            
        return f(*args, **kwargs)
    return decorated_function

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.all()
    decks = FlashcardDeck.query.all()
    return render_template('admin.html', users=users, decks=decks)

@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow admin to delete themselves
    if user.id == session['user_id']:
        return jsonify({'error': 'Cannot delete your own account'}), 400
        
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/deck/<int:deck_id>', methods=['DELETE'])
@admin_required
def delete_deck(deck_id):
    deck = FlashcardDeck.query.get_or_404(deck_id)
    try:
        db.session.delete(deck)
        db.session.commit()
        return jsonify({'message': 'Deck deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Update base template to show admin link
@app.context_processor
def inject_admin_status():
    def is_admin():
        if not session.get('user_id'):
            return False
        user = User.query.get(session['user_id'])
        return user and user.is_admin()
    return dict(is_admin=is_admin) 