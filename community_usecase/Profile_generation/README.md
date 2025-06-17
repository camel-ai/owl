# Profile Generation Web Application

This web application allows you to generate academic profiles from Google Scholar URLs using AI-powered web browsing and content analysis.

## Features

- Extract scholar information from Google Scholar profiles
- Search for relevant web links automatically
- Interactive web interface to review and modify candidate URLs
- AI-powered profile generation using browser automation
- Export profiles to HTML format

## Setup

### Prerequisites

- Python 3.8+
- CAMEL-AI library
- OpenAI API key
- EXA API key (for web search)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
   - Copy your `.env` file to the appropriate location with:
     - `OPENAI_API_KEY`
     - `EXA_API_KEY` (if different from hardcoded value)

### Running the Application

#### Web Interface (Recommended)

1. Start the web server:
```bash
python run_profile_generation.py --web
```

2. Open your browser and go to: `http://localhost:5000`

3. Follow the web interface:
   - Enter a Google Scholar URL
   - Add any blacklisted URLs (optional)
   - Click "Search" to find the scholar info and candidate URLs
   - Review and modify the candidate URLs as needed
   - Click "Generate Profile" to create the final profile
   - Click "View Profile" to see the generated HTML

#### Command Line Interface

For direct command-line usage:
```bash
python run_profile_generation.py --task "https://scholar.google.com/citations?user=..." --blacklist "http://unwanted-site.com" --output_file "output.html"
```

## Web Interface Workflow

1. **Input Scholar URL**: Enter the Google Scholar profile URL
2. **Set Blacklist**: (Optional) Add URLs you want to exclude from search
3. **Search**: Click search to get scholar info and candidate URLs
4. **Review URLs**: The system will show:
   - Identified scholar name and affiliation
   - List of candidate URLs found through web search
5. **Modify URLs**: You can:
   - Remove unwanted URLs by clicking the × button
   - Add new URLs by clicking the + button
6. **Generate Profile**: Click "Generate Profile" to start the AI-powered browsing and analysis
7. **View Result**: Click "View Profile" to open the generated HTML profile

## API Endpoints

- `GET /` - Serve the web interface
- `POST /api/search_scholar` - Search for scholar info and URLs
- `POST /api/generate_profile` - Generate the final profile
- `GET /api/get_profile` - Serve the generated HTML profile

## Files Structure

- `run_profile_generation.py` - Main application with Flask backend
- `templates/index.html` - Web interface frontend
- `browser_toolkit.py` - Browser automation toolkit
- `template.html` - HTML template for generated profiles
- `start_server.py` - Simple startup script
- `requirements.txt` - Python dependencies

## Notes

- The profile generation process may take several minutes depending on the number of URLs to browse
- The browser runs in non-headless mode by default for debugging purposes
- Generated profiles are saved as `scholar.html` in the working directory
- The system uses CAMEL-AI's browser toolkit for intelligent web browsing and content extraction

## Troubleshooting

- If you encounter browser-related errors, try restarting the application
- Make sure all API keys are properly configured
- Check the console logs for detailed error information
- Ensure the `templates/` directory exists and contains `index.html`
