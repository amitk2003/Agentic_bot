import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import os
import io

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using PyMuPDF. Falls back to OCR if text is empty."""
    text = ""
    try:
        doc = fitz.open(file_path)
        all_links = set()
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text += page_text + "\n"
            else:
                # Fallback to OCR if page has no text (scanned PDF)
                # Optimize by reducing resolution before OCR to speed it up
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) # Slightly lower res for speed
                img = Image.open(io.BytesIO(pix.tobytes()))
                # Resize if too large
                if img.width > 2000 or img.height > 2000:
                    img.thumbnail((2000, 2000))
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text + "\n"
                
            # Extract hyperlinks
            for link in page.get_links():
                if 'uri' in link:
                    all_links.add(link['uri'])
                    
        if all_links:
            links_text = "--- Embedded Links ---\n"
            for link in all_links:
                links_text += f"- {link}\n"
            links_text += "----------------------\n\n"
            text = links_text + text

                
        return text.strip()
    except Exception as e:
        return f"[Error extracting PDF: {str(e)}]"

def extract_text_from_image(file_path: str) -> str:
    """Extracts text from an image using Tesseract OCR."""
    try:
        img = Image.open(file_path)
        # Resize if too large for faster OCR
        if img.width > 2000 or img.height > 2000:
            img.thumbnail((2000, 2000))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        return f"[Error extracting Image: {str(e)}]"
