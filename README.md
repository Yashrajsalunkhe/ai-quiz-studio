# AI Quiz Studio

AI Quiz Studio generates MCQ, true/false, and fill-in-the-blank practice quizzes from a topic, pasted notes, or a PDF. It validates the model output, supports quiz practice in the browser, and exports CSV and PDF files.

## Vercel architecture

The Vercel-ready application is deliberately split into a static browser UI and one Python serverless function:

| Path | Purpose |
| --- | --- |
| `public/index.html` | Static frontend served at the site root |
| `public/app.js` | Browser-side form, downloads, and practice mode |
| `api/index.py` | Flask serverless function at `/api/generate` |
| `requirements.txt` | Lightweight production dependencies used by Vercel |
| `app.py` | Original Gradio interface, retained for local-only use |
| `requirements-local.txt` | Extra dependencies needed to run the local Gradio interface |

The deployment does not include PyTorch, Transformers, FAISS, or a locally downloaded model. Vercel functions are ephemeral and are not appropriate for hosting an LLM; generation uses the Hugging Face Inference API instead. PDF retrieval uses lightweight keyword ranking, which keeps the function small and starts quickly.

## Deploy to Vercel

1. Push this directory to a Git repository and import it in Vercel, or run `vercel` from this directory.
2. In **Project Settings → Environment Variables**, add `HF_TOKEN` with a Hugging Face access token that can use the configured inference provider.
3. Deploy. Vercel reads `vercel.json`, serves `public/` at `/`, and runs `api/index.py` for `/api/*` requests.

Optional environment variables:

- `MODEL_ID` — Hugging Face chat model. Defaults to `Qwen/Qwen2.5-7B-Instruct`.
- `FALLBACK_MODEL` — only relevant when using the local Gradio application without `HF_TOKEN`.

After deployment, open `/api/health` to verify the serverless function. Never put `HF_TOKEN` in frontend files or commit it to the repository.

## Run locally

For the Vercel-style site, install production dependencies and use the Vercel CLI:

```bash
python -m pip install -r requirements.txt
vercel dev
```

Set `HF_TOKEN` in the Vercel project's local environment or in your shell before generating a quiz.

The original Gradio interface is also available locally:

```bash
python -m pip install -r requirements-local.txt
export HF_TOKEN="hf_xxx"  # PowerShell: $env:HF_TOKEN = "hf_xxx"
python app.py
```

Without `HF_TOKEN`, the local Gradio interface may download and run the fallback model, which needs substantial memory and is intentionally unavailable on Vercel.

## API

`POST /api/generate` accepts JSON such as:

```json
{
  "source": "Topic",
  "topic": "Cellular respiration",
  "question_count": 5,
  "difficulty": "Medium",
  "question_type": "MCQ",
  "language": "English",
  "bloom": "Understand"
}
```

For note-based quizzes, use `source: "Paste Text"` and include `text`. For PDF quizzes, use `source: "Upload PDF"` and include base64-encoded `pdf_base64`. Serverless request limits mean PDFs are limited to **3 MB**. The response contains `questions`, CSV text, and a base64-encoded PDF.
