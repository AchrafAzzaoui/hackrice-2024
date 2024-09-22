import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import os
import re
import logging
import PyPDF2
from collections import defaultdict, deque


def extract_text_with_pypdf2(pdf_path):
    """
    Extracts text from a PDF file using PyPDF2.

    :param pdf_path: Path to the PDF file.
    :return: Extracted text as a single continuous string.
    """
    combined_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    cleaned_text = re.sub(r'\s+', ' ', text.strip())
                    combined_text += cleaned_text + " "
    except Exception as e:
        print(f"PyPDF2 Error extracting text: {e}")
    return combined_text.strip()

def extract_text_and_images(pdf_path):
    """
    Extracts text and images from a PDF file in the order they appear.
    Embeds OCR'd text from images directly into the continuous paragraph.

    :param pdf_path: Path to the PDF file.
    :return: Combined text as a single continuous string.
    """
    combined_text = ""
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)
        # Iterate through each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Get the page's content blocks
            blocks = page.get_text("dict")["blocks"]
            for block_index, block in enumerate(blocks, start=1):
                # Handle Text Blocks
                if block["type"] == 0:  # Text block
                    text = block.get("text", "").strip()
                    if text:
                        # Clean the text by replacing multiple whitespaces with a single space
                        cleaned_text = re.sub(r'\s+', ' ', text)
                        combined_text += cleaned_text + " "
                # Handle Image Blocks
                elif block["type"] == 1:  # Image block
                    try:
                        # Extract image
                        image_data = block.get("image")
                        # Handle different types of 'image' data
                        if isinstance(image_data, int):
                            # 'image' is an xref number
                            try:
                                base_image = doc.extract_image(image_data)
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]

                                # Open image with PIL
                                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                                # Perform OCR on the image
                                ocr_text = pytesseract.image_to_string(image).strip()
                                if ocr_text:
                                    # Clean the OCR'd text
                                    cleaned_ocr_text = re.sub(r'\s+', ' ', ocr_text)
                                    combined_text += cleaned_ocr_text + " "
                            except Exception as img_err:
                                print(f"Error processing image with xref {image_data} on Page {page_num +1}, Block {block_index}: {img_err}")

                        elif isinstance(image_data, bytes):
                            # 'image' contains image bytes directly
                            try:
                                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                                # Perform OCR on the image
                                ocr_text = pytesseract.image_to_string(image).strip()
                                if ocr_text:
                                    # Clean the OCR'd text
                                    cleaned_ocr_text = re.sub(r'\s+', ' ', ocr_text)
                                    combined_text += cleaned_ocr_text + " "
                            except Exception as img_err:
                                print(f"Error processing direct image on Page {page_num +1}, Block {block_index}: {img_err}")
                    except Exception as block_err:
                        print(f"Error processing block on Page {page_num +1}, Block {block_index}: {block_err}")
        # Final cleanup: Replace multiple spaces with a single space
        combined_text = re.sub(r'\s+', ' ', combined_text).strip()
    except Exception as e:
        return
        print(f"Error processing PDF file: {e}")
    return combined_text


def run(filename: str):
    # TODO: tesseract setup

    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two directory levels
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    # Join with the filename
    full_path = os.path.join(parent_dir, filename)
    # Normalize the path
    normalized_path = os.path.normpath(full_path)

    # Path to your PDF file
    pdf_file = normalized_path
    # Check if the PDF file exists
    if not os.path.exists(pdf_file):
        print(f"The file {pdf_file} does not exist.")
        return
    # Extract text and images with PyMuPDF
    combined_text_pymupdf = extract_text_and_images(pdf_file)
    # Extract text with PyPDF2 as a fallback
    combined_text_pypdf2 = extract_text_with_pypdf2(pdf_file)
    # Combine both texts
    if combined_text_pypdf2:
        combined_text = combined_text_pymupdf + " " + combined_text_pypdf2
    else:
        combined_text = combined_text_pymupdf
    # Final cleanup: Replace multiple spaces with a single space
    combined_text = re.sub(r'\s+', ' ', combined_text).strip()
    return combined_text
    
    
    # # Save the combined text to a file
    # output_text_file = "/Users/wyattbellinger/Projects/Testing/output_text.txt"
    # try:
    #     with open(output_text_file, 'w', encoding='utf-8') as f:
    #         f.write(combined_text)
    # except Exception as e:
    #     print(f"Error writing combined text to file: {e}")
    # # Optionally print the text
    # # print(combined_text)