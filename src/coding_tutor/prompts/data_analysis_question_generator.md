Generate one original data-analysis practice question.

Input:
- Difficulty: {{difficulty}}
- Topic or tags: {{topic}}
- Selected learner method: {{selected_method}}
- Supported methods: SQL, Pandas, PySpark, Polars

Create one canonical data-analysis task that can be solved through all four supported methods. The same schema, fixture data, and expected result must apply to every method.

Return this JSON structure:

{
  "status": "ok",
  "question_type": "data_analysis",
  "title": "string",
  "difficulty": "Beginner | Easy | Medium | Hard | Very Hard",
  "tags": ["string"],
  "problem_statement": "string",
  "business_context": "string",
  "supported_methods": ["sql", "pandas", "pyspark", "polars"],
  "schema": [
    {
      "table_name": "string",
      "columns": [
        {
          "name": "string",
          "type": "string",
          "description": "string"
        }
      ]
    }
  ],
  "fixture_data": {
    "table_name": [
      {
        "column_name": "value"
      }
    ]
  },
  "expected_result": {
    "columns": ["string"],
    "rows": [
      {
        "column_name": "value"
      }
    ],
    "ordering_rule": "string"
  },
  "examples": [
    {
      "description": "string",
      "expected_output": "string"
    }
  ],
  "starter_templates": {
    "sql": "string",
    "pandas": "string",
    "pyspark": "string",
    "polars": "string"
  },
  "reference_solutions": {
    "sql": {
      "code": "string",
      "explanation": "string"
    },
    "pandas": {
      "code": "string",
      "explanation": "string"
    },
    "pyspark": {
      "code": "string",
      "explanation": "string"
    },
    "polars": {
      "code": "string",
      "explanation": "string"
    }
  },
  "review_rubric": [
    "string"
  ]
}

Requirements:
- Provide actual fixture rows. A schema alone is not enough.
- Make the expected result deterministic.
- Keep table and column names consistent across schema, fixture data, expected result, and all solutions.
- Do not fabricate executed results; reason from the supplied fixture data.
- The selected learner method should receive the most beginner-friendly starter template.