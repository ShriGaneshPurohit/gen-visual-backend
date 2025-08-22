# test.py
# This script simulates the frontend by sending a prompt to the middleware and prints the JSON output for the backend.
from middleware.middleware import process_prompt


import requests
import json
import os

def main():
    prompt = "Generate a poster for the Annual Innovation Summit: Future Forward 2025 at Mumbai North Campus. Department of Information Technology. Event type: Annual Innovation Summit. About: A hands-on workshop exploring the latest trends in Artificial Intelligence, from cutting-edge research to real-world deployment. Speaker: Prof. Arjun Mehta. Designation: Lead Data Scientist, InnovateX Labs. Date: September 10, 2025. Time: 2:00 PM - 7:00 PM. Venue: Innovation Hall, 5th Floor, Skyline Building. Footer: School of Engineering Designed by AI."
    # "Generate a poster for the Annual Innovation Summit: Future Forward 2025 at Mumbai North Campus. Department of Information Technology. Event type: Annual Innovation Summit. About: A hands-on workshop exploring the latest trends in Artificial Intelligence, from cutting-edge research to real-world deployment. Speaker: Prof. Arjun Mehta. Designation: Lead Data Scientist, InnovateX Labs. Date: September 10, 2025. Time: 2:00 PM - 7:00 PM. Venue: Innovation Hall, 5th Floor, Skyline Building. Footer: School of Engineering Designed by AI"
    json_output = process_prompt(prompt)
    print("[Middleware Output]")
    print(json.dumps(json_output, indent=2))

    # Backend expects form-data, so set up the required files and fields
    url = "http://127.0.0.1:8000/full-process"
    files = {}
    data = {
        'base_template_path': 'assets/original_poster.png',
        'mapping_file_path': 'assets/mapping.json',
        'font_file_path': 'fonts/OpenSans-VariableFont_wdth,wght.ttf',
        'logo_paths': 'logos/goal4.png,logos/goal9.png',
        'venue_icon_file_path': 'icons/venue.png',
        'calendar_icon_file_path': 'icons/calendar.png',
        'poster_text_content': json.dumps(json_output['poster_text_content']),
        'custom_font_sizes': json.dumps(json_output['custom_font_sizes']),
        'face_image_paths': 'assets/p1.jpeg'
    }
    print("\n[Sending request to backend...]")
    response = requests.post(url, data=data, files=files)
    if response.status_code == 200:
        output_path = os.path.join('outputs', 'final_poster_from_backend.png')
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Poster image saved to {output_path}")
    else:
        print(f"Backend error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
