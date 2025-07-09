# Poster Generator

This project generates customizable A4 posters (2480x3508px at 300 DPI) for university events using the Gemini API and canvas rendering.

## Setup
1. **Install Dependencies**:
   - Run `npm install` to install required packages (`canvas`, `dotenv`, `readline`).
2. **Configure Environment**:
   - Create a `.env` file in the project root with:

```
GEMINI_API_KEY=your_actual_api_key_here
```

Replace `your_actual_api_key_here` with a valid free-tier Gemini API key.
3. **Prepare Images**:
- Create an `images` folder in the project directory.
- Add speaker images (e.g., `speaker1.jpg`, `speaker2.jpg`) and a university logo (e.g., `logo.jpg`), ensuring each is a PNG or JPEG file under 5MB.
4. **Run the Project**:
- Use `npm start` or `npm test` to launch the interactive poster generator.

## Usage
- Follow the prompts to enter:
  - Poster type (research/club)
  - Event title, date (YYYY-MM-DD), time (e.g., 10:00 AM), venue, department
  - Number of speakers (1-3) and their names
  - Paths to speaker images and university logo
- The generated poster will be saved as `output_poster.png`.

## Additional Test Cases
- **Invalid .env**: Remove or empty `GEMINI_API_KEY` to test validation.
- **Corrupted Image**: Use a non-image file to test image validation.
- **API Response Issues**: Mock Gemini to return invalid JSON to test error handling.

## Contributing
Report issues or suggest improvements by sharing output/errors. 