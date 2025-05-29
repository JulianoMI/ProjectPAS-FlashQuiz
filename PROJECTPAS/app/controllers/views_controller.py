from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from app.models.models import User, FlashcardDeck, Flashcard, StudySession
from app import db
from datetime import datetime
from sqlalchemy import desc, func, distinct, case
from sqlalchemy.orm import aliased

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def home():
    return render_template('home.html')

@views_bp.route('/my-progress')
def my_progress():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get user's study history with the most recent sessions first
    study_history = (
        StudySession.query
        .join(FlashcardDeck)
        .filter(StudySession.user_id == session['user_id'])
        .order_by(desc(StudySession.started_at))
        .all()
    )
    
    # Group sessions by deck
    deck_stats = {}
    for study_session in study_history:
        if study_session.deck_id not in deck_stats:
            deck_stats[study_session.deck_id] = {
                'deck': study_session.deck,
                'total_sessions': 0,
                'last_studied': study_session.started_at,
                'completed_sessions': 0
            }
        deck_stats[study_session.deck_id]['total_sessions'] += 1
        if study_session.completed_at:
            deck_stats[study_session.deck_id]['completed_sessions'] += 1
    
    return render_template('my_progress.html', deck_stats=deck_stats.values())

@views_bp.route('/decks')
def decks():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_decks = FlashcardDeck.query.filter_by(creator_id=session['user_id']).all()
    return render_template('decks.html', decks=user_decks)

@views_bp.route('/deck/new', methods=['GET', 'POST'])
def create_deck():
    if 'user_id' not in session or session.get('role') != 'creator':
        flash('Only creators can create decks.', 'error')
        return redirect(url_for('views.decks'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        fronts = request.form.getlist('fronts[]')
        backs = request.form.getlist('backs[]')
        hints = request.form.getlist('hints[]')

        deck = FlashcardDeck(
            title=title,
            description=description,
            creator_id=session['user_id']
        )
        db.session.add(deck)
        db.session.flush()

        for front, back, hint in zip(fronts, backs, hints):
            card = Flashcard(
                front=front,
                back=back,
                hint=hint if hint else None,
                deck_id=deck.id
            )
            db.session.add(card)

        db.session.commit()
        flash('Deck created successfully!', 'success')
        return redirect(url_for('views.decks'))

    return render_template('edit_deck.html')

@views_bp.route('/deck/<int:deck_id>/edit', methods=['GET', 'POST'])
def edit_deck(deck_id):
    deck = FlashcardDeck.query.get_or_404(deck_id)
    if deck.creator_id != session.get('user_id'):
        flash('You can only edit your own decks.', 'error')
        return redirect(url_for('views.decks'))

    if request.method == 'POST':
        deck.title = request.form.get('title')
        deck.description = request.form.get('description')
        
        # Delete existing cards
        Flashcard.query.filter_by(deck_id=deck.id).delete()
        
        # Add new cards
        fronts = request.form.getlist('fronts[]')
        backs = request.form.getlist('backs[]')
        hints = request.form.getlist('hints[]')

        for front, back, hint in zip(fronts, backs, hints):
            card = Flashcard(
                front=front,
                back=back,
                hint=hint if hint else None,
                deck_id=deck.id
            )
            db.session.add(card)

        db.session.commit()
        flash('Deck updated successfully!', 'success')
        return redirect(url_for('views.decks'))

    return render_template('edit_deck.html', deck=deck)

@views_bp.route('/deck/<int:deck_id>', methods=['DELETE'])
def delete_deck(deck_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    deck = FlashcardDeck.query.get_or_404(deck_id)
    if deck.creator_id != session['user_id']:
        return jsonify({'error': 'Forbidden'}), 403

    # Delete associated study sessions first
    StudySession.query.filter_by(deck_id=deck_id).delete()
    
    # Delete associated flashcards
    Flashcard.query.filter_by(deck_id=deck_id).delete()
    
    # Finally delete the deck
    db.session.delete(deck)
    db.session.commit()
    return jsonify({'message': 'Deck deleted successfully'})

@views_bp.route('/deck/<int:deck_id>/study')
def study_deck(deck_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    deck = FlashcardDeck.query.get_or_404(deck_id)
    card_index = request.args.get('card', 0, type=int)
    
    # Create or update study session
    session_record = StudySession.query.filter_by(
        user_id=session['user_id'],
        deck_id=deck_id,
        completed_at=None
    ).first()
    
    if not session_record:
        session_record = StudySession(
            user_id=session['user_id'],
            deck_id=deck_id
        )
        db.session.add(session_record)
        db.session.commit()

    cards = deck.flashcards
    if not cards:
        flash('This deck has no cards.', 'error')
        return redirect(url_for('views.decks'))

    # Handle card index bounds
    card_index = max(0, min(card_index, len(cards) - 1))
    current_card = cards[card_index]

    return render_template('study.html',
        deck=deck,
        current_card=current_card,
        current_card_index=card_index,
        total_cards=len(cards)
    )

@views_bp.route('/deck/<int:deck_id>/card/<int:card_id>/review', methods=['POST'])
def review_card(deck_id, card_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    # Get or create study session
    study_session = StudySession.query.filter_by(
        user_id=session['user_id'],
        deck_id=deck_id,
        completed_at=None
    ).first()
    
    if not study_session:
        study_session = StudySession(
            user_id=session['user_id'],
            deck_id=deck_id
        )
        db.session.add(study_session)
    
    # Update review count
    study_session.cards_reviewed += 1
    db.session.commit()
    
    return jsonify({'message': 'Review recorded'})

@views_bp.route('/deck/<int:deck_id>/complete', methods=['POST'])
def complete_study_session(deck_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    session_record = StudySession.query.filter_by(
        user_id=session['user_id'],
        deck_id=deck_id,
        completed_at=None
    ).first()

    if session_record:
        session_record.completed_at = datetime.utcnow()
        db.session.commit()

    return jsonify({'message': 'Study session completed'})

@views_bp.route('/explore')
def explore_decks():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get all decks
    decks = FlashcardDeck.query.order_by(FlashcardDeck.created_at.desc()).all()
    
    return render_template('explore.html', decks=decks)

@views_bp.route('/analytics')
def analytics():
    if 'user_id' not in session or session.get('role') != 'creator':
        flash('Only teachers can access analytics.', 'error')
        return redirect(url_for('views.decks'))
    
    # Get overall statistics
    total_decks = FlashcardDeck.query.filter_by(creator_id=session['user_id']).count()
    total_cards = (Flashcard.query
                  .join(FlashcardDeck)
                  .filter(FlashcardDeck.creator_id == session['user_id'])
                  .count())
    
    # Get unique students who studied teacher's decks
    student_subq = (db.session.query(StudySession.user_id)
                   .join(FlashcardDeck)
                   .filter(FlashcardDeck.creator_id == session['user_id'])
                   .distinct()
                   .subquery())
    
    total_students = db.session.query(func.count()).select_from(student_subq).scalar()
    
    total_sessions = (StudySession.query
                     .join(FlashcardDeck)
                     .filter(FlashcardDeck.creator_id == session['user_id'])
                     .count())
    
    # Get deck performance data
    decks = FlashcardDeck.query.filter_by(creator_id=session['user_id']).all()
    for deck in decks:
        # Calculate unique students
        deck.unique_students = (StudySession.query
                              .filter_by(deck_id=deck.id)
                              .distinct(StudySession.user_id)
                              .count())
        
        # Calculate average completion rate
        completed_sessions = sum(1 for session in deck.study_sessions if session.completed_at)
        total_sessions = len(deck.study_sessions)
        deck.avg_completion = round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0)
    
    # Get student progress data
    student_alias = aliased(User)
    students = (db.session.query(student_alias,
                               func.count(distinct(StudySession.deck_id)).label('decks_studied'),
                               func.count(StudySession.id).label('total_sessions'),
                               func.max(StudySession.started_at).label('last_active'))
               .join(StudySession, StudySession.user_id == student_alias.id)
               .join(FlashcardDeck, FlashcardDeck.id == StudySession.deck_id)
               .filter(FlashcardDeck.creator_id == session['user_id'])
               .group_by(student_alias.id)
               .all())
    
    student_data = []
    for student, decks_studied, total_sessions, last_active in students:
        student_data.append({
            'username': student.username,
            'decks_studied': decks_studied,
            'total_sessions': total_sessions,
            'last_active': last_active
        })
    
    # Get recent activity
    recent_activity = (StudySession.query
                      .join(FlashcardDeck)
                      .join(User, User.id == StudySession.user_id)
                      .filter(FlashcardDeck.creator_id == session['user_id'])
                      .order_by(desc(StudySession.started_at))
                      .limit(10)
                      .all())
    
    activity_data = []
    for activity in recent_activity:
        action = 'completed' if activity.completed_at else 'started studying'
        activity_data.append({
            'timestamp': activity.started_at,
            'student': activity.student,
            'action': action,
            'deck': activity.deck
        })
    
    return render_template('analytics.html',
                         total_decks=total_decks,
                         total_cards=total_cards,
                         total_students=total_students,
                         total_sessions=total_sessions,
                         decks=decks,
                         students=student_data,
                         recent_activity=activity_data)

@views_bp.route('/deck/<int:deck_id>/preview')
def preview_deck(deck_id):
    if 'user_id' not in session or session.get('role') != 'creator':
        flash('Only teachers can preview decks.', 'error')
        return redirect(url_for('views.explore_decks'))
    
    deck = FlashcardDeck.query.get_or_404(deck_id)
    cards = deck.flashcards
    
    return render_template('preview_deck.html',
                         deck=deck,
                         cards=cards)

@views_bp.route('/deck/<int:deck_id>/details')
def deck_details(deck_id):
    if 'user_id' not in session or session.get('role') != 'creator':
        flash('Only teachers can view deck details.', 'error')
        return redirect(url_for('views.explore_decks'))
    
    deck = FlashcardDeck.query.get_or_404(deck_id)
    if deck.creator_id != session['user_id']:
        flash('You can only view details of your own decks.', 'error')
        return redirect(url_for('views.analytics'))
    
    # Get detailed statistics
    total_sessions = len(deck.study_sessions)
    completed_sessions = sum(1 for session in deck.study_sessions if session.completed_at)
    completion_rate = round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0)
    
    # Get student performance
    student_performance = (db.session.query(User,
                                          func.count(StudySession.id).label('sessions'),
                                          func.sum(case((StudySession.completed_at != None, 1), else_=0)).label('completed'))
                         .join(StudySession, StudySession.user_id == User.id)
                         .filter(StudySession.deck_id == deck_id)
                         .group_by(User.id)
                         .all())
    
    performance_data = []
    for student, sessions, completed in student_performance:
        performance_data.append({
            'username': student.username,
            'sessions': sessions,
            'completed': completed,
            'completion_rate': round((completed / sessions * 100) if sessions > 0 else 0)
        })
    
    return render_template('deck_details.html',
                         deck=deck,
                         total_sessions=total_sessions,
                         completed_sessions=completed_sessions,
                         completion_rate=completion_rate,
                         student_performance=performance_data) 