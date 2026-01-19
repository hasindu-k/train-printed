from docx import Document
import re

INPUT_DOCX = "tier-1-OCR-train.docx"
OUTPUT_TXT = "corpus-tier-1.txt"

def clean_line(line: str) -> str:
    """
    Remove numbering, page numbers, English explanations in brackets,
    and extra whitespace.
    """
    line = line.strip()

    # Skip empty lines
    if not line:
        return ""

    # Remove leading numbering like "1.", "Entries 1-100:", etc.
    line = re.sub(r"^(Entries\s*\d+[-–]\d+:|[0-9]+\.)\s*", "", line)

    # Remove trailing page numbers
    line = re.sub(r"\s+\d+$", "", line)

    # OPTIONAL: remove English explanations in brackets
    # Comment this out if you want to keep English text
    line = re.sub(r"\s*\(.*?\)", "", line)

    return line.strip()


def extract_word_list():
    doc = Document(INPUT_DOCX)
    extracted = []

    for para in doc.paragraphs:
        text = clean_line(para.text)

        # Heuristic: keep Sinhala-heavy lines
        if text and any('\u0D80' <= ch <= '\u0DFF' for ch in text):
            extracted.append(text)

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        for line in extracted:
            f.write(line + "\n")

    print(f"✅ Extracted {len(extracted)} lines into '{OUTPUT_TXT}'")


if __name__ == "__main__":
    extract_word_list()
