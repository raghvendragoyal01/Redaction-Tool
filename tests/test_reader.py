from pathlib import Path

from src.document.reader import DocxReader


INPUT_FILE = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)


def test_docx_file_exists():
    assert INPUT_FILE.exists()


def test_reader_extracts_text():
    reader = DocxReader(INPUT_FILE)

    text = reader.extract_text()

    assert text
    assert len(text) > 1000

def test_reader_extracts_structured_blocks():
    reader = DocxReader(INPUT_FILE)

    blocks = reader.extract_blocks()

    assert blocks
    assert all(block.text for block in blocks)
    assert all(block.block_type for block in blocks)
    assert all(block.location for block in blocks)