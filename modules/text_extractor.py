import hashlib
import os
import pymupdf as fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple

class TextExtractor:
    """Extracts text from PDF and TXT documents with page-level tracking and checksum fingerprinting."""

    @staticmethod
    def compute_file_hash(file_bytes: bytes) -> str:
        """Compute SHA256 checksum for document duplicate prevention."""
        return hashlib.sha256(file_bytes).hexdigest()

    @classmethod
    def extract_pages(cls, file_name: str, file_bytes: bytes) -> Tuple[List[Dict[str, Any]], str]:
        """
        Extract page-level structured content from uploaded bytes.
        Returns:
            pages: List[Dict] containing {'doc_name': str, 'page_num': int, 'text': str}
            file_hash: SHA256 fingerprint
        """
        file_hash = cls.compute_file_hash(file_bytes)
        ext = os.path.splitext(file_name)[1].lower()

        if ext == ".pdf":
            return cls._extract_pdf(file_name, file_bytes), file_hash
        elif ext == ".txt":
            return cls._extract_txt(file_name, file_bytes), file_hash
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_pdf(file_name: str, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract text from PDF pages using PyMuPDF."""
        pages = []
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            if doc.is_encrypted:
                raise ValueError("PDF file is password protected and cannot be processed.")

            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                text = page.get_text("text").strip()
                if text:
                    pages.append({
                        "doc_name": file_name,
                        "page_num": page_idx + 1,
                        "text": text
                    })
            doc.close()
        except Exception as e:
            if "password" in str(e).lower():
                raise ValueError("PDF is encrypted or password protected.")
            raise RuntimeError(f"Error parsing PDF '{file_name}': {str(e)}")

        if not pages:
            raise ValueError(f"No extractable text found in '{file_name}'. The PDF may contain only scanned images.")

        return pages

    @staticmethod
    def _extract_txt(file_name: str, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract text from TXT file."""
        try:
            text_content = file_bytes.decode("utf-8", errors="replace").strip()
        except Exception as e:
            raise ValueError(f"Could not read text file '{file_name}': {str(e)}")

        if not text_content:
            raise ValueError(f"Text file '{file_name}' is empty.")

        # Chunk text into pseudo-pages (~1500 chars per page for consistency in citation)
        chunk_size = 1500
        chunks = [text_content[i:i + chunk_size] for i in range(0, len(text_content), chunk_size)]
        
        pages = []
        for idx, chunk in enumerate(chunks):
            pages.append({
                "doc_name": file_name,
                "page_num": idx + 1,
                "text": chunk.strip()
            })
        return pages
