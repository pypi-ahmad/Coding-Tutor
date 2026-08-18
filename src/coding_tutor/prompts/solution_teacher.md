Teach the learner how to solve the following question.

Question:
<question>
{{question}}
</question>

Question type:
<question_type>
{{question_type}}
</question_type>

Requested method:
<requested_method>
{{requested_method}}
</requested_method>

Exercise data, if applicable:
<exercise_data>
{{exercise_data}}
</exercise_data>

Return this JSON structure:

{
  "status": "ok | insufficient_information",
  "concepts": [
    {
      "name": "string",
      "explanation": "string"
    }
  ],
  "solutions": [
    {
      "method": "python | sql | pandas | pyspark | polars",
      "name": "string",
      "when_to_use": "string",
      "code": "string",
      "step_by_step_explanation": ["string"],
      "time_complexity": "string | null",
      "space_complexity": "string | null",
      "limitations": ["string"]
    }
  ],
  "common_mistakes": ["string"],
  "practice_tip": "string"
}

Rules:
- Explain in a teacher-friendly manner for the question difficulty.
- Provide multiple valid approaches when meaningful.
- For an algorithm question, provide Python solutions only unless the question explicitly requests another language.
- For a data-analysis question, provide SQL, Pandas, PySpark, and Polars solutions when the provided schema and fixture data support them.
- Use well-commented code.
- Do not claim code was executed.
- Do not reveal hidden reasoning; provide concise educational explanations.