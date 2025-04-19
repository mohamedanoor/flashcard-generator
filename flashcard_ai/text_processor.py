import re

def process_text(text):
    """
    Process raw text input to prepare it for flashcard generation.
    
    Args:
        text (str): Raw text input from the user
        
    Returns:
        str: Processed text ready for flashcard generation
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    
    # Remove very short paragraphs (likely not content-rich)
    paragraphs = [p for p in paragraphs if len(p) > 20]
    
    # Join the paragraphs back
    processed_text = '\n\n'.join(paragraphs)
    
    return processed_text