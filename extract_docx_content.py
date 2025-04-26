import docx

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

# Extract text from the DOCX file
file_path = 'data/gaia/2023/validation/cffe0e32-c9a6-4c52-9877-78ceb4aaa9fb.docx'
extracted_text = extract_text_from_docx(file_path)
extracted_text