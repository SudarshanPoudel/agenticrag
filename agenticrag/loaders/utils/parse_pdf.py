import json
import logging
import time
from pathlib import Path
from typing import Literal

def parse_pdf(path:str, use_ocr=False) -> str:
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
        from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractOcrOptions  
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except ImportError:
        raise ImportError("Docling is required to parse PDFs. Please run `pip install docling` to install it.")
    
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = use_ocr
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    
    if use_ocr:
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_picture_images = True
        pipeline_options.ocr_options = TesseractOcrOptions()

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend=PyPdfiumDocumentBackend,
            ),
        }
    )
    conv_result = doc_converter.convert(path)
    return conv_result.document.export_to_markdown()