
# gen-visual-backend

This project is a backend service for generating event posters using AI and LLM-powered prompt parsing.

## Features
- Accepts natural language prompts and converts them to structured JSON using Gemini LLM.
- Generates event posters with custom text, fonts, logos, and face images.
- FastAPI backend for easy integration with any frontend.

## Setup Instructions

### 1. Clone the Repository
```
git clone https://github.com/ShriGaneshPurohit/gen-visual-backend
cd gen-visual-backend
```

### 2. Create and Activate a Virtual Environment (Recommended)
```
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```
pip install -r requirements.txt
```

### 4. Set Up Gemini API Key
Create a `.env` file in the project root with your Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the Backend Server
```
uvicorn main:app --reload
```

### 6. Test the Middleware and Poster Generation
Edit `test.py` to change the prompt or font as needed, then run:
```
python test.py
```
The generated poster will be saved in the `outputs/` directory.

## Project Structure
- `main.py` - FastAPI backend
- `middleware/` - LLM-powered prompt parser
- `script1.py`, `script2.py` - Poster and slot generation logic
- `assets/`, `fonts/`, `logos/`, `icons/` - Required images and fonts
- `outputs/` - Generated posters

## Notes
- Make sure all required asset files (images, fonts) are present in their respective folders.
- The middleware uses Gemini LLM for robust prompt parsing. If the API is unavailable, it falls back to default values.

## API Usage
- You can use the interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test the API.
- For JSON fields (like `poster_text_content` and `custom_font_sizes`), paste the JSON as a string in the form.
- For list fields (like `logo_paths`), use comma-separated values.

## License
MIT
