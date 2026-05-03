"""Intentional anti-pattern for drift discussion."""

from openai import OpenAI


def draft_reply_directly(subject: str, body: str) -> str:
    client = OpenAI()
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"Draft a support reply for subject={subject!r} body={body!r}",
    )
    return response.output_text
