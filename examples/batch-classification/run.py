import json
import instructor
import asyncio

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator
from typing import List
from enum import Enum


client = instructor.patch(AsyncOpenAI(), mode=instructor.Mode.TOOLS)
sem = asyncio.Semaphore(5)


class QuestionType(Enum):
    CONTENT_OWNERSHIP = "CONTENT_OWNERSHIP"
    CONTACT = "CONTACT"
    TIMELINE_QUERY = "TIMELINE_QUERY"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    COMPARE_CONTRAST = "COMPARE_CONTRAST"
    MEETING_TRANSCRIPTS = "MEETING_TRANSCRIPTS"
    EMAIL = "EMAIL"
    PHOTOS = "PHOTOS"
    HOW_DOES_THIS_WORK = "HOW_DOES_THIS_WORK"
    NEEDLE_IN_HAYSTACK = "NEEDLE_IN_HAYSTACK"
    SUMMARY = "SUMMARY"


ALLOWED_TYPES = [t.value for t in QuestionType]


# You can add more instructions and examples in the description
# or you can put it in the prompt in `messages=[...]`
class QuestionClassification(BaseModel):
    """
    Predict the type of question that is being asked.

    Here are some tips on how to predict the question type:

    CONTENT_OWNERSHIP: "Who owns the a certain piece of content?"
    CONTACT: Searches for some contact information.
    TIMELINE_QUERY: "When did something happen?
    DOCUMENT_SEARCH: "Find me a document"
    COMPARE_CONTRAST: "Compare and contrast two things"
    MEETING_TRANSCRIPTS: "Find me a transcript of a meeting, or a soemthing said in a meeting"
    EMAIL: "Find me an email, search for an email"
    PHOTOS: "Find me a photo, search for a photo"
    HOW_DOES_THIS_WORK: "How does this question /answer product work?"
    NEEDLE_IN_HAYSTACK: "Find me something specific in a large amount of data"
    SUMMARY: "Summarize a large amount of data"
    """

    # If you want only one classification, just change it to
    #   `classification: QuestionType` rather than `classifications: List[QuestionType]``
    classification: List[QuestionType] = Field(
        description=f"An accuracy and correct prediction predicted class of question. Only allowed types: {ALLOWED_TYPES}, should be used",
    )

    @field_validator("classification", mode="before")
    def validate_classification(cls, v):
        # sometimes the API returns a single value, just make sure it's a list
        if not isinstance(v, list):
            v = [v]
        return v


# Modify the classify function
async def classify(data: str) -> QuestionClassification:
    async with sem:  # some simple rate limiting
        return data, await client.chat.completions.create(
            model="gpt-4",
            response_model=QuestionClassification,
            max_retries=2,
            messages=[
                {
                    "role": "user",
                    "content": f"Classify the following question: {data}",
                },
            ],
        )


async def main(
    questions: List[str], *, path_to_jsonl: str = None
) -> List[QuestionClassification]:
    tasks = [classify(question) for question in questions]
    for task in asyncio.as_completed(tasks):
        question, label = await task
        resp = {
            "question": question,
            "classification": [c.value for c in label.classification],
        }
        print(resp)
        if path_to_jsonl:
            with open(path_to_jsonl, "a") as f:
                json_dump = json.dumps(resp)
                f.write(json_dump + "\n")


if __name__ == "__main__":
    import asyncio

    path = "./data.jsonl"
    # Obviously we might want to big query or
    # load this from a file or something???
    questions = [
        "What was that ai app that i saw on the news the other day?",
        "Can you find the trainline booking email?",
        "What was the book I saw on amazon yesturday?",
        "Can you speak german?",
        "Do you have access to the meeting transcripts?",
        "what are the recent sites I visited?",
        "what did I do on Monday?",
        "Tell me about todays meeting and how it relates to the email on Monday",
    ]

    asyncio.run(main(questions, path_to_jsonl=path))
