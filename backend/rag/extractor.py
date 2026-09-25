import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
from .config import GDRIVE_RESOURCES_URL

logger = logging.getLogger("rag.extractor")


def chunk_text(text: str, source_tag: str, min_chunk_len: int = 60) -> List[str]:
    """Splits text content into semantic paragraph-based chunks with source citations."""
    raw_paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []

    for para in raw_paragraphs:
        cleaned = para.strip()
        if not cleaned:
            continue
        # Section headers or tabular rows create immediate chunk boundaries
        if (
            cleaned.startswith("#")
            or cleaned.startswith("|")
            or cleaned.startswith("Table")
            or cleaned.startswith("Figure")
        ):
            if current_chunk:
                combined = "\n\n".join(current_chunk)
                chunks.append(f"{source_tag}\n{combined}")
                current_chunk = []
            current_chunk.append(cleaned)
        else:
            current_chunk.append(cleaned)
            combined = "\n\n".join(current_chunk)
            if len(combined) >= min_chunk_len:
                chunks.append(f"{source_tag}\n{combined}")
                current_chunk = []

    if current_chunk:
        combined = "\n\n".join(current_chunk)
        chunks.append(f"{source_tag}\n{combined}")

    return [c for c in chunks if len(c.strip()) > 35]


def extract_file_chunks(file_path: Path) -> List[Tuple[str, Dict[str, Any]]]:
    """Extracts text and splits into chunks across PDF, TXT, MD, and CSV files."""
    results: List[Tuple[str, Dict[str, Any]]] = []
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                for page_idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    if not page_text.strip():
                        continue
                    source_tag = f"[Research Resource: {file_path.name} | Page {page_idx + 1}]"
                    page_chunks = chunk_text(page_text, source_tag)
                    for c_idx, chunk in enumerate(page_chunks):
                        meta = {
                            "source": file_path.name,
                            "type": "pdf",
                            "page": page_idx + 1,
                            "chunk_id": f"{file_path.stem}_p{page_idx+1}_{c_idx}",
                            "gdrive_url": GDRIVE_RESOURCES_URL,
                        }
                        results.append((chunk, meta))
            except Exception as pdf_err:
                logger.warning(f"Could not parse PDF {file_path.name}: {pdf_err}")

        elif suffix in [".txt", ".md"]:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            source_tag = f"[Knowledge Base / Research Document: {file_path.name}]"
            doc_chunks = chunk_text(content, source_tag)
            for c_idx, chunk in enumerate(doc_chunks):
                meta = {
                    "source": file_path.name,
                    "type": "text/markdown",
                    "chunk_id": f"{file_path.stem}_{c_idx}",
                    "gdrive_url": GDRIVE_RESOURCES_URL,
                }
                results.append((chunk, meta))

        elif suffix == ".csv":
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            header = lines[0] if lines else "data"
            for idx in range(1, len(lines), 10):
                batch_lines = lines[idx : idx + 10]
                text_block = (
                    f"Table Data ({file_path.name})\nColumns: {header}\n"
                    + "\n".join(batch_lines)
                )
                source_tag = f"[Agronomic Table: {file_path.name}]"
                meta = {
                    "source": file_path.name,
                    "type": "csv_table",
                    "chunk_id": f"{file_path.stem}_{idx}",
                    "gdrive_url": GDRIVE_RESOURCES_URL,
                }
                results.append((f"{source_tag}\n{text_block}", meta))

    except Exception as err:
        logger.error(f"Failed to process {file_path.name}: {err}")

    return results
