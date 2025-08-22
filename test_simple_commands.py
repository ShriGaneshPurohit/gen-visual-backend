# test_simple_commands.py
# Test case for clear and simple commands to the middleware and backend
from middleware.middleware import process_prompt
import json
import requests
import os


def sanitize_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in s).strip().replace(' ', '_')


def test_simple_commands():
    commands = [
        "make the title blue",
        "change the date to 25th July 2025",
        "make the venue font size 30"
    ]

    url = "http://127.0.0.1:8000/full-process"
    os.makedirs('outputs', exist_ok=True)

    for i, cmd in enumerate(commands, start=1):
        print(f"\n[Testing command: '{cmd}']")
        json_output = process_prompt(cmd)
        print(json.dumps(json_output, indent=2))

        # Prepare form-data for backend
        data = {
            'base_template_path': 'assets/original_poster.png',
            'mapping_file_path': 'assets/mapping.json',
            'font_file_path': 'fonts/OpenSans-VariableFont_wdth,wght.ttf',
            'logo_paths': 'logos/goal4.png,logos/goal9.png',
            'venue_icon_file_path': 'icons/venue.png',
            'calendar_icon_file_path': 'icons/calendar.png',
            'poster_text_content': json.dumps(json_output.get('poster_text_content', {})),
            'custom_font_sizes': json.dumps(json_output.get('custom_font_sizes', {})),
            'face_image_paths': 'assets/p1.jpeg'
        }

        if 'custom_colors' in json_output:
            data['custom_colors'] = json.dumps(json_output['custom_colors'])

        try:
            resp = requests.post(url, data=data, files={})
        except Exception as e:
            print(f"Request failed: {e}")
            continue

        if resp.status_code == 200:
            safe = sanitize_filename(cmd)
            out_path = os.path.join('outputs', f'poster_command_{i}_{safe}.png')
            with open(out_path, 'wb') as f:
                f.write(resp.content)
            print(f"Poster saved to {out_path}")
        else:
            print(f"Backend error: {resp.status_code}")
            print(resp.text)


if __name__ == "__main__":
    test_simple_commands()

    # --- Combined run: apply all three commands in one poster ---
    print("\n[Combined test: applying all commands in one request]")
    combined_commands = [
        "make the title blue",
        "change the date to 25th July 2025",
        "make the venue font size 30"
    ]

    combined_text = {}
    combined_font_sizes = {}
    combined_colors = {}

    for cmd in combined_commands:
        out = process_prompt(cmd)
        # merge poster_text_content: non-empty values override
        for k, v in out.get('poster_text_content', {}).items():
            if v:
                combined_text[k] = v
        # merge font sizes
        for k, v in out.get('custom_font_sizes', {}).items():
            try:
                combined_font_sizes[k] = int(v)
            except Exception:
                pass
        # merge colors
        for k, v in out.get('custom_colors', {}).items() if 'custom_colors' in out else []:
            if v:
                combined_colors[k] = v

    # Ensure defaults for text keys exist by calling with an empty prompt fallback
    base = process_prompt("")
    base_text = base.get('poster_text_content', {})
    for k, v in base_text.items():
        if k not in combined_text:
            combined_text[k] = v

    # Prepare form-data and POST once
    data = {
        'base_template_path': 'assets/original_poster.png',
        'mapping_file_path': 'assets/mapping.json',
        'font_file_path': 'fonts/OpenSans-VariableFont_wdth,wght.ttf',
        'logo_paths': 'logos/goal4.png,logos/goal9.png',
        'venue_icon_file_path': 'icons/venue.png',
        'calendar_icon_file_path': 'icons/calendar.png',
        'poster_text_content': json.dumps(combined_text),
        'custom_font_sizes': json.dumps(combined_font_sizes),
        'face_image_paths': 'assets/p1.jpeg'
    }
    if combined_colors:
        data['custom_colors'] = json.dumps(combined_colors)

    url = "http://127.0.0.1:8000/full-process"
    try:
        resp = requests.post(url, data=data, files={})
        if resp.status_code == 200:
            out_path = os.path.join('outputs', 'poster_combined_commands.png')
            with open(out_path, 'wb') as f:
                f.write(resp.content)
            print(f"Combined poster saved to {out_path}")
        else:
            print(f"Backend error on combined post: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Combined request failed: {e}")
