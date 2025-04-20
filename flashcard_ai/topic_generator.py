import requests
import re
import os
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        
        # Limit text length to avoid excessive tokens
        if len(combined_text) > 4000:
            combined_text = combined_text[:4000]
            
        return combined_text
        
    except Exception as e:
        print(f"Error in topic search: {e}")
        return f"Information about {topic} could not be retrieved due to an error."

def generate_topic_flashcards(topic, difficulty='easy', include_definitions=True, include_facts=True, include_dates=False, model="gpt-4"):
    """
    Generate flashcards for a specific topic using OpenAI
    
    Args:
        topic (str): The topic to generate flashcards for
        difficulty (str): Difficulty level ('easy', 'medium', 'hard')
        include_definitions (bool): Whether to include definitions
        include_facts (bool): Whether to include key facts
        include_dates (bool): Whether to include dates/timeline
        model (str): OpenAI model to use ('gpt-3.5-turbo', 'gpt-4')
        
    Returns:
        dict: Dictionary containing different types of flashcards
    """
    try:
        # Skip scraping if user just wants AI-generated content
        if include_facts:
            # Search for information about the topic
            topic_text = search_topic(topic, num_results=2)
        else:
            # Just use the topic name for pure AI generation
            topic_text = f"Generate flashcards about {topic}."
        
        # Determine number of cards based on difficulty
        if difficulty == 'easy':
            num_cards = 5
        elif difficulty == 'medium':
            num_cards = 8
        else:  # hard
            num_cards = 10
        
        # Create flashcard types
        card_types = []
        if include_facts:
            card_types.append("fact-based question-answer pairs")
        if include_definitions:
            card_types.append("key term definitions")
        if include_dates:
            card_types.append("important dates and timeline events")
        
        # Default if nothing is selected
        if not card_types:
            card_types = ["general knowledge question-answer pairs"]
        
        # Create enhanced prompts for GPT-4
        system_prompt = """
        You are an expert educator who creates high-quality flashcards about specific topics.
        Your goal is to create effective study materials that help users learn important concepts.
        
        IMPORTANT: You must generate the flashcards in the SAME LANGUAGE as the topic input.
        If the topic is in French, create French flashcards. If it's in Spanish, create Spanish flashcards, etc.
        Never translate the content to another language - maintain the original language throughout.
        
        Guidelines for creating excellent flashcards:
        1. Each card should focus on a single concept or fact
        2. Questions should be clear and promote critical thinking
        3. Answers should be comprehensive yet concise
        4. Prioritize understanding over memorization
        5. Create flashcards that build upon each other in complexity
        6. Ensure factual accuracy and clarity in all cards
        """
        
        user_prompt = f"""
        Please create {num_cards} flashcards about the topic: {topic}
        Difficulty level: {difficulty}
        
        Include these card types: {', '.join(card_types)}.
        
        Format your response as a JSON object with these keys:
        - "main": A list of question-answer flashcards with "question" and "answer" keys
        - "definitions": A list of term definition flashcards (if requested)
        - "cloze": A list of fill-in-the-blank flashcards (if requested)
        
        Each list should contain objects with "question" and "answer" keys.
        Make the content concise, clear, and focused on the most important concepts.
        
        IMPORTANT:
        - Generate all flashcards in the SAME LANGUAGE as the topic input
        - DO NOT translate the content to another language
        - For {difficulty} difficulty, ensure appropriate complexity: {'basic recall for beginners' if difficulty == 'easy' else 'deeper understanding and connections' if difficulty == 'medium' else 'advanced application and critical thinking'}
        
        Use this information if relevant:
        {topic_text}
        """
        
        # Call the OpenAI API using the new client format
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract and parse the content from the new response format
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
            # If JSON parsing fails, create a simple fallback response
            print(f"Error parsing JSON response: {content[:100]}...")
            return {
                "main": [
                    {"question": f"What is {topic}?", 
                     "answer": f"This is a key concept related to {topic}."},
                    {"question": f"Why is {topic} important?", 
                     "answer": f"Understanding {topic} is important for several reasons."}
                ]
            }
        
        # Ensure all required sections exist
        if "main" not in flashcards:
            flashcards["main"] = []
        if include_definitions and "definitions" not in flashcards:
            flashcards["definitions"] = []
        if include_dates and "dates" not in flashcards:
            flashcards["dates"] = []
        
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