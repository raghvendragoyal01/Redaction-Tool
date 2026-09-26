# 🛡️ PII Redaction & Anonymization Tool

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise PII redaction and anonymization pipeline designed for Indian financial filings (Draft Red Herring Prospectus / RHP `.docx` files). 

The tool detects sensitive PII, replaces it with realistic synthetic alternatives (`Faker` with `en_IN` locale), and **strictly preserves original DOCX styling**, fonts, bold/italic runs, tables, headers, and footers.

---

## 🚀 Key Highlights

- **9 PII Entity Types Supported:** Full Names (`PERSON`), Emails (`EMAIL_ADDRESS`), Phone Numbers (`PHONE_NUMBER`), Companies (`ORGANIZATION`), Addresses (`ADDRESS`), SSNs/National IDs (`SSN`), Credit Cards (`CREDIT_CARD`), Dates of Birth (`DATE_OF_BIRTH`), and IP Addresses (`IP_ADDRESS`).
- **Hybrid Detection:** Ensemble of Context Rules, High-Precision Regex, Microsoft Presidio, and Spacy NER.
- **Run-Level Style Preservation:** Modifies text slices in DOCX XML runs without altering paragraph styles or table formatting.
- **Deterministic Anonymization:** Entity caching ensures recurring names/entities are replaced consistently across the document.
- **Zero Leakage:** Global multi-pass substitution ensures no unredacted source PII remains in the output.

---

## 📂 Project Structure

```
├── evaluation/
│   ├── evaluation_report.md         # Comprehensive evaluation metrics & report
│   ├── detection_summary.json        # Machine-readable detection summary
│   ├── detection_audit.csv          # Full granular detection audit log
│   └── unique_entities.csv          # Unique detected entity counts
├── input/
│   └── RHP.docx                     # Input prospectus document
├── output/
│   └── Red_Herring_Prospectus_REDACTED.docx  # Redacted output document
├── scripts/
│   ├── run_anonymization.py         # Main anonymization runner
│   ├── validate_redaction.py        # Leakage & document structure validator
│   ├── evaluate.py                  # Evaluation benchmark runner
│   └── inspect_pipeline.py          # Detailed audit log generator
├── src/
│   ├── anonymizer/                  # Synthetic data generator & entity caching
│   ├── detector/                    # Hybrid detection engine & validators
│   ├── document/                    # DOCX reader & style-preserving writer
│   ├── evaluation/                  # Metric computation & reporting
│   └── main.py                      # CLI entry point
└── tests/                           # Unit tests
```

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/raghvendragoyal01/Redaction-Tool.git
   cd Redaction-Tool
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   
   # Linux / macOS
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

---

## 💻 Usage

### 1. Run Anonymization Pipeline
```bash
# Using CLI
python -m src.main --input input/RHP.docx --output output/Red_Herring_Prospectus_REDACTED.docx --seed 42

# Or via script
python scripts/run_anonymization.py
```

### 2. Validate Redaction & Document Structure
Verifies that 0% source PII leaked into the output and that paragraph/table counts are 100% preserved:
```bash
python scripts/validate_redaction.py
```

### 3. Run Evaluation Benchmark
Runs the evaluation against ground-truth benchmarks and regenerates the metric report:
```bash
python scripts/evaluate.py
```

### 4. Run Unit Tests
```bash
pytest -v
```

---

## 📊 Evaluation & Metrics

Detailed quantitative metrics (Precision, Recall, F1 scores across all 9 categories), false positive/negative analysis, and structural integrity validations are documented in:

👉 **[Evaluation Report (evaluation/evaluation_report.md)](evaluation/evaluation_report.md)**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
