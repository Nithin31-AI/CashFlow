import os
from PIL import Image
from app.services.extraction.base import BaseDocumentExtractor, DocumentExtractionResult

class ImageDocumentExtractor(BaseDocumentExtractor):
    """
    Extensible image extraction interface for receipts, vouchers, and statements.
    Validates image structure, extracts dimensions, and plugs into OCR pipeline.
    If OCR engine is not configured, provides a documented extension point
    without inventing fake financial numbers.
    """
    def extract(self, file_path: str) -> DocumentExtractionResult:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format or "IMAGE"

            # Check if tesseract or OCR library is configured
            ocr_available = False
            extracted_text = ""
            try:
                import pytesseract
                # Test if tesseract binary responds
                extracted_text = pytesseract.image_to_string(Image.open(file_path))
                ocr_available = True
            except Exception:
                ocr_available = False

            if ocr_available and extracted_text.strip():
                return DocumentExtractionResult(
                    document_type=format_name,
                    is_supported=True,
                    requires_ocr_config=False,
                    extracted_text_sample=extracted_text[:500],
                    headers=["Line_Text"],
                    structured_rows=[{"Line_Text": line.strip()} for line in extracted_text.splitlines() if line.strip()],
                    extraction_confidence=0.75,
                    uncertain_fields_count=0,
                )
            else:
                return DocumentExtractionResult(
                    document_type=format_name,
                    is_supported=True,
                    requires_ocr_config=True,
                    configuration_notes=(
                        f"Image parsed successfully ({width}x{height} {format_name}). "
                        "OCR engine is not configured in this environment. To enable automated text/table extraction "
                        "from receipt images, install 'tesseract-ocr' or configure an external cloud OCR adapter (e.g. AWS Textract, GCP Vision)."
                    ),
                    headers=[],
                    structured_rows=[],
                    extraction_confidence=0.0,
                    uncertain_fields_count=0,
                )
        except Exception as e:
            return DocumentExtractionResult(
                document_type="IMAGE",
                is_supported=False,
                requires_ocr_config=True,
                configuration_notes=f"Image reading error: {str(e)}",
                extraction_confidence=0.0,
            )
