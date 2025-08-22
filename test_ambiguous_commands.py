# test_ambiguous_commands.py
# Demonstrates middleware behavior for ambiguous or unsupported commands.

from middleware.middleware import process_prompt
import json


def run_tests():
    prompts = [
        "make me a coffee",
        "change it",
        "do it",
        "please, order a pizza",
        "make the title blue"  # control: supported
    ]

    for p in prompts:
        print('\n--- Prompt:', p)
        out = process_prompt(p)
        print(json.dumps(out, indent=2))


if __name__ == '__main__':
    run_tests()
