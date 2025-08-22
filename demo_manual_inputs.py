# demo_manual_inputs.py
# Demonstrates what `interactive_prompt.py` would show by calling process_prompt with sample inputs.

from middleware.middleware import process_prompt
import json

prompts = [
    "make me a coffee",
    "change it",
    "make the title blue",
    "make the venue font size 30",
    "make the title bigger and change its color to red"
]

for p in prompts:
    print('\n--- Prompt:', p)
    out = process_prompt(p)
    print(json.dumps(out, indent=2))
