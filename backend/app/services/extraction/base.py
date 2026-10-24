from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ExtractionField(BaseModel):
    field_name: str
    value: Any
    confidence: float  # 0.0 to 1.0
    is_uncertain: bool
    source_bbox: Optional[List[float]] = None

class ExtractionRow(BaseModel):
    row_index: int
    fields: Dict[str, ExtractionField]
    overall_confidence: float
    requires_user_review: bool

class DocumentExtractionResult(BaseModel):
    document_type: str
    is_supported: bool
    requires_ocr_config: bool = False
    configuration_notes: Optional[str] = None
    extracted_text_sample: Optional[str] = None
    extracted_tables: List[List[Dict[str, Any]]] = []
    headers: List[str] = []
    structured_rows: List[Dict[str, Any]] = []
    extraction_confidence: float = 0.0
    uncertain_fields_count: int = 0

class BaseDocumentExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> DocumentExtractionResult:
        """
        Extracts structured financial information from a document.
        Does not fabricate missing values. Flags uncertainty.
        """
        pass
