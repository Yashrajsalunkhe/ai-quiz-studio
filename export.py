"""CSV and PDF export."""
import csv
import io
import tempfile
from fpdf import FPDF


def _safe(s):  # core PDF fonts are latin-1 only
    return str(s).encode("latin-1", "replace").decode("latin-1")


def to_csv_text(qs):
    output = io.StringIO(newline="")
    w = csv.writer(output)
    w.writerow(["#", "Question", "Options", "Answer", "Explanation"])
    for i, q in enumerate(qs, 1):
        w.writerow([i, q["question"], " | ".join(q["options"]), q["options"][q["answer_index"]], q["explanation"]])
    return output.getvalue()


def to_csv(qs):
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline="", encoding="utf-8")
    f.write(to_csv_text(qs))
    f.close()
    return f.name


def to_pdf_bytes(qs):
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Quiz", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for i, q in enumerate(qs, 1):
        pdf.multi_cell(0, 7, _safe(f"Q{i}. {q['question']}"), new_x="LMARGIN", new_y="NEXT")
        for j, o in enumerate(q["options"]):
            pdf.multi_cell(0, 6, _safe(f"   {chr(65 + j)}. {o}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Answer Key", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=11)
    for i, q in enumerate(qs, 1):
        pdf.multi_cell(0, 6, _safe(f"{i}. {chr(65 + q['answer_index'])} - {q['explanation']}"),
                       new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def to_pdf(qs):
    path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    with open(path, "wb") as pdf_file:
        pdf_file.write(to_pdf_bytes(qs))
    return path
