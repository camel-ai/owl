import PyPDF2

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Initialize a variable to store the extracted text
        extracted_text = ""
        
        # Iterate through each page in the PDF
        for page in pdf_reader.pages:
            # Extract text from the page
            extracted_text += page.extract_text()
        
    return extracted_text

# Function to search for a specific term in the extracted text
def search_for_term(text, term):
    # Check if the term is in the text
    if term.lower() in text.lower():
        return True
    return False

# Path to the PDF file
pdf_path = 'path_to_your_pdf/1004106.pdf'

# Extract text from the PDF
text = extract_text_from_pdf(pdf_path)

# Search for Valentina Re's contribution and the horror movie
valentina_re_found = search_for_term(text, "Valentina Re")
horror_movie_found = search_for_term(text, "horror movie")

# Print the results
print("Valentina Re found:", valentina_re_found)
print("Horror movie found:", horror_movie_found)