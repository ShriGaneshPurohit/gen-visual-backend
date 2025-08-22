# apply_edit_to_last.py
# Loads the most recent poster metadata from outputs/, applies a new prompt as an edit (middleware parse),
# merges the changes onto the saved poster metadata, sends merged payload to backend, and saves a new poster.

import os
import glob
import json
import sys
from middleware.middleware import process_prompt
from interactive_prompt import call_backend_and_save


def list_recent_metadata(limit: int = 6):
    files = glob.glob('outputs/*.json')
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:limit]


def choose_metadata_interactive():
    files = list_recent_metadata(10)
    if not files:
        return None
    print('Recent saved posters:')
    for i, f in enumerate(files):
        print(f'[{i}] {os.path.basename(f)}')
    choice = input('Choose index to edit (Enter for 0/latest): ').strip()
    if choice == '':
        return files[0]
    try:
        idx = int(choice)
        if 0 <= idx < len(files):
            return files[idx]
    except Exception:
        pass
    print('Invalid choice, using latest.')
    return files[0]


def merge_and_apply(new_prompt: str, meta_path: str = None):
    if meta_path is None:
        meta_path = find_latest_meta()
    if not meta_path:
        print('No existing poster metadata found in outputs/. Save a poster first.')
        return
    with open(meta_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    print('Loaded metadata for poster saved at:', meta_path)
    print('Existing prompt:', existing.get('prompt'))

    # Parse the new prompt
    delta = process_prompt(new_prompt)
    print('Middleware delta:', json.dumps(delta, indent=2))

    # Merge: overlay non-empty values from delta onto existing metadata
    merged_text = existing.get('poster_text_content', {}).copy()
    for k, v in (delta.get('poster_text_content') or {}).items():
        if v:
            merged_text[k] = v

    merged_font = existing.get('custom_font_sizes', {}).copy()
    merged_font.update(delta.get('custom_font_sizes') or {})

    merged_colors = existing.get('custom_colors', {}).copy() if existing.get('custom_colors') else {}
    merged_colors.update(delta.get('custom_colors') or {})

    # Prepare an artificial prompt note
    merged_prompt = existing.get('prompt', '') + ' | EDIT: ' + new_prompt

    print('Posting merged payload to backend...')
    # call backend helper which returns saved file path or error
    result = call_backend_and_save({'poster_text_content': merged_text, 'custom_font_sizes': merged_font, 'custom_colors': merged_colors}, merged_prompt)
    print('Result:', result)

    # Try to open the saved file if result was a path
    try:
        if isinstance(result, str) and os.path.exists(result):
            try:
                os.startfile(result)
                print('Opened saved poster:', result)
            except Exception:
                print('Saved poster at:', result)
    except Exception:
        pass


def find_latest_meta():
    files = glob.glob('outputs/*.json')
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return latest


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        # first arg is the edit prompt
        merge_and_apply(sys.argv[1])
    else:
        meta = choose_metadata_interactive()
        if not meta:
            print('No saved posters found in outputs/. Save one first with interactive_prompt.py')
            sys.exit(1)
        edit = input('Enter the edit you want to make (e.g. "change the title color to red"): ').strip()
        if not edit:
            print('No edit provided, exiting.')
            sys.exit(0)
        merge_and_apply(edit, meta)
