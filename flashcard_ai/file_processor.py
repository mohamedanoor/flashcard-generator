import os
import tempfile
from werkzeug.utils import secure_filename
from flashcard_ai.text_processor import process_text
from flashcard_ai.flashcard_generator import generate_flashcards

def process_files(files, difficulty='easy', extract_all=True, use_ocr=False):
    """
    Process uploaded files and generate flashcards
    
    Args:
        files: List of file objects from request
        difficulty (str): Difficulty level ('easy', 'medium', 'hard')
        extract_all (bool): Whether to extract all content
        use_ocr (bool): Whether to use OCR for images
        
    Returns:
        dict: Dictionary containing flashcards
    """
    extracted_text = ""
    
    # Process each file
    for file in files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            temp_path = temp.name
        
        try:
            # Extract text based on file type
            file_text = extract_text_from_file(temp_path, filename, use_ocr)
            if file_text:
                extracted_text += f"\n\n--- From {filename} ---\n\n"
                extracted_text += file_text
            
            # Remove temporary file
            os.unlink(temp_path)
        
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
            try:
                os.unlink(temp_path)  # Clean up temp file in case of error
            except:
                pass
    
    if not extracted_text:
        return {
            "main": [
                {"question": "No content could be extracted from the uploaded files.", 
                 "answer": "Try a different file format or check if the file contains extractable text."}
            ]
        }
    
    # Process the extracted text
    processed_text = process_text(extracted_text)
    
    # Generate flashcards
    return generate_flashcards(
        processed_text, 
        difficulty=difficulty,
        extract_definitions=extract_all,
        create_cloze=extract_all,
        question_answer=True
    )

def extract_text_from_file(file_path, filename, use_ocr=False):
    """
    Extract text from a file based on its type
    
    Args:
        file_path (str): Path to the temporary file
        filename (str): Original filename with extension
        use_ocr (bool): Whether to use OCR for images
        
    Returns:
        str: Extracted text
    """
    ext = os.path.splitext(filename)[1].lower()
    
    # Plain text file
    if ext in ['.txt', '.md', '.csv']:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return f"Could not read {filename} due to an error: {str(e)}"
    
    # For the initial implementation, let's handle just plain text files
    # and provide informational messages for other formats
    
    # PDF file
    elif ext == '.pdf':
        return f"PDF support is coming soon. Upload a text file (.txt) for now."
    
    # Word document
    elif ext in ['.docx', '.doc']:
        return f"Word document support is coming soon. Upload a text file (.txt) for now."
    
    # Image file
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        return f"Image text extraction is coming soon. Upload a text file (.txt) for now."
    
    # Unsupported file type
    else:
        return f"Unsupported file type: {ext}. Try uploading a text file (.txt)."