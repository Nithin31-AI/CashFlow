import os
from typing import List, Dict, Any
import pdfplumber
from app.services.extraction.base import BaseDocumentExtractor, DocumentExtractionResult

class PDFDocumentExtractor(BaseDocumentExtractor):
    def extract(self, file_path: str) -> DocumentExtractionResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        extracted_rows: List[Dict[str, Any]] = []
        headers: List[str] = []
        text_sample = ""
        total_tables = 0
        uncertain_count = 0

        try:
            with pdfplumber.open(file_path) as pdf:
                for p_idx, page in enumerate(pdf.pages):
                    if p_idx == 0:
                        text_sample = (page.extract_text() or "")[:500]

                    tables = page.extract_tables()
                    for tbl in tables:
                        if not tbl or len(tbl) < 2:
                            continue
                        total_tables += 1
                        
                        # First table defines headers if not already set
                        if not headers:
                            raw_h = tbl[0]
                            headers = [str(col).strip() if col else f"Column_{i+1}" for i, col in enumerate(raw_h)]
                            table_rows = tbl[1:]
                        else:
                            table_rows = tbl

                        for row_vals in table_rows:
                            if not row_vals or all(c is None or str(c).strip() == "" for c in row_vals):
                                continue
                            row_dict = {}
                            has_none = False
                            for c_idx, h in enumerate(headers):
                                val = row_vals[c_idx] if c_idx < len(row_vals) else None
                                if val is None:
                                    has_none = True
                                    val = ""
                                else:
                                    val = str(val).strip()
                                row_dict[h] = val
                            
                            if has_none:
                                uncertain_count += 1
                            extracted_rows.append(row_dict)

            confidence = 0.85 if total_tables > 0 else 0.40
            if uncertain_count > 0 and len(extracted_rows) > 0:
                confidence = max(0.50, confidence - (uncertain_count / len(extracted_rows) * 0.3))

            return DocumentExtractionResult(
                document_type="PDF",
                is_supported=True,
                requires_ocr_config=False if total_tables > 0 else True,
                configuration_notes=None if total_tables > 0 else "No structured text tables detected. Scanned or image-only PDF requires OCR engine setup (e.g. Tesseract or cloud OCR adapter).",
                extracted_text_sample=text_sample,
                headers=headers,
                structured_rows=extracted_rows,
                extraction_confidence=confidence,
                uncertain_fields_count=uncertain_count,
            )
        except Exception as e:
            return DocumentExtractionResult(
                document_type="PDF",
                is_supported=False,
                requires_ocr_config=True,
                configuration_notes=f"PDF extraction error: {str(e)}. Document may be encrypted or image-only.",
                extraction_confidence=0.0,
            )
