Convert the supplied dataset record into a normalized Coding Tutor question.

The record may be incomplete. Do not invent missing fixture data, expected results, tests, licenses, source identifiers, or reference solutions.

Dataset metadata:
<dataset_metadata>
{{dataset_metadata}}
</dataset_metadata>

Raw dataset record:
<raw_record>
{{raw_record}}
</raw_record>

Return this JSON structure:

{
  "status": "ready | incomplete | unsupported",
  "reason": "string",
  "question_type": "algorithm | data_analysis | null",
  "title": "string | null",
  "difficulty": "string | null",
  "tags": ["string"],
  "problem_statement": "string | null",
  "supported_methods": ["string"],
  "starter_code_or_templates": {},
  "reference_solutions": {},
  "test_cases": [],
  "schema": [],
  "fixture_data": {},
  "expected_result": {},
  "source_provenance": {
    "source_dataset": "string | null",
    "source_record_id": "string | null",
    "license": "string | null",
    "attribution": "string | null"
  },
  "missing_requirements": ["string"]
}

Classification rules:
- Use `algorithm` for programming tasks that can be answered through Python code.
- Use `data_analysis` only when the record has, or is supplied with, a usable schema, fixture data, and expected result.
- A SQL query plus only `CREATE TABLE` statements is incomplete for a multi-method data-analysis task because it lacks actual fixture data.
- Do not classify based only on folder name.
- Preserve provenance exactly when available.