# middleware.py
# This file contains the middleware logic to process prompts from the frontend and convert them to JSON format for the backend.
import os
import requests
import json
from dotenv import load_dotenv

def process_prompt(prompt: str) -> dict:
    """
    Process the incoming prompt string and convert it to the expected JSON format for the backend.
    This version uses simple keyword extraction to fill the fields if present in the prompt.
    """
        
        # Default values (used as fallback)
    default_poster_text_content = {
            'campus_name': "Bangalore Central Campus",
            'department_name': "Department of Computer Science",
            'type_of_event': "Annual Tech Fest\nCode Genesis 2025",
            'about_event': "A hands-on workshop exploring the latest advancements in Generative AI, from foundational models to practical applications.",
            "speaker 1": "Dr. Evelyn Reed",
            "designation 1": "Chief AI Scientist, Futura Corp",
            'date': "August 22, 2025",
            'time': "9:00 AM - 12:00 PM",
            'venue': "Central Block, 10th Floor, Campus View",
            'footer': "School of Sciences\nDesigned by AI"
        }

    custom_font_sizes = {
            'type_of_event': 55,
            'campus_name': 45,
            'department_name': 50,
            'about_event': 35,
            'venue': 25,
            'date': 25,
            'time': 25
        }

        # LLM (Gemini) integration


    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        # Try to load from .env manually if not set
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    print("GEMINI_API_KEY loaded:", bool(GEMINI_API_KEY))

    # Gemini API endpoint (v1beta, correct model and header)
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" if GEMINI_API_KEY else None

    # System prompt for the LLM
    system_prompt = (
        "Extract the following fields from the user prompt and return them as a JSON object with these keys: "
        "campus_name, department_name, type_of_event, about_event, speaker 1, designation 1, date, time, venue, footer. "
        "For 'about_event', keep it short (max 15 words) but detailed. "
        "If a field is missing, use an empty string. Respond ONLY with the JSON object."
    )

    llm_response = None
    if GEMINI_API_URL:
        try:
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": system_prompt + "\nPrompt: " + prompt}]}
                ]
            }
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY
            }
            resp = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload), timeout=10)
            print("LLM raw response:", resp.text)
            if resp.status_code == 200:
                candidates = resp.json().get("candidates", [])
                if candidates:
                    import re
                    # Try to extract JSON from the LLM response
                    text = candidates[0]["content"]["parts"][0]["text"]
                    match = re.search(r'\{.*\}', text, re.DOTALL)
                    if match:
                        llm_response = json.loads(match.group(0))
            else:
                print(f"LLM HTTP error: {resp.status_code}")
        except Exception as e:
            print("LLM Exception:", e)


    poster_text_content = default_poster_text_content.copy()
    if llm_response:
        for k in poster_text_content:
            if k in llm_response and llm_response[k]:
                poster_text_content[k] = llm_response[k]

    # Post-process 'designation 1' to remove any '\n' (let rendering logic handle line breaks)
    desig = poster_text_content.get('designation 1', '')
    if desig:
        poster_text_content['designation 1'] = desig.replace('\\n', '').replace('\n', '').strip()

    return {
        'poster_text_content': poster_text_content,
        'custom_font_sizes': custom_font_sizes
    }

# Example usage (for testing):
if __name__ == "__main__":
    test_prompt = "Generate a poster for World Trade Organization event."
    result = process_prompt(test_prompt)
    print(result)
