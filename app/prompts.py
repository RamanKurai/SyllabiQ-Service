"""
Prompt templates and helpers.
Store canonical prompt templates here so they are easy to test and version.
"""

QA_PROMPT_TEMPLATE = """You are an academic assistant constrained by the provided syllabus context.
Respond in an exam-appropriate format. Keep answers concise and within the requested marks.

Context:
{context}

Question:
{question}
"""

SUMMARIZE_PROMPT_TEMPLATE = """Summarize the following notes in a concise, exam-oriented manner.

Notes:
{notes}
"""

