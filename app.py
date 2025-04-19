import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from flashcard_ai.text_processor import process_text
from flashcard_ai.flashcard_generator import generate_flashcards
from flashcard_ai.topic_generator import generate_topic_flashcards

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Get text input from the request
    text_input = request.form.get('text_input')
    
    if not text_input:
        return jsonify({'error': 'No text provided'}), 400
    
    # Process the text
    processed_text = process_text(text_input)
    
    # Generate flashcards
    try:
        flashcards = generate_flashcards(processed_text)
        return jsonify({'flashcards': flashcards})
    except Exception as e:
        print(f"Error in Flask route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_from_topic', methods=['POST'])
def generate_from_topic():
    # Get topic input from the request
    topic_input = request.form.get('topic_input')
    
    if not topic_input:
        return jsonify({'error': 'No topic provided'}), 400
    
    # Generate flashcards from the topic
    try:
        flashcards = generate_topic_flashcards(topic_input)
        return jsonify({'flashcards': flashcards})
    except Exception as e:
        print(f"Error in topic generation route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html')

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))