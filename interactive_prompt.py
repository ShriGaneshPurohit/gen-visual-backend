# interactive_prompt.py
# Run this to type prompts manually and see middleware output immediately.

from middleware.middleware import process_prompt
import json
import os
import requests
from datetime import datetime


def safe_filename_from_prompt(prompt: str) -> str:
    # Create a compact, safe filename: short slug + 8-char hex of prompt to avoid collisions
    import re, hashlib
    # keep letters, numbers and spaces
    slug = re.sub(r'[^A-Za-z0-9 ]+', '', prompt)
    slug = '_'.join(slug.split())
    if len(slug) > 40:
        slug = slug[:40]
    digest = hashlib.md5(prompt.encode('utf-8')).hexdigest()[:8]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"poster_manual_{slug}_{digest}_{ts}.png"
    # Ensure filename isn't empty
    if not slug:
        filename = f"poster_manual_{digest}_{ts}.png"
    return filename


def call_backend_and_save(out: dict, prompt: str) -> str:
    # Prepare form data similar to test scripts
    poster_text = out.get('poster_text_content', {})
    font_sizes = out.get('custom_font_sizes', {}) or {}
    colors = out.get('custom_colors', {}) or {}

    # Fallback: if user asked for 'bigger' and no numeric override, bump the title
    if 'bigger' in prompt.lower() and 'type_of_event' not in font_sizes:
        font_sizes['type_of_event'] = 65

    data = {
        'base_template_path': 'assets/original_poster.png',
        'mapping_file_path': 'assets/mapping.json',
        'font_file_path': 'fonts/OpenSans-VariableFont_wdth,wght.ttf',
        'logo_paths': 'logos/goal4.png,logos/goal9.png',
        'venue_icon_file_path': 'icons/venue.png',
        'calendar_icon_file_path': 'icons/calendar.png',
        'poster_text_content': json.dumps(poster_text),
        'custom_font_sizes': json.dumps(font_sizes),
        'face_image_paths': 'assets/p1.jpeg'
    }
    if colors:
        data['custom_colors'] = json.dumps(colors)

    url = 'http://127.0.0.1:8000/full-process'
    try:
        resp = requests.post(url, data=data, files={}, timeout=20)
    except Exception as e:
        return f"Request failed: {e}"

    if resp.status_code == 200:
        try:
            os.makedirs('outputs', exist_ok=True)
            fname = safe_filename_from_prompt(prompt)
            path = os.path.join('outputs', fname)
            with open(path, 'wb') as f:
                f.write(resp.content)
            # Also save metadata (poster_text_content, font sizes, colors, original prompt)
            metadata = {
                'prompt': prompt,
                'poster_text_content': poster_text,
                'custom_font_sizes': font_sizes,
                'custom_colors': colors,
                'saved_at': datetime.now().isoformat()
            }
            meta_path = os.path.splitext(path)[0] + '.json'
            try:
                with open(meta_path, 'w', encoding='utf-8') as mf:
                    json.dump(metadata, mf, indent=2)
            except OSError:
                # best-effort: continue
                pass
            return path
        except OSError as oe:
            return f"Failed to save file: {oe}"
    else:
        return f"Backend error {resp.status_code}: {resp.text}"


def main():
    print("Interactive middleware tester. Type a prompt and press Enter. Empty input quits.")
    while True:
        try:
            p = input('\nEnter prompt: ').strip()
        except EOFError:
            break
        if not p:
            print('Exiting.')
            break
        out = process_prompt(p)
        print(json.dumps(out, indent=2))

        # Ask user if they want to save a poster for this prompt
        try:
            choice = input('\nCall backend and save poster for this prompt? (y/N): ').strip().lower()
        except EOFError:
            choice = 'n'
        if choice == 'y':
            print('Calling backend...')
            result = call_backend_and_save(out, p)
            print('Result:', result)


if __name__ == '__main__':
    main()
