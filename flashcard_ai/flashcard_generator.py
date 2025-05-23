import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_flashcards(text, difficulty='easy', extract_definitions=False, create_cloze=False, question_answer=True, model="gpt-3.5"):
    """
    Generate flashcards from text using OpenAI's API
    
    Args:
        text (str): Processed text
        difficulty (str): Difficulty level ('easy', 'medium', 'hard')
        extract_definitions (bool): Whether to extract definitions
        create_cloze (bool): Whether to create cloze deletions
        question_answer (bool): Whether to create question-answer pairs
        model (str): OpenAI model to use ('gpt-3.5-turbo', 'gpt-4')
        
    Returns:
        dict: Dictionary containing different types of flashcards
    """
    try:
        # Determine number of cards based on difficulty
        if difficulty == 'easy':
            num_cards = 5
        elif difficulty == 'medium':
            num_cards = 10
        else:  # hard
            num_cards = 15
        
        # Prepare detailed instructions for each card type
        instructions = []
        output_format = {}
        
        if question_answer:
            instructions.append("""
            Question-Answer pairs:
            - Identify key concepts, facts, and relationships
            - Create direct questions that test understanding
            - Format as {"question": "What is X?", "answer": "X is Y"}
            - Ensure answers are comprehensive yet concise
            - Focus on conceptual understanding rather than mere facts
            """)
            output_format["main"] = "List of question-answer objects with 'question' and 'answer' keys"
        
        if extract_definitions:
            instructions.append("""
            Definitions:
            - Identify important terms and concepts in the text
            - Create definition cards with the term as the question
            - Format as {"question": "What is [term]?", "answer": "definition of the term"}
            - Ensure definitions are accurate and capture the essence of the term
            """)
            output_format["definitions"] = "List of definition objects with 'question' and 'answer' keys"
        
        if create_cloze:
            instructions.append("""
            Fill-in-the-blank:
            - Take important sentences and replace key terms with blanks
            - The question should contain the sentence with a blank (use "_____")
            - The answer should be the missing word or phrase
            - Format as {"question": "Process of _____ involves cell division", "answer": "mitosis"}
            - Focus on terms that are central to understanding the concept
            """)
            output_format["cloze"] = "List of cloze deletion objects with 'question' and 'answer' keys"
        
        # Default if nothing is selected
        if not instructions:
            instructions.append("Create basic question-answer pairs")
            output_format["main"] = "List of question-answer objects"
        
        # Create enhanced prompts for GPT-4
        system_prompt = """
        You are an expert educator who creates high-quality flashcards from text.
        You must strictly follow the requested format for each flashcard type.
        Separate your output into the exact requested categories (main, definitions, cloze).
        
        IMPORTANT: You must generate the flashcards in the SAME LANGUAGE as the input text.
        If the input text is in French, create French flashcards. If it's in Spanish, create Spanish flashcards, etc.
        Never translate the content to another language - maintain the original language throughout.
        
        Guidelines for creating excellent flashcards:
        1. Each card should focus on a single concept or fact
        2. Questions should be clear and unambiguous
        3. Answers should be comprehensive yet concise
        4. Prioritize understanding over memorization
        5. Create flashcards that build upon each other in complexity
        6. Ensure factual accuracy and clarity in all cards
        """
        
        user_prompt = f"""
        Create flashcards from the following text, with a total of approximately {num_cards} cards distributed across the requested types.
        Difficulty level: {difficulty}
        
        Instructions for card types:
        {' '.join(instructions)}
        
        Format your response as a JSON object with these specific keys:
        {json.dumps(output_format, indent=2)}
        
        IMPORTANT: 
        - Generate all flashcards in the SAME LANGUAGE as the input text
        - DO NOT translate the content to another language
        - DO NOT mix card types - each type must go in its own specific section
        - For definition cards, focus ONLY on terminology definitions
        - For cloze cards, ALWAYS include blanks (____) in the question
        - Make all content concise and clear
        - For {difficulty} difficulty, ensure appropriate complexity: {'basic recall for beginners' if difficulty == 'easy' else 'deeper understanding and connections' if difficulty == 'medium' else 'advanced application and critical thinking'}
        
        TEXT TO PROCESS:
        {text}
        """
        
        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
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
        
        try:
            # Parse the JSON
            flashcards = json.loads(content)
        except json.JSONDecodeError:
            print(f"Error parsing JSON response: {content[:100]}...")
            # Create a basic structure based on requirements
            flashcards = {}
            if question_answer:
                flashcards["main"] = [{"question": "What is this text about?", "answer": "Key concepts from the provided text."}]
            if extract_definitions:
                flashcards["definitions"] = [{"question": "What is an important term?", "answer": "Definition of that term."}]
            if create_cloze:
                flashcards["cloze"] = [{"question": "This text discusses important _____.", "answer": "concepts"}]
        
        # Ensure all requested sections exist with at least empty arrays
        if question_answer and "main" not in flashcards:
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
                 "answer": "Review the text to identify key concepts."}
            ]
        }