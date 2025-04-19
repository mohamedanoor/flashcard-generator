import os
import openai
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_flashcards(text, difficulty='easy', extract_definitions=False, create_cloze=False, question_answer=True):
    """
    Generate flashcards from text using OpenAI's API
    
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
        # Determine number of cards based on difficulty
        if difficulty == 'easy':
            num_cards = 5
        elif difficulty == 'medium':
            num_cards = 8
        else:  # hard
            num_cards = 10
        
        # Prepare card types based on options
        card_types = []
        if question_answer:
            card_types.append("question-answer pairs")
        if extract_definitions:
            card_types.append("term definitions")
        if create_cloze:
            card_types.append("fill-in-the-blank")
        
        # Default if nothing is selected
        if not card_types:
            card_types = ["question-answer pairs"]
        
        # Create the prompt
        system_prompt = """
        You are an expert educator who creates high-quality flashcards from text.
        Your goal is to extract the most important concepts and create effective study materials.
        """
        
        user_prompt = f"""
        Please create {num_cards} flashcards from the following text. 
        Difficulty level: {difficulty}.
        
        Include these card types: {', '.join(card_types)}.
        
        Format your response as a JSON object with these keys:
        - "main": A list of question-answer flashcards with "question" and "answer" keys
        - "definitions": A list of term definition flashcards (if requested)
        - "cloze": A list of fill-in-the-blank flashcards (if requested)
        
        Each list should contain objects with "question" and "answer" keys.
        Make the content concise, clear, and focused on the most important concepts.
        
        TEXT TO PROCESS:
        {text}
        """
        
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # You can use "gpt-4" for higher quality but higher cost
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        # Extract and parse the content
        content = response.choices[0].message.content
        
        # Clean up the response to ensure it's valid JSON
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse the JSON
        flashcards = json.loads(content)
        
        # Ensure all required sections exist
        if "main" not in flashcards:
            flashcards["main"] = []
        if extract_definitions and "definitions" not in flashcards:
            flashcards["definitions"] = []
        if create_cloze and "cloze" not in flashcards:
            flashcards["cloze"] = []
        
        return flashcards
        
    except Exception as e:
        print(f"Error generating flashcards with OpenAI: {e}")
        # Return basic cards on error
        return {
            "main": [
                {"question": "What is the main topic of this text?", 
                 "answer": "Review the text to identify key concepts."},
                {"question": "What are the key points in this text?",
                 "answer": "The text covers several important aspects of the topic."}
            ]
        }