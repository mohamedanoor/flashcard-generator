from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import re
import json
import random

# Initialize the models - these will be loaded the first time they're needed
summarizer = None
qa_model = None

def initialize_models():
    """
    Initialize the transformer models for text processing
    """
    global summarizer, qa_model
    
    if summarizer is None:
        # T5 model for summarization and text generation
        print("Loading T5 model for summarization...")
        summarizer = pipeline("summarization", model="t5-small")
    
    if qa_model is None:
        # Question answering model
        print("Loading question answering model...")
        qa_model = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

def extract_key_points(text, max_length=512):
    """
    Extract key points from text
    
    Args:
        text (str): Input text
        max_length (int): Maximum length for processing
        
    Returns:
        list: List of key points
    """
    initialize_models()
    
    # For longer texts, process in chunks
    if len(text) > max_length:
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        all_points = []
        
        for chunk in chunks:
            # Get summary of the chunk
            summary = summarizer(chunk, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
            
            # Split into sentences and add to points
            sentences = re.split(r'(?<=[.!?])\s+', summary)
            all_points.extend([s for s in sentences if len(s) > 15])  # Only keep substantial sentences
            
        return all_points
    else:
        # For shorter texts, just summarize
        summary = summarizer(text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        return re.split(r'(?<=[.!?])\s+', summary)

def generate_question_from_point(point):
    """
    Generate a question from a key point
    
    Args:
        point (str): A key point extracted from the text
        
    Returns:
        tuple: (question, answer)
    """
    # Simple transformation approach - identify the main subject and create a question
    words = point.split()
    
    if len(words) < 5:  # Skip very short points
        return None
    
    # Check for common patterns to form questions
    if point.startswith("The ") or point.startswith("A "):
        subject_end = min(4, len(words))
        subject = " ".join(words[:subject_end])
        remaining = " ".join(words[subject_end:])
        question = f"What {remaining}?"
        answer = subject
    elif "is" in words[1:4]:
        # For "X is Y" statements
        is_index = words.index("is")
        subject = " ".join(words[:is_index])
        predicate = " ".join(words[is_index+1:])
        question = f"What is {subject}?"
        answer = predicate
    else:
        # Fallback: create a fill-in-the-blank question
        # Find the longest word as a key term
        key_word_index = max(range(len(words)), key=lambda i: len(words[i]) if len(words[i]) > 3 else 0)
        key_word = words[key_word_index]
        
        # Create question by replacing the key word with a blank
        question_words = words.copy()
        question_words[key_word_index] = "_______"
        question = " ".join(question_words)
        answer = key_word
    
    return (question, answer)

def generate_question_answer_pair(text):
    """
    Generate a more sophisticated question-answer pair using the QA model
    
    Args:
        text (str): Input text snippet
        
    Returns:
        tuple: (question, answer)
    """
    initialize_models()
    
    # Extract a potential answer from the text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    if not sentences:
        return None
    
    # Select a substantial sentence
    substantial_sentences = [s for s in sentences if len(s.split()) >= 5]
    if not substantial_sentences:
        return None
    
    sentence = random.choice(substantial_sentences)
    
    # Extract a potential answer - look for entities or important phrases
    words = sentence.split()
    potential_answers = []
    
    # Look for proper nouns (capitalized words not at the start of the sentence)
    for i, word in enumerate(words):
        if i > 0 and word[0].isupper() and len(word) > 3:
            potential_answers.append((i, word))
    
    # If no proper nouns, look for longer words
    if not potential_answers:
        for i, word in enumerate(words):
            if len(word) > 5 and word.isalpha():
                potential_answers.append((i, word))
    
    # If still no answers, use the subject of the sentence
    if not potential_answers and len(words) >= 3:
        potential_answers.append((1, words[1]))
    
    if not potential_answers:
        return None
    
    # Select an answer and its position
    ans_pos, answer = random.choice(potential_answers)
    
    # Create a question based on the answer type
    question_types = [
        f"What is {answer}?",
        f"What does the text say about {answer}?",
        f"How does the text describe {answer}?"
    ]
    
    question = random.choice(question_types)
    
    return (question, sentence)

def generate_flashcards(text, num_cards=10):
    """
    Generate flashcards from text
    
    Args:
        text (str): Processed text
        num_cards (int): Maximum number of flashcards to generate
        
    Returns:
        list: List of flashcard dictionaries with 'question' and 'answer' keys
    """
    try:
        # Extract key points
        key_points = extract_key_points(text)
        
        flashcards = []
        
        # Generate simple transformation questions
        for point in key_points:
            if len(flashcards) >= num_cards:
                break
                
            qa_pair = generate_question_from_point(point)
            if qa_pair:
                question, answer = qa_pair
                flashcards.append({
                    'question': question,
                    'answer': answer
                })
        
        # If we need more cards, generate QA pairs
        if len(flashcards) < num_cards:
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                if len(flashcards) >= num_cards:
                    break
                    
                qa_pair = generate_question_answer_pair(paragraph)
                if qa_pair:
                    question, answer = qa_pair
                    flashcards.append({
                        'question': question,
                        'answer': answer
                    })
        
        # If still not enough, create some general questions
        general_questions = [
            {"question": "What is the main topic of this text?", 
             "answer": summarizer(text[:1024], max_length=20, min_length=5, do_sample=False)[0]['summary_text']},
            {"question": "Summarize the key points in this text.", 
             "answer": summarizer(text[:1024], max_length=50, min_length=20, do_sample=False)[0]['summary_text']}
        ]
        
        while len(flashcards) < min(num_cards, 2):
            flashcards.append(general_questions.pop(0))
        
        return flashcards
    
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        # Return a simple set of flashcards if an error occurs
        return [
            {"question": "What is the main topic of this text?", 
             "answer": "Please review the text and identify the main topic."},
            {"question": "List one key concept from this text.", 
             "answer": "Please identify an important concept from the text."}
        ]