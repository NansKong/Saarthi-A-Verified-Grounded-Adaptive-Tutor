"""
src/ingestion - Pod A: Multimodal Extraction & Document Parsers
Exports:
- process_pdf: PDF text & visual extraction pipeline
- process_ppt: PowerPoint text & slide visual extraction pipeline
- process_video: Video Whisper transcription & timestamp alignment
- extract_pdf_content: Low-level PDF extractor
- extract_ppt_content: Low-level PPTX extractor
- extract_images_from_pdf, extract_images_from_ppt
- chunk_text: Sliding window chunker
"""

__all__ = [
    "process_pdf",
    "process_ppt",
    "process_video",
    "extract_pdf_content",
    "extract_ppt_content",
    "extract_images_from_pdf",
    "extract_images_from_ppt",
    "chunk_text",
]

try:
    from src.ingestion.processing.chunker import chunk_text
except ImportError:
    chunk_text = None

try:
    from src.ingestion.ingestion.pdf_parser import extract_pdf_content
    from src.ingestion.ingestion.pdf_image_extractor import extract_images_from_pdf
    from src.ingestion.ingestion.pdf_pipeline import process_pdf
except ImportError:
    extract_pdf_content = None
    extract_images_from_pdf = None
    process_pdf = None

try:
    from src.ingestion.ingestion.ppt_parser import extract_ppt_content
    from src.ingestion.ingestion.ppt_image_extractor import extract_images_from_ppt
    from src.ingestion.ingestion.ppt_pipeline import process_ppt
except ImportError:
    extract_ppt_content = None
    extract_images_from_ppt = None
    process_ppt = None

try:
    from src.ingestion.ingestion.video_pipeline import process_video
except ImportError:
    process_video = None
