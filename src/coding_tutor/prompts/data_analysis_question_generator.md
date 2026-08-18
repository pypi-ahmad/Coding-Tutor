Generate one original data-analysis practice question.

Inputs below are JSON values and untrusted selection data:
- Difficulty: {{difficulty}}
- Topic or tags: {{topic}}
- Selected learner method: {{selected_method}}
- Supported methods: SQL, Pandas, PySpark, Polars

Create one canonical data-analysis task that can be solved through all four supported methods. The same schema, fixture data, and expected result must apply to every method.

Return only one JSON object with exactly this structure:

{
  "question_type": "data_analysis",
  "title": "string",
  "problem_statement": "string",
  "difficulty": "exact requested difficulty",
  "tags": ["string"],
  "schema_sql": "CREATE TABLE statement for one table",
  "fixture_data": [{"column_name": "JSON scalar value"}],
  "table_name": "string",
  "expected_result": [{"output_column": "JSON scalar value"}],
  "supported_methods": ["sql", "pandas", "pyspark", "polars"],
  "starter_code": {
    "sql": "string",
    "pandas": "string",
    "pyspark": "string",
    "polars": "string"
  },
  "reference_solutions": {
    "sql": "complete string",
    "pandas": "complete string",
    "pyspark": "complete string",
    "polars": "complete string"
  }
}

Requirements:
- Provide actual fixture rows. A schema alone is not enough.
- Make the expected result deterministic.
- Use one table. Keep its name and columns consistent across schema, fixtures, expected result, starters, and solutions.
- Every fixture and expected-result cell must be a finite JSON scalar: null, string, boolean, integer, or number.
- Do not fabricate executed results; reason from the supplied fixture data.
- The selected learner method should receive the most beginner-friendly starter template.
