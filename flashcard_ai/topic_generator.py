import requests
import re
from bs4 import BeautifulSoup
from flashcard_ai.text_processor import process_text
from flashcard_ai.flashcard_generator import generate_flashcards

def search_topic(topic, num_results=2):
    """
    Search for information about a topic
    
    Args:
        topic (str): The topic to search for
        num_results (int): Number of search results to return
        
    Returns:
        str: Compiled text from search results
    """
    try:
        # Create a search query
        search_query = f"{topic} facts information overview"
        
        # Make a request to a search engine
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Using DuckDuckGo's HTML response
        response = requests.get(
            f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}",
            headers=headers
        )
        
        if response.status_code != 200:
            return f"Error searching for information: HTTP {response.status_code}"
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find search results
        results = soup.find_all('div', class_='result__body')
        
        # Extract text from first few results
        extracted_text = []
        
        for i, result in enumerate(results):
            if i >= num_results:
                break
                
            # Get the snippet text
            snippet = result.find('a', class_='result__snippet')
            if snippet:
                extracted_text.append(snippet.text.strip())
                
            # Try to get more text from the link
            link = result.find('a', class_='result__url')
            if link and link.has_attr('href'):
                try:
                    page_url = link['href']
                    page_response = requests.get(page_url, headers=headers, timeout=5)
                    
                    if page_response.status_code == 200:
                        page_soup = BeautifulSoup(page_response.text, 'html.parser')
                        
                        # Remove script and style elements
                        for script in page_soup(['script', 'style']):
                            script.extract()
                            
                        # Get text from paragraphs
                        paragraphs = page_soup.find_all('p')
                        relevant_paragraphs = []
                        
                        for p in paragraphs:
                            p_text = p.get_text().strip()
                            # Only include substantial paragraphs
                            if len(p_text) > 100 and topic.lower() in p_text.lower():
                                relevant_paragraphs.append(p_text)
                                
                        # Add up to 2 relevant paragraphs to save memory
                        extracted_text.extend(relevant_paragraphs[:2])
                        
                except Exception as e:
                    print(f"Error fetching page content: {e}")
        
        # Combine all text
        combined_text = "\n\n".join(extracted_text)
        
        # If we couldn't get enough text, add some generic information
        if len(combined_text) < 500:
            combined_text += f"\n\n{topic} is an important subject that has various key aspects worth studying. Understanding {topic} requires examining its main components and historical context."
        
        # Limit text length to avoid memory issues
        if len(combined_text) > 2000:
            combined_text = combined_text[:2000]
            
        return combined_text
        
    except Exception as e:
        print(f"Error in topic search: {e}")
        return f"Information about {topic} could not be retrieved due to an error."

def generate_topic_flashcards(topic, difficulty='easy', include_definitions=True, include_facts=True, include_dates=False):
    """
    Generate flashcards for a specific topic
    
    Args:
        topic (str): The topic to generate flashcards for
        difficulty (str): Difficulty level ('easy', 'medium', 'hard')
        include_definitions (bool): Whether to include definitions
        include_facts (bool): Whether to include key facts
        include_dates (bool): Whether to include dates/timeline
        
    Returns:
        dict: Dictionary containing different types of flashcards
    """
    try:
        # Search for information about the topic
        topic_text = search_topic(topic, num_results=2)  # Limit to 2 results to save memory
        
        # Process the text
        processed_text = process_text(topic_text)
        
        # Generate flashcards using the existing generator
        flashcards = generate_flashcards(
            processed_text, 
            difficulty=difficulty,
            extract_definitions=include_definitions,
            create_cloze=include_facts,
            question_answer=True
        )
        
        # Add topic context to beginning of the list
        if "main" in flashcards and isinstance(flashcards["main"], list):
            flashcards["main"].insert(0, {
                "question": f"What is the main focus of {topic}?",
                "answer": f"These flashcards cover key information about {topic}."
            })
        else:
            flashcards["main"] = [{
                "question": f"What is {topic}?", 
                "answer": f"These flashcards cover key information about {topic}."
            }]
        
        return flashcards
        
    except Exception as e:
        print(f"Error generating topic flashcards: {e}")
        # Return fallback flashcards
        return {
            "main": [
                {"question": f"What is {topic}?", 
                 "answer": f"This is a key concept related to {topic}."},
                {"question": f"Why is {topic} important?", 
                 "answer": f"Understanding {topic} is important for several reasons."}
            ]
        }