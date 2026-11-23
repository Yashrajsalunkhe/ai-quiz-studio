"""Vercel serverless API for AI Quiz Studio.

The module-level ``app`` object is the Vercel Python Function entry point.
"""
import base64
import binascii
import io

from flask import Flask, jsonify, request

from export import to_csv_text, to_pdf_bytes
from llm import MODEL, generate_quiz
from prompts import user_prompt
from rag import extract_pdf_text, retrieve


app = Flask(__name__)

MAX_PDF_BYTES = 3 * 1024 * 1024
VALID_SOURCES = {"Topic", "Paste Text", "Upload PDF"}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
VALID_QUESTION_TYPES = {"MCQ", "True/False", "Fill-in-the-blank"}
VALID_LANGUAGES = {"English", "Hindi"}
VALID_BLOOM_LEVELS = {"Any", "Remember", "Understand", "Apply", "Analyze", "Evaluate"}


def _input_data(payload):
    source = payload.get("source", "Topic")
    topic = str(payload.get("topic", "")).strip()
    text = str(payload.get("text", ""))
    context = ""

    if source == "Topic":
        if not topic:
            raise ValueError("Please enter a topic.")
    elif source == "Paste Text":
        if len(text.split()) < 30:
            raise ValueError("Please provide at least 30 words of text.")
        context = retrieve(text, topic)
    elif source == "Upload PDF":
        encoded_pdf = payload.get("pdf_base64")
        if not encoded_pdf:
            raise ValueError("Provide the PDF as the pdf_base64 field.")
        try:
            pdf_bytes = base64.b64decode(encoded_pdf, validate=True)
        except (binascii.Error, ValueError, TypeError) as error:
            raise ValueError("pdf_base64 must contain valid base64 data.") from error
        if len(pdf_bytes) > MAX_PDF_BYTES:
            raise ValueError("PDF larger than 3 MB.")
        context = retrieve(extract_pdf_text(io.BytesIO(pdf_bytes)), topic)
    else:
        raise ValueError("source must be Topic, Paste Text, or Upload PDF.")

    return topic, context


@app.get("/health")
@app.get("/api/health")
def health():
    return jsonify({"name": "AI Quiz Studio API", "status": "ok"})


@app.post("/generate")
@app.post("/api/generate")
def generate():
    payload = request.get_json(silent=True) or {}
    try:
        if not isinstance(payload, dict):
            raise ValueError("The request body must be a JSON object.")
        if payload.get("source", "Topic") not in VALID_SOURCES:
            raise ValueError("source must be Topic, Paste Text, or Upload PDF.")
        topic, context = _input_data(payload)
        question_count = int(payload.get("question_count", 5))
        if not 1 <= question_count <= 20:
            raise ValueError("question_count must be between 1 and 20.")
        difficulty = payload.get("difficulty", "Medium")
        question_type = payload.get("question_type", "MCQ")
        language = payload.get("language", "English")
        bloom = payload.get("bloom", "Any")
        if difficulty not in VALID_DIFFICULTIES:
            raise ValueError("difficulty must be Easy, Medium, or Hard.")
        if question_type not in VALID_QUESTION_TYPES:
            raise ValueError("question_type must be MCQ, True/False, or Fill-in-the-blank.")
        if language not in VALID_LANGUAGES:
            raise ValueError("language must be English or Hindi.")
        if bloom not in VALID_BLOOM_LEVELS:
            raise ValueError("Invalid Bloom's taxonomy level.")
        quiz = generate_quiz(
            user_prompt(topic, context, question_count, difficulty, question_type, language, bloom),
            question_count,
            qtype=question_type,
        )
        questions = [question.model_dump() for question in quiz.questions]
        return jsonify({
            "model": MODEL,
            "questions": questions,
            "csv": to_csv_text(questions),
            "pdf_base64": base64.b64encode(to_pdf_bytes(questions)).decode("ascii"),
        })
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True)
