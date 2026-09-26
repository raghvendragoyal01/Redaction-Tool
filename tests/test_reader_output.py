import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.document.reader import DocxReader

INPUT_FILE = (
    Path("input/RHP.docx")
    if Path("input/RHP.docx").exists()
    else Path("input/Red Herring Prospectus.docx")
)


def test_reader_output():
    reader = DocxReader(INPUT_FILE)
    blocks = reader.extract_blocks()

    assert len(blocks) > 0

    block_types = {}
    for block in blocks:
        block_types[block.block_type] = (
            block_types.get(block.block_type, 0) + 1
        )

    assert "paragraph" in block_types


if __name__ == "__main__":
    reader = DocxReader(INPUT_FILE)
    blocks = reader.extract_blocks()

    print("\n" + "=" * 80)
    print("STRUCTURED DOCUMENT ANALYSIS")
    print("=" * 80)
    print(f"Total blocks: {len(blocks):,}")

    block_types = {}
    for block in blocks:
        block_types[block.block_type] = (
            block_types.get(block.block_type, 0) + 1
        )

    print("\nBlock types:")
    for block_type, count in block_types.items():
        print(f"  {block_type:<15} {count:,}")

    print("\nFirst 20 blocks:")
    for block in blocks[:20]:
        print(
            f"[{block.index:04}] "
            f"{block.block_type:<12} "
            f"{block.location:<25} "
            f"{block.text[:100]}"
        )

