import pymupdf


def extract_text_from_pdf(file_bytes):

    pdf_document = pymupdf.open(stream=file_bytes, filetype="pdf")

    extracted_text = ""

    for page in pdf_document:
        extracted_text += page.get_text()

    pdf_document.close()

    return extracted_text