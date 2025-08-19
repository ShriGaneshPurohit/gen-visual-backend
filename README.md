▶️ Running the Project
1. Run the API server
uvicorn main:app --reload

2. Test with browser

Go to:

http://127.0.0.1:8000/docs
Click "Try it out" → enter data → Execute.

2️⃣ Single-Value Fields

For fields that take a single value, just enter a string path or JSON.

Example:

base_template_path → assets/template.png

mapping_file_path → assets/mapping.json

font_file_path → fonts/Roboto-Regular.ttf

venue_icon_file_path → icons/venue.png

calendar_icon_file_path → icons/calendar.png

3️⃣ JSON Inputs (poster text & font sizes)

Some fields expect JSON strings (because Swagger form inputs are text).

Example for poster_text_content:

{
  "campus_name": "Bangalore Central Campus",
  "department_name": "Department of Computer Science",
  "type_of_event": "Annual Tech Fest\nCode Genesis 2025",
  "about_event": "A hands-on workshop exploring AI.",
  "speaker 1": "Dr. Evelyn Reed",
  "designation 1": "Chief AI Scientist, Futura Corp",
  "date": "August 22, 2025",
  "time": "9:00 AM - 12:00 PM",
  "venue": "Central Block, 10th Floor",
  "footer": "School of Sciences\nDesigned by AI"
}


For custom_font_sizes:

{
  "type_of_event": 55,
  "campus_name": 45,
  "department_name": 50,
  "about_event": 35,
  "venue": 25,
  "date": 25,
  "time": 25
}


Paste the whole JSON as text in the form field.
FastAPI will parse it back into Python dict.

4️⃣ Multiple Inputs (Lists like logo_paths, face_image_paths)

Since forms don’t support arrays directly, we pass them as comma-separated strings.

The API code then splits them internally.

Example:
face_image_paths: assets/p1.jpeg

["logos/goal4.png", "logos/goal9.png"]
