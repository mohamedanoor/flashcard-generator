import os
import sys
import gc
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from flashcard_ai.text_processor import process_text
from flashcard_ai.flashcard_generator import generate_flashcards
from flashcard_ai.topic_generator import generate_topic_flashcards
from flashcard_ai.file_processor import process_files  # Add this line
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
        question_answer = request.form.get('question_answer', 'true') == 'true'  # Default to True
        
        if not text_input:
            return jsonify({'error': 'No text provided'}), 400
        
        # Limit input size to save on tokens
        if len(text_input) > 4000:
            text_input = text_input[:4000]
        
        # Process the text
        processed_text = process_text(text_input, format_type)
        
        # Generate flashcards using OpenAI
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
        
        # Generate flashcards from the topic using OpenAI
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
        gc.collect()  # Force garbage collection on error
        return jsonify({'error': str(e)}), 500

@app.route('/generate_from_files', methods=['POST'])
def generate_from_files():
    try:
        # Get files from the request
        files = request.files.getlist('files')
        difficulty = request.form.get('difficulty', 'easy')
        
        # Get options (converting string 'true'/'false' to actual booleans)
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
        import gc
        gc.collect()
        
        return jsonify({
            'flashcards': flashcards,
            'main': flashcards.get('main', []),
            'definitions': flashcards.get('definitions', []),
            'cloze': flashcards.get('cloze', [])
        })
    except Exception as e:
        print(f"Error in file processing route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/flashcards')
def flashcards():
    return render_template('flashcards.html')

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))