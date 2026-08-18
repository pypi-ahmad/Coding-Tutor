"""Prompt templates for question generation. Version-controlled for traceability."""

PROMPT_VERSION = "v1"

ALGORITHM_SYSTEM_PROMPT = """You are an expert coding interviewer creating LeetCode-style algorithm problems.
Generate a complete, self-contained problem in JSON format.
The problem must be original, solvable in Python, and appropriate for the requested difficulty."""

ALGORITHM_USER_PROMPT = """Generate a {difficulty} difficulty algorithm problem about {topic}.

Return ONLY a valid JSON object with this exact structure:
{{
  "title": "Problem Title",
  "problem_statement": "Full problem description with clear input/output specification",
  "examples": [
    {{"input": "nums = [1,2,3]", "output": "6", "explanation": "Sum of all elements"}},
    {{"input": "nums = []", "output": "0", "explanation": "Empty array"}}
  ],
  "constraints": "1 <= nums.length <= 10^4\\n-10^9 <= nums[i] <= 10^9",
  "difficulty": "{difficulty}",
  "tags": ["Array", "Math"],
  "starter_code_python": "class Solution:\\n    def solve(self, nums: List[int]) -> int:\\n        pass",
  "test_cases": [
    {{"input": {{"nums": [1, 2, 3]}}, "expected_output": 6}},
    {{"input": {{"nums": []}}, "expected_output": 0}}
  ],
  "reference_solution_python": "class Solution:\\n    def solve(self, nums: List[int]) -> int:\\n        return sum(nums)"
}}"""

DATA_ANALYSIS_SYSTEM_PROMPT = """You are an expert data engineering interviewer creating data analysis problems.
Generate a complete problem solvable via SQL, Pandas, PySpark, and Polars.
Include schema, deterministic fixture data, and expected results."""

DATA_ANALYSIS_USER_PROMPT = """Generate a {difficulty} difficulty data analysis problem about {topic}.

Return ONLY a valid JSON object with this exact structure:
{{
  "title": "Problem Title",
  "problem_statement": "Analytical question to solve",
  "difficulty": "{difficulty}",
  "tags": ["Aggregation", "SQL"],
  "schema_sql": "CREATE TABLE employees (\\n  id INTEGER,\\n  name TEXT,\\n  department TEXT,\\n  salary DOUBLE\\n);",
  "fixture_data": [
    {{"id": 1, "name": "Alice", "department": "Engineering", "salary": 90000}},
    {{"id": 2, "name": "Bob", "department": "Marketing", "salary": 70000}},
    {{"id": 3, "name": "Carol", "department": "Engineering", "salary": 95000}}
  ],
  "table_name": "employees",
  "expected_result": [
    {{"department": "Engineering", "avg_salary": 92500.0}},
    {{"department": "Marketing", "avg_salary": 70000.0}}
  ],
  "supported_methods": ["sql", "pandas", "pyspark", "polars"],
  "starter_code": {{
    "sql": "SELECT\\n",
    "pandas": "import pandas as pd\\n\\ndef solution(df: pd.DataFrame) -> pd.DataFrame:\\n    return df\\n",
    "pyspark": "from pyspark.sql import DataFrame\\n\\ndef solution(spark, df: DataFrame) -> DataFrame:\\n    return df\\n",
    "polars": "import polars as pl\\n\\ndef solution(df: pl.DataFrame) -> pl.DataFrame:\\n    return df\\n"
  }},
  "reference_solutions": {{
    "sql": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department ORDER BY department;",
    "pandas": "def solution(df):\\n    return df.groupby('department')['salary'].mean().reset_index(name='avg_salary').sort_values('department')\\n",
    "polars": "def solution(df):\\n    return df.group_by('department').agg(pl.col('salary').mean().alias('avg_salary')).sort('department')\\n"
  }}
}}"""
