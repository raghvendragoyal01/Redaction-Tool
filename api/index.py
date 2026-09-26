import io
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response, JSONResponse

from src.anonymizer.anonymizer import Anonymizer
from src.detector.pipeline import PIIDetectionPipeline
from src.document.reader import DocxReader
from src.document.writer import DocxWriter

app = FastAPI(
    title="PII Redaction Engine API",
    description="REST API for detecting, redacting, and anonymizing PII in DOCX documents.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "PII Redaction & Anonymization Engine",
        "supported_entities": [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "ORGANIZATION",
            "ADDRESS", "SSN", "CREDIT_CARD", "DATE_OF_BIRTH", "IP_ADDRESS"
        ],
        "endpoints": {
            "POST /redact": "Upload a .docx file and receive the redacted .docx file",
            "POST /detect": "Upload a .docx file and receive detected PII entities in JSON",
        },
    }


@app.post("/redact")
async def redact_document(
    file: UploadFile = File(...),
    seed: int = Form(42),
):
    if not file.filename.endswith(".docx"):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file type. Please upload a .docx file."},
        )

    content = await file.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_input = Path(tmpdir) / "input.docx"
        tmp_output = Path(tmpdir) / "redacted.docx"
        tmp_input.write_bytes(content)

        # 1. Read Blocks
        reader = DocxReader(tmp_input)
        blocks = reader.extract_blocks()

        # 2. Detect
        pipeline = PIIDetectionPipeline()
        entities = pipeline.detect(blocks)

        # 3. Anonymize
        anonymizer = Anonymizer(seed=seed)
        replacements = anonymizer.anonymize_entities(entities)

        # 4. Write
        writer = DocxWriter(tmp_input)
        writer.save(
            output_path=tmp_output,
            entities=entities,
            replacements=replacements,
            mapping=anonymizer.get_raw_mapping(),
        )

        redacted_bytes = tmp_output.read_bytes()

    filename = f"REDACTED_{file.filename}"
    return Response(
        content=redacted_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/detect")
async def detect_pii(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid file type. Please upload a .docx file."},
        )

    content = await file.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_input = Path(tmpdir) / "input.docx"
        tmp_input.write_bytes(content)

        reader = DocxReader(tmp_input)
        blocks = reader.extract_blocks()

        pipeline = PIIDetectionPipeline()
        entities = pipeline.detect(blocks)

    return {
        "filename": file.filename,
        "total_blocks": len(blocks),
        "total_detections": len(entities),
        "entities": [
            {
                "entity_type": e.entity_type,
                "original_text": e.original_text,
                "block_index": e.block_index,
                "start": e.start,
                "end": e.end,
                "confidence": e.confidence,
                "source": e.source,
            }
            for e in entities
        ],
    }
