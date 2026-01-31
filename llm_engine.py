"""
Bookinator LLM Engine
Uses Ollama for local LLM and DuckDuckGo for web search.
"""

import requests
import json
import csv
import os
from typing import Optional
from ddgs import DDGS 

# Configuration
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "llama3.2" 
BOOKS_CSV_PATH = "data/books.csv"

SYSTEM_PROMPT = """You are Bookinator, an AI Quiz Host at the **Kolkata Book Fair (Boimela)**.
YOUR GOAL: Guess the visitor's book.

CONTEXT & BIAS:
- **Bias**: Expect **Bengali Literature** and Indian English authors.

**BENGALI LIT CHEAT SHEET (DO NOT CONFUSE THESE)**:
- **Feluda**: Detective by **Satyajit Ray**. (Assistant: Topshe).
- **Byomkesh Bakshi**: Detective by **Sharadindu Bandyopadhyay**. (Assistant: Ajit).
- **Kakababu**: Adventure series by **Sunil Gangopadhyay**. (Partner: Santu).
- **Tenida**: Humor/Adventure by **Narayan Gangopadhyay**. (Loc: Potol Danga).
- **Ghanada**: Tall tales by **Premendra Mitra**. (Mess bari).
- **Shonku**: Scientist by **Satyajit Ray**.
- **Kallol Jug**: Modernist movement (Achintya Kumar Sengupta, Buddhadeb Bosu).

GAMEPLAY RULES:
1.  **SHORT QUESTIONS**: Max **15 words** per question. Concise & direct.
2.  **ONE QUESTION**: Ask exactly one question at a time.
3.  **ACCEPTED ANSWERS**: Questions must be answerable by "Yes", "No", "Maybe", "Probably", "Probably Not".
4.  **NO CHIT-CHAT**: Output **ONLY** the question text or the [GUESS] block. No "Okay, I see", "Interesting", etc.
5.  **NO REPEATS**: Check `[NEGATIVE CONSTRAINTS]` and `[REJECTED BOOKS]`. Do NOT ask about these again.

GUESSING PROTOCOL:
Output the [GUESS] block ONLY when you are absolutely sure (Confidence > 90%).

[GUESS]
Confidence: 95%
Book: Feluda (Sonar Kella)
Reasoning: User confirmed Detective + Satyajit Ray + Desert setting.
Similar: 
- Royal Bengal Rahasya
- Joi Baba Felunath
[END GUESS]

INFO/CLARIFICATION:
If the user says "No" to a specifically confused entity (e.g. they say No to "Is it Byomkesh?" when you suspect Feluda), add:
[INFO] Note: Byomkesh is Sharadindu's detective. Feluda is Ray's.

SEARCHING:
Use [SEARCH: query] for silent searches.
"""

FINAL_TURN_PROMPT = """
STOP ASKING QUESTIONS. The game is over (20 Questions reached).
Based on the conversation, list your **Top 3 Most Likely Candidates**.
Format strictly as:
[FINAL]
1. Title by Author
2. Title by Author
3. Title by Author
[END FINAL]
Do not add any other text.
"""

class BookinatorLLM:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.conversation_history: list[dict] = []
        self.rejected_books: list[str] = []
        self.constraints: list[str] = []
        
        try:
            self.search_client = DDGS()
        except:
            self.search_client = None
            
        # Load Knowledge Base
        self.knowledge_base = self._load_knowledge_base()
            
        # Auto-discover Ollama URL
        self.base_url = self._find_ollama_url()
        print(f"DEBUG: Using Ollama URL: {self.base_url}")

    def _load_knowledge_base(self) -> list[dict]:
        """Load books from CSV into memory."""
        kb = []
        if os.path.exists(BOOKS_CSV_PATH):
            try:
                with open(BOOKS_CSV_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        kb.append(row)
                print(f"DEBUG: Loaded {len(kb)} books from knowledge base.")
            except Exception as e:
                print(f"ERROR: Failed to load KB: {e}")
        else:
            print(f"DEBUG: No local knowledge base found at {BOOKS_CSV_PATH}")
        return kb

    def _find_ollama_url(self) -> str:
        """Try to find where Ollama is running."""
        candidates = [
            "http://127.0.0.1:11434",
            "http://localhost:11434",
            "http://host.docker.internal:11434"
        ]
        for url in candidates:
            try:
                requests.get(f"{url}/api/tags", timeout=1)
                return url
            except:
                continue
        return "http://127.0.0.1:11434"
        
    def reset(self):
        """Clear conversation history and constraints."""
        self.conversation_history = []
        self.rejected_books = []
        self.constraints = []
        
    def _call_ollama(self, messages: list[dict]) -> str:
        """Make a request to the Ollama API (Synchronous)."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        print(f"DEBUG: Calling Ollama... (History: {len(messages)})")
        try:
            # Set a 45s timeout to prevent infinite hangs
            response = requests.post(url, json=payload, timeout=45) 
            response.raise_for_status()
            data = response.json()
            raw_content = data.get('message', {}).get('content', '')
            print("DEBUG: Ollama responded.")
            
            # Post-processing to clean up the LLM's messy output
            import re
            
            # 1. Remove Markdown bold/italic (* or **)
            clean_content = re.sub(r'\*\*|__|\*|_', '', raw_content)
            
            # 2. Remove "Question X:" prefixes
            clean_content = re.sub(r'^(Question \d+|Category):?\s*', '', clean_content, flags=re.IGNORECASE)
            
            # 3. Remove "Here is my question:" preambles
            clean_content = re.sub(r"^Here'?s my.*?question:?\s*", "", clean_content, flags=re.IGNORECASE)
            
            return clean_content.strip()
            
        except requests.exceptions.Timeout:
            print(f"DEBUG: Ollama Timed Out (45s).")
            return "Error: I'm thinking too hard and timed out. Please try again."
        except requests.exceptions.ConnectionError:
            print(f"DEBUG: Failed to connect to {url}")
            return "Error: Cannot connect to Ollama (Connection Refused). Is 'ollama serve' running?"
        except Exception as e:
            print(f"DEBUG: Ollama Error: {e}")
            return f"Error: {str(e)}"
    
    def _search_local_db(self, query: str, max_results: int = 5) -> list[dict]:
        """Search the local knowledge base."""
        if not self.knowledge_base:
            return []
            
        query_terms = query.lower().split()
        matches = []
        
        for book in self.knowledge_base:
            text = (book.get('title', '') + " " + book.get('authors', '')).lower()
            score = 0
            for term in query_terms:
                if term in text:
                    score += 1
            if score > 0:
                matches.append((score, book))
        
        matches.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for _, book in matches[:max_results]:
            results.append({
                'title': book.get('title', 'Unknown'),
                'snippet': f"Author: {book.get('authors', 'Unknown')}, Year: {book.get('publication_date', '')}",
                'source': 'Local Database'
            })
        return results

    def _web_search(self, query: str, max_results: int = 3) -> list[dict]:
        """Perform a web search using DuckDuckGo."""
        if not self.search_client:
            return [{'error': 'Search client not initialized'}]

        try:
            results = list(self.search_client.text(query, max_results=max_results))
            return [{
                'title': r.get('title', ''),
                'snippet': r.get('body', ''),
                'url': r.get('href', ''),
                'source': 'DuckDuckGo' 
            } for r in results]
        except Exception as e:
            return [{'error': str(e)}]
    
    def _process_search_request(self, response: str) -> tuple[str, Optional[list]]:
        """Check if LLM wants to search and process it (Hybrid: Local + Web)."""
        if '[SEARCH:' in response:
            try:
                start = response.find('[SEARCH:') + 8
                end = response.find(']', start)
                if end > start:
                    query = response[start:end].strip()
                    
                    # 1. Local Search
                    local_results = self._search_local_db(query)
                    
                    # 2. Web Search (always do it for now to ensure coverage, as local DB is limited)
                    web_results = self._web_search(query)
                    
                    # Combine
                    combined_results = local_results + web_results
                    return response, combined_results
            except:
                pass
        return response, None

    def _parse_info_bit(self, response: str) -> tuple[str, Optional[str]]:
        """Extract [INFO] block if present."""
        info_bit = None
        if '[INFO]' in response:
            parts = response.split('[INFO]')
            clean_text = parts[0].strip() # Question before the info
            info_bit = parts[1].strip()   # The info text
            return clean_text, info_bit
        return response, None
    
    def _parse_final_candidates(self, response: str) -> Optional[list]:
        """Parse the [FINAL] ... [END FINAL] block."""
        if '[FINAL]' not in response:
            return None
        
        try:
            start = response.find('[FINAL]') + 7
            end = response.find('[END FINAL]')
            if end == -1: end = len(response)
            
            block = response[start:end].strip()
            lines = block.split('\n')
            candidates = [line.strip() for line in lines if line.strip()]
            return candidates
        except:
            return None

    def _parse_guess(self, response: str) -> Optional[dict]:
        """Parse the structured guess block."""
        # 1. Standard Tag Parsing
        block = ""
        if '[GUESS]' in response:
            start_marker = "[GUESS]"
            end_marker = "[END GUESS]"
            start_idx = response.find(start_marker) + len(start_marker)
            end_idx = response.find(end_marker)
            if end_idx == -1: end_idx = len(response)
            block = response[start_idx:end_idx].strip()
            
        # 2. Fallback: Check for content outside tags or missing tags
        elif "Book:" in response and "Confidence:" in response:
            # Assume the whole response is the block, or the part starting with Confidence
            block = response
            
        if not block:
            return None
            
        try:
            lines = block.split('\n')
            guess_data = {
                'confidence': '0%',
                'book': 'Unknown',
                'reasoning': '',
                'similar': []
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Markers removal if they exist in the line
                clean_line = line.replace('[GUESS]', '').replace('[END GUESS]', '')
                
                if clean_line.lower().startswith('confidence:'):
                    guess_data['confidence'] = clean_line.split(':', 1)[1].strip()
                elif clean_line.lower().startswith('book:'):
                    guess_data['book'] = clean_line.split(':', 1)[1].strip()
                elif clean_line.lower().startswith('reasoning:'):
                    guess_data['reasoning'] = clean_line.split(':', 1)[1].strip()
                    current_section = 'reasoning'
                elif clean_line.lower().startswith('similar:'):
                    current_section = 'similar'
                elif line.startswith('-') and current_section == 'similar':
                    guess_data['similar'].append(line[1:].strip())
                elif current_section == 'reasoning':
                     guess_data['reasoning'] += " " + clean_line
            
            # Simple validation: If we didn't find a book, it's not a valid guess
            if guess_data['book'] == 'Unknown':
                return None
                
            return guess_data
        except Exception as e:
            print(f"Error parsing guess: {e}")
            return None

    def chat(self, user_message: str) -> dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        
        # Detect Rejections/Negations manually (Simple heuristic)
        last_assistant_msg = self.conversation_history[-1]['content'] if self.conversation_history else ""
        if 'no' in user_message.lower() or 'not' in user_message.lower():
            # If the user says No, we assume the previous question's premise is false.
            # We append this simple fact to specific constraints.
            self.constraints.append(f"User denied: '{last_assistant_msg}'")
            
        # Add Dynamic Constraints to the Context
        constraint_block = ""
        if self.rejected_books:
            constraint_block += f"\n[REJECTED BOOKS] (Do not guess these): {', '.join(self.rejected_books)}"
        if self.constraints:
            # Keep only last 5 constraints to avoid context bloat
            recent_constraints = self.constraints[-5:]
            constraint_block += f"\n[NEGATIVE CONSTRAINTS] (Avoid these): {'; '.join(recent_constraints)}"
            
        if constraint_block:
             messages.append({"role": "system", "content": constraint_block})

        # Check turn count (Assistant messages in history)
        turn_count = len([m for m in self.conversation_history if m['role'] == 'assistant'])
        
        # Game Over Logic (Question 20)
        is_final_turn = turn_count >= 19 # 0-indexed
        
        if is_final_turn:
            messages.append({"role": "user", "content": user_message + FINAL_TURN_PROMPT})
        else:
            messages.append({"role": "user", "content": user_message})
        
        response = self._call_ollama(messages)
        
        # 0. Check for Final Candidates
        final_candidates = self._parse_final_candidates(response)
        if final_candidates:
             return {
                'response': '',
                'search_results': None,
                'search_query': None,
                'guess': None,
                'final_candidates': final_candidates,
                'game_over': True
            }

        # 1. Check for search (ONLY after Turn 5 to prevent early hangs)
        search_results = None
        search_query = None
        
        if turn_count >= 5:
            processed_response, search_results = self._process_search_request(response)
            
            if search_results:
                try:
                    start = response.find('[SEARCH:') + 8
                    end = response.find(']', start)
                    search_query = response[start:end].strip()
                except:
                    search_query = "Unknown"
                
                messages.append({"role": "assistant", "content": response})
                
                # Format results for LLM
                search_context = f"\n\nSearch results for '{search_query}':\n"
                for i, r in enumerate(search_results[:5], 1): 
                    source_tag = f"[{r.get('source', 'Web')}]"
                    search_context += f"{i}. {source_tag} {r['title']}: {r['snippet']}\n"
                
                messages.append({"role": "user", "content": search_context + "\nNow continue."})
                response = self._call_ollama(messages)
        else:
            # If LLM tried to search early, ignore it and force a question generation if needed?
            # Actually, if it outputted JUST [SEARCH:...] and we ignore it, the user gets nothing.
            # We must strip the search tag or tell it to just ask.
            # But usually it outputs "Question... [SEARCH]" or similar.
            # If it outputs ONLY [SEARCH:...], we need to handle it.
            if '[SEARCH:' in response:
                print("DEBUG: Suppressing early search request.")
                # Strip the search command to show the rest, or if empty, ask it to continue
                # Improving: If it effectively just searched, we loop back with "Just ask a question".
                pass 

        # 2. Check for GUESS
        guess_data = self._parse_guess(response)
        
        # 3. Check for INFO bit
        display_text, info_bit = self._parse_info_bit(response)
        
        if guess_data:
            display_text = "" 
        
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return {
            'response': display_text,
            'info_bit': info_bit,
            'search_results': search_results,
            'search_query': search_query,
            'guess': guess_data,
            'final_candidates': None,
            'game_over': False
        }
    
    def start_game(self) -> dict:
        self.reset()
        # The prompt says "Start immediately with Question 1"
        return self.chat("Game Start. Ask the first Yes/No question about the book's language or format.")
