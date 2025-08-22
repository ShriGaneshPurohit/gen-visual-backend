# run_user_prompts.py
# Programmatically run a single prompt through middleware and optionally save the poster via backend.

from middleware.middleware import process_prompt
from interactive_prompt import call_backend_and_save
import json

prompt = "make the title pink and make it bigger"
print('Prompt:', prompt)
out = process_prompt(prompt)
print(json.dumps(out, indent=2))
print('Calling backend to save poster...')
result = call_backend_and_save(out, prompt)
print('Result:', result)
