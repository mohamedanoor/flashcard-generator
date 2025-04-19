import re

def process_text(text, format_type='plain'):
    """
    Process raw text input to prepare it for flashcard generation.
    
    Args:
        text (str): Raw text input from the user
        format_type (str): Type of input format ('plain', 'markdown', 'url')
        
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
    
    # For URLs, we would normally fetch content, but we'll skip that for simplicity
    # If needed, you could add URL processing using the requests library
    
    # For markdown, we would strip markdown formatting
    if format_type == 'markdown':
        # Simple markdown cleanup (just a basic example)
        processed_text = re.sub(r'#+ ', '', processed_text)  # Remove headings
        processed_text = re.sub(r'\*\*(.*?)\*\*', r'\1', processed_text)  # Remove bold
        processed_text = re.sub(r'\*(.*?)\*', r'\1', processed_text)  # Remove italic
    
    return processed_text