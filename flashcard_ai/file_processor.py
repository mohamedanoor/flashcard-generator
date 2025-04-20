import os
import tempfile
from werkzeug.utils import secure_filename
from flashcard_ai.text_processor import process_text
from flashcard_ai.flashcard_generator import generate_flashcards
import io

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
    processed_files = []
    
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
                processed_files.append(filename)
            
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
    flashcards = generate_flashcards(
        processed_text, 
        difficulty=difficulty,
        extract_definitions=extract_all,
        create_cloze=extract_all,
        question_answer=True,
        model=model  # Pass model parameter

    )
    
    # Add a special card mentioning the source files
    if "main" in flashcards and len(flashcards["main"]) > 0:
        source_card = {
            "question": "What files were used to generate these flashcards?",
            "answer": f"These flashcards were generated from: {', '.join(processed_files)}"
        }
        flashcards["main"].insert(0, source_card)
    
    return flashcards

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
    
    # PDF file
    elif ext == '.pdf':
        try:
            from pdfminer.high_level import extract_text as pdf_extract_text
            text = pdf_extract_text(file_path)
            
            # Clean up the text (remove excessive whitespace)
            import re
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Break into paragraphs where appropriate
            text = re.sub(r'(\. |\? |\! )(?=[A-Z])', r'\1\n\n', text)
            
            return text
        except ImportError:
            return "PDF extraction requires pdfminer.six package."
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return f"Could not extract text from {filename}: {str(e)}"
    
    # Word document
    elif ext in ['.docx', '.doc']:
        try:
            if ext == '.docx':
                import docx
                doc = docx.Document(file_path)
                full_text = []
                for para in doc.paragraphs:
                    full_text.append(para.text)
                return '\n\n'.join(full_text)
            else:
                # .doc files need additional processing
                return "Legacy .doc format is not directly supported. Please convert to .docx."
        except ImportError:
            return "Word document extraction requires python-docx package."
        except Exception as e:
            print(f"Error extracting text from Word document: {e}")
            return f"Could not extract text from {filename}: {str(e)}"
    
    # Image file
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        if use_ocr:
            try:
                import pytesseract
                from PIL import Image
                
                img = Image.open(file_path)
                return pytesseract.image_to_string(img)
            except ImportError:
                return "OCR requires pytesseract and Pillow packages."
            except Exception as e:
                print(f"Error performing OCR on image: {e}")
                return f"Could not extract text from {filename}: {str(e)}"
        else:
            return "Image files require OCR option to be enabled."
    
    # Unsupported file type
    else:
        return f"Unsupported file type: {ext}. Supported formats: TXT, PDF, DOCX."