from transformers import pipeline
import re
import json
import random

# Initialize the models
summarizer = None
qa_model = None

def initialize_models():
    """
    Initialize the transformer models for text processing
    """
    global summarizer, qa_model
    
    if summarizer is None:
        # Use a smaller model for summarization
        print("Loading summarization model...")
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")
    
    if qa_model is None:
        # Question answering model - only load when needed
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

def extract_definitions(text):
    """
    Extract definitions from text
    
    Args:
        text (str): Processed text
        
    Returns:
        list: List of definition flashcards
    """
    definitions = []
    
    # Look for definition patterns like "X is Y", "X means Y", "X refers to Y"
    definition_patterns = [
        r'([A-Z][^.!?:]{2,40}?) is ([^.!?]+)',
        r'([A-Z][^.!?:]{2,40}?) means ([^.!?]+)',
        r'([A-Z][^.!?:]{2,40}?) refers to ([^.!?]+)',
        r'([A-Z][^.!?:]{2,40}?) defined as ([^.!?]+)',
        r'([A-Z][^.!?:]{2,40}?): ([^.!?]+)'
    ]
    
    for pattern in definition_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            term, definition = match
            # Clean up
            term = term.strip()
            definition = definition.strip()
            
            if len(term) > 2 and len(definition) > 5:
                definitions.append({
                    "question": f"What is {term}?",
                    "answer": definition
                })
    
    return definitions

def create_cloze_deletions(text):
    """
    Create cloze (fill-in-the-blank) flashcards
    
    Args:
        text (str): Processed text
        
    Returns:
        list: List of cloze flashcards
    """
    cloze_cards = []
    
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        # Only process substantial sentences (min 6 words)
        if len(sentence.split()) >= 6:  # Fixed: Changed undefined 'a' to '6'
            # Find important words (nouns, technical terms)
            words = sentence.split()
            
            # Get potential keywords (longer words, possibly important)
            potential_keywords = []
            for i, word in enumerate(words):
                # Look for capitalized words or longer words that aren't at the start
                if ((i > 0 and word[0].isupper() and len(word) > 3) or 
                    (len(word) > 6 and word.isalpha())):
                    potential_keywords.append((i, word))
            
            # Create cloze deletion if we found keywords
            if potential_keywords:
                # Take a random important word
                idx, keyword = random.choice(potential_keywords)
                
                # Create cloze question
                cloze_words = words.copy()
                cloze_words[idx] = "________"
                question = " ".join(cloze_words)
                
                cloze_cards.append({
                    "question": question,
                    "answer": keyword
                })
    
    # Limit to reasonable number
    return cloze_cards[:10]

def generate_flashcards(text, difficulty='easy', extract_definitions=False, create_cloze=False, question_answer=True):
    """
    Generate flashcards from processed text
    
    Args:
        text (str): Processed text
        difficulty (str): Difficulty level ('easy', 'medium', 'hard')
        extract_definitions (bool): Whether to extract definitions
        create_cloze (bool): Whether to create cloze deletions
        question_answer (bool): Whether to create question-answer pairs
        
    Returns:
        dict: Dictionary containing different types of flashcards
    """
    try:
        # Adjust parameters based on difficulty
        if difficulty == 'easy':
            num_cards = 6
            chunk_size = 400
        elif difficulty == 'medium':
            num_cards = 8
            chunk_size = 500
        else:  # hard
            num_cards = 10
            chunk_size = 600
        
        result = {}
        main_cards = []
        
        # Generate question-answer pairs if requested
        if question_answer:
            # Extract key points
            key_points = extract_key_points(text)
            
            # Generate cards from key points
            for point in key_points:
                if len(main_cards) >= num_cards:
                    break
                    
                # Convert statements to questions
                words = point.split()
                if len(words) < 5:  # Skip very short points
                    continue
                
                # Create different question types based on the content
                if point.startswith("The ") or point.startswith("A "):
                    subject_end = min(4, len(words))
                    subject = " ".join(words[:subject_end])
                    remaining = " ".join(words[subject_end:])
                    question = f"What {remaining}?"
                    answer = subject
                    main_cards.append({"question": question, "answer": answer})
                
                elif "is" in words[1:4]:
                    # For "X is Y" statements
                    is_index = words.index("is")
                    subject = " ".join(words[:is_index])
                    predicate = " ".join(words[is_index+1:])
                    question = f"What is {subject}?"
                    answer = predicate
                    main_cards.append({"question": question, "answer": answer})
                
                else:
                    # For other statements, create a "What about X?" question
                    if len(words) > 5:
                        # Find a key noun or term to ask about
                        potential_topics = []
                        for i, word in enumerate(words):
                            if i > 0 and word[0].isupper() and len(word) > 3:
                                potential_topics.append(word)
                        
                        if potential_topics:
                            topic = random.choice(potential_topics)
                            question = f"What does the text say about {topic}?"
                            answer = point
                            main_cards.append({"question": question, "answer": answer})
        
        # Add to result
        result["main"] = main_cards
        
        # Extract definitions if requested
        if extract_definitions:
            result["definitions"] = extract_definitions(text)
        
        # Create cloze deletions if requested
        if create_cloze:
            result["cloze"] = create_cloze_deletions(text)
        
        # If no cards were generated, add a generic card
        if len(main_cards) == 0 and not result.get("definitions") and not result.get("cloze"):
            result["main"] = [
                {"question": "What is the main topic of this text?", 
                 "answer": summarizer(text[:1024], max_length=50, min_length=20, do_sample=False)[0]['summary_text']}
            ]
        
        return result
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        # Return basic cards on error
        return {
            "main": [
                {"question": "What is the main topic of this text?", 
                 "answer": "Review the text to identify key concepts."},
                {"question": "What are the key points in this text?",
                 "answer": "The text covers several important aspects of the topic."}
            ]
        }