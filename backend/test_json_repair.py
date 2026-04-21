"""Test the JSON truncation repair logic"""
import json
import re

# Simulate truncated JSON exactly like the LLM output
raw_json = '''{
  "questions": [
    {
      "question": "What is titration?",
      "options": [
        "Measuring concentration",
        "Measuring pH level",
        "Measuring temperature",
        "Measuring volume"
      ],
      "correct_index": 0,
      "explanation": "Titration measures concentration"
    },
    {
      "question": "What is the endpoint?",
      "options": [
        "Color change point",
        "Starting point",
        "Midway point",
        "Random point"
      ],
      "correct_index": 0,
      "explanation": "Endpoint is color change"
    },
    {
      "question": "Truncated question here?",
      "options": [
        "To measure the concentration of a specific substance in a sa'''

print(f"Raw JSON length: {len(raw_json)}")
print(f"Closing braces found: {raw_json.count('}')}")

# Test Strategy 5: Progressive truncation
brace_positions = [i for i, c in enumerate(raw_json) if c == '}']
parsed_data = None

for pos in reversed(brace_positions):
    candidate = raw_json[:pos + 1].rstrip().rstrip(',')
    for closing in ['\n  ]\n}', ']}', '\n]\n}']:
        try:
            test = candidate + closing
            result = json.loads(test)
            if isinstance(result, dict) and "questions" in result and len(result["questions"]) >= 1:
                parsed_data = result
                print(f"\nSUCCESS: Recovered {len(result['questions'])} questions")
                break
        except json.JSONDecodeError:
            continue
    if parsed_data:
        break

if not parsed_data:
    print("\nStrategy 5 FAILED, trying Strategy 6...")
    individual_questions = []
    q_starts = [m.start() for m in re.finditer(r'\{\s*"question"', raw_json)]
    print(f"Found {len(q_starts)} question starts")
    
    for start in q_starts:
        for end_pos in range(start + 1, len(raw_json)):
            if raw_json[end_pos] == '}':
                candidate = raw_json[start:end_pos + 1]
                try:
                    q_obj = json.loads(candidate)
                    if "question" in q_obj and "options" in q_obj:
                        individual_questions.append(q_obj)
                        break
                except json.JSONDecodeError:
                    continue
    
    if individual_questions:
        parsed_data = {"questions": individual_questions}
        print(f"SUCCESS: Extracted {len(individual_questions)} individual questions")

if parsed_data:
    for q in parsed_data["questions"]:
        print(f"  Q: {q['question']}")
        print(f"     Options: {len(q['options'])}")
else:
    print("ALL STRATEGIES FAILED")
