from io import BytesIO
from docx import Document


def _extract_table_text(table):
    """Recursively extract text from all cells in a table, including nested tables."""
    text = ""
    for row in table.rows:
        for cell in row.cells:
            # Extract paragraphs inside the cell
            for paragraph in cell.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            # Recurse into nested tables
            for nested_table in cell.tables:
                text += _extract_table_text(nested_table)
    return text


def extract_text_from_docx(file_bytes):

    document = Document(BytesIO(file_bytes))

    extracted_text = ""

    # Extract paragraphs (body text, headings, bullet points)
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            extracted_text += paragraph.text + "\n"

    # Extract text from tables (common in resume templates)
    for table in document.tables:
        extracted_text += _extract_table_text(table)

    # Extract text from text boxes and shapes inside the document body
    # These are stored as XML drawing elements — parse them directly
    from docx.oxml.ns import qn
    for shape in document.element.body.iter(qn("wp:inline"), qn("wp:anchor")):
        for text_elem in shape.iter(qn("a:t")):
            content = text_elem.text
            if content and content.strip():
                extracted_text += content.strip() + "\n"

    return extracted_text