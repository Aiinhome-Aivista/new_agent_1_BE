import os
import uuid
import traceback

def extract_first_image_from_pdf(pdf_path, output_dir):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            for img_info in doc.get_page_images(i):
                xref = img_info[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                # Filter out very small images (icons, logos)
                if pix.width < 300 or pix.height < 200:
                    continue
                    
                img_path = os.path.join(output_dir, f"extracted_{uuid.uuid4()}.png")
                pix.save(img_path)
                return img_path
    except Exception as e:
        print(f"Error extracting image from PDF {pdf_path}: {e}")
        traceback.print_exc()
    return None

def extract_first_image_from_docx(docx_path, output_dir):
    try:
        import docx
        doc = docx.Document(docx_path)
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                img_data = rel.target_part.blob
                # Basic size check if possible, or just take the first one
                if len(img_data) > 15000: # heuristic for non-icon images (>15KB)
                    img_path = os.path.join(output_dir, f"extracted_{uuid.uuid4()}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    return img_path
    except Exception as e:
        print(f"Error extracting image from DOCX {docx_path}: {e}")
        traceback.print_exc()
    return None

def extract_architecture_image(file_path):
    if not file_path or not os.path.exists(file_path):
        return None
        
    ext = os.path.splitext(file_path)[1].lower()
    output_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'images')
    os.makedirs(output_dir, exist_ok=True)
    
    if ext == ".pdf":
        return extract_first_image_from_pdf(file_path, output_dir)
    elif ext in [".docx", ".doc"]:
        return extract_first_image_from_docx(file_path, output_dir)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return file_path
    
    return None
