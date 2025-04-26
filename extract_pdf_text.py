import PyPDF2

# Define the path to the PDF file
pdf_file_path = 'extracted_files/Job Listing.pdf'

# Open the PDF file
with open(pdf_file_path, 'rb') as file:
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfReader(file)
    
    # Initialize a variable to store the text
    pdf_text = ''
    
    # Iterate through each page in the PDF
    for page in pdf_reader.pages:
        # Extract text from the page
        pdf_text += page.extract_text()

# Print the extracted text
pdf_text