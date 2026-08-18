Generate one new algorithm practice question.

Input:
- Difficulty: {{difficulty}}
- Topic or tags: {{topic}}
- Preferred language: Python
- Learner level: {{difficulty}}

Create an original LeetCode-style Python problem. Do not copy a known problem statement word-for-word.

Return this JSON structure:

{
  "status": "ok",
  "question_type": "algorithm",
  "title": "string",
  "difficulty": "Beginner | Easy | Medium | Hard | Very Hard",
  "tags": ["string"],
  "problem_statement": "string",
  "input_description": "string",
  "output_description": "string",
  "constraints": ["string"],
  "examples": [
    {
      "input": "string",
      "output": "string",
      "explanation": "string"
    }
  ],
  "starter_code": "string",
  "reference_solutions": [
    {
      "name": "string",
      "code": "string",
      "explanation": "string",
      "time_complexity": "string",
      "space_complexity": "string"
    }
  ],
  "review_rubric": [
    "string"
  ],
  "notes_for_tutor": "string"
}

Requirements:
- Include at least two examples.
- Include clear constraints.
- Provide at least two meaningfully different solutions when appropriate.
- Ensure the starter code and reference code are Python.
- The problem must match the selected difficulty.
- Do not claim that code was executed or tested.