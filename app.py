import os
import sys
import gc
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import tempfile
from datetime import datetime
from flask_weasyprint import HTML, render_pdf

from flashcard_ai.text_processor import process_text
from flashcard_ai.flashcard_generator import generate_flashcards
from flashcard_ai.topic_generator import generate_topic_flashcards
from flashcard_ai.file_processor import process_files
from models import db, User, Deck

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-flashcards')

# Fix potential Postgres connection string format issue
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
else:
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///flashcards.db')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# Authentication routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('signup'))
            
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        flash('Account created successfully!')
        return redirect(url_for('index'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('login'))

# Main application routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Get text input from the request
        text_input = request.form.get('text_input')
        format_type = request.form.get('format', 'plain')
        difficulty = request.form.get('difficulty', 'easy')
        
        # Get advanced options
        extract_definitions = request.form.get('extract_definitions') == 'true'
        create_cloze = request.form.get('create_cloze') == 'true'
        question_answer = request.form.get('question_answer', 'true') == 'true'
        
        if not text_input:
            return jsonify({'error': 'No text provided'}), 400
        
        # Limit input size
        if len(text_input) > 5000:
            text_input = text_input[:5000]
        
        # Process the text
        processed_text = process_text(text_input, format_type)
        
        # Generate flashcards
        flashcards = generate_flashcards(
            processed_text, 
            difficulty=difficulty,
            extract_definitions=extract_definitions,
            create_cloze=create_cloze,
            question_answer=question_answer
        )
        
        # Force garbage collection to free memory
        gc.collect()
        
        return jsonify({
            'flashcards': flashcards,
            'main': flashcards.get('main', []),
            'definitions': flashcards.get('definitions', []),
            'cloze': flashcards.get('cloze', [])
        })
    except Exception as e:
        print(f"Error in generate route: {str(e)}")
        gc.collect()  # Force garbage collection on error
        return jsonify({'error': str(e)}), 500

@app.route('/generate_from_topic', methods=['POST'])
def generate_from_topic():
    try:
        # Get topic input from the request
        topic_input = request.form.get('topic_input')
        difficulty = request.form.get('difficulty', 'easy')
        
        # Get advanced options
        include_definitions = request.form.get('include_definitions') == 'true'
        include_facts = request.form.get('include_facts') == 'true'
        include_dates = request.form.get('include_dates') == 'true'
        
        if not topic_input:
            return jsonify({'error': 'No topic provided'}), 400
        
        # Generate flashcards from the topic
        flashcards = generate_topic_flashcards(
            topic_input,
            difficulty=difficulty,
            include_definitions=include_definitions,
            include_facts=include_facts,
            include_dates=include_dates
        )
        
        # Force garbage collection to free memory
        gc.collect()
        
        return jsonify({
            'flashcards': flashcards,
            'main': flashcards.get('main', []),
            'definitions': flashcards.get('definitions', []),
            'cloze': flashcards.get('cloze', [])
        })
    except Exception as e:
        print(f"Error in topic generation route: {str(e)}")
        gc.collect()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_from_files', methods=['POST'])
def generate_from_files():
    try:
        # Get files from the request
        files = request.files.getlist('files')
        difficulty = request.form.get('difficulty', 'easy')
        
        # Get advanced options
        extract_all = request.form.get('extract_all') == 'true'
        use_ocr = request.form.get('use_ocr') == 'true'
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files provided'}), 400
        
        # Process files
        flashcards = process_files(
            files,
            difficulty=difficulty,
            extract_all=extract_all,
            use_ocr=use_ocr
        )
        
        # Force garbage collection to free memory
        gc.collect()
        
        return jsonify({
            'flashcards': flashcards,
            'main': flashcards.get('main', []),
            'definitions': flashcards.get('definitions', []),
            'cloze': flashcards.get('cloze', [])
        })
    except Exception as e:
        print(f"Error in file processing route: {str(e)}")
        gc.collect()
        return jsonify({'error': str(e)}), 500

@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html')

# Deck management routes
@app.route('/save_deck', methods=['POST'])
def save_deck():
    try:
        data = request.json
        title = data.get('title')
        cards = data.get('cards')
        
        if not title or not cards:
            return jsonify({'error': 'Missing title or cards data'}), 400
            
        # If user is logged in, save to database
        if current_user.is_authenticated:
            deck = Deck(
                title=title,
                user_id=current_user.id
            )
            deck.set_cards(cards)
            
            db.session.add(deck)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Deck saved to your account',
                'deck_id': deck.id
            })
        else:
            # For non-logged in users, just return success (they'll save locally)
            return jsonify({
                'success': True,
                'message': 'Deck saved locally'
            })
    except Exception as e:
        print(f"Error saving deck: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_deck/<int:deck_id>')
@login_required
def download_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    
    # Ensure user owns this deck
    if deck.user_id != current_user.id:
        flash('You do not have permission to download this deck')
        return redirect(url_for('my_decks'))
    
    # Get the cards
    cards = deck.get_cards()
    
    # Create HTML for the PDF
    html_content = render_template(
        'pdf_template.html',
        title=deck.title,
        created=deck.created_at.isoformat(),
        cards=cards
    )
    
    # Generate PDF from HTML
    return render_pdf(HTML(string=html_content), 
                     download_filename=f"{deck.title.replace(' ', '_')}.pdf")

@app.route('/download_deck_direct', methods=['POST'])
def download_deck_direct():
    """Download deck directly from the form submission"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Create HTML for the PDF
        html_content = render_template(
            'pdf_template.html',
            title=data.get('title', 'Flashcards'),
            created=datetime.utcnow().isoformat(),
            cards=data.get('cards', {})
        )
        
        # Generate PDF from HTML
        return render_pdf(HTML(string=html_content), 
                         download_filename=f"{data.get('title', 'flashcards').replace(' ', '_')}.pdf")
    except Exception as e:
        print(f"Error downloading deck: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/my_decks')
@login_required
def my_decks():
    decks = Deck.query.filter_by(user_id=current_user.id).order_by(Deck.created_at.desc()).all()
    return render_template('my_decks.html', decks=decks)

@app.route('/load_deck/<int:deck_id>')
@login_required
def load_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    
    # Ensure user owns this deck
    if deck.user_id != current_user.id:
        flash('You do not have permission to access this deck')
        return redirect(url_for('my_decks'))
    
    # Update last studied timestamp
    deck.last_studied = datetime.utcnow()
    db.session.commit()
    
    return render_template('flashcards.html', deck=deck)

@app.route('/delete_deck/<int:deck_id>', methods=['POST'])
@login_required
def delete_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    
    # Ensure user owns this deck
    if deck.user_id != current_user.id:
        flash('You do not have permission to delete this deck')
        return redirect(url_for('my_decks'))
    
    db.session.delete(deck)
    db.session.commit()
    
    flash('Deck deleted successfully')
    return redirect(url_for('my_decks'))

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))