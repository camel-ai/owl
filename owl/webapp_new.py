import os
import gradio as gr
from pathlib import Path
import logging
from datetime import datetime
import importlib
from dotenv import load_dotenv
import json
from fpdf import FPDF
from docx import Document
from markdown_it import MarkdownIt
import re
from utils import run_society

# Configure logging
def setup_logging():
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"owl_log_{datetime.now().strftime('%Y-%m-%d')}.txt"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file

# File export functions
def export_to_pdf(text, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split text into lines that fit the page width
    lines = text.split('\n')
    for line in lines:
        # Handle non-ASCII characters
        line = line.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=line)
    
    output_path = Path("outputs") / filename
    output_path.parent.mkdir(exist_ok=True)
    pdf.output(str(output_path))
    return str(output_path)

def export_to_docx(text, filename="output.docx"):
    doc = Document()
    doc.add_paragraph(text)
    
    output_path = Path("outputs") / filename
    output_path.parent.mkdir(exist_ok=True)
    doc.save(str(output_path))
    return str(output_path)

def format_markdown(text):
    # Convert to HTML using markdown-it-py
    md = MarkdownIt()
    html = md.render(text)
    return html

class OWLAssistant:
    def __init__(self):
        load_dotenv()
        self.history = []
        
    def process_request(self, message, module_name="run_ollama", format_type="text"):
        try:
            # Import the specified module
            module = importlib.import_module(f"examples.{module_name}")
            
            # Create society and process request
            society = module.construct_society(message)
            answer, chat_history, token_info = run_society(society)
            
            # Format the response based on type
            if format_type == "pdf":
                filepath = export_to_pdf(answer)
                return f"Response has been saved to PDF: {filepath}", chat_history
            elif format_type == "docx":
                filepath = export_to_docx(answer)
                return f"Response has been saved to DOCX: {filepath}", chat_history
            else:
                return format_markdown(answer), chat_history
                
        except Exception as e:
            logging.error(f"Error processing request: {str(e)}")
            return f"Error: {str(e)}", None

def create_ui():
    owl = OWLAssistant()
    
    with gr.Blocks(title="OWL Assistant", theme=gr.themes.Soft()) as interface:
        # Add custom CSS
        gr.HTML("""
            <style>
            .container {
                max-width: 1200px;
                margin: auto;
            }
            
            .chatbot {
                height: 600px !important;
                overflow-y: auto;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .user-message {
                background-color: #f0f7ff;
                padding: 10px;
                border-radius: 10px;
                margin: 5px;
            }
            
            .assistant-message {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 10px;
                margin: 5px;
            }
            
            .input-row {
                margin-top: 20px;
            }
            
            .control-buttons {
                display: flex;
                gap: 10px;
                margin-top: 10px;
            }
            
            .export-buttons {
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }
            
            .settings-panel {
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 10px;
                margin-left: 20px;
            }
            </style>
        """)
        
        gr.Markdown("# 🦉 OWL Writing Assistant")
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    show_label=False,
                    elem_classes="chatbot"
                )
                with gr.Row(elem_classes="input-row"):
                    msg = gr.Textbox(
                        show_label=False,
                        placeholder="Enter your request here...",
                        container=False,
                        scale=12
                    )
                    
                with gr.Row(elem_classes="control-buttons"):
                    submit = gr.Button("Send", variant="primary")
                    clear = gr.Button("Clear")
                    
                with gr.Row(elem_classes="export-buttons"):
                    pdf_btn = gr.Button("📄 Export to PDF")
                    docx_btn = gr.Button("📝 Export to DOCX")
                    
            with gr.Column(scale=1, elem_classes="settings-panel"):
                format_type = gr.Radio(
                    choices=["text", "pdf", "docx"],
                    value="text",
                    label="Output Format"
                )
                module_select = gr.Dropdown(
                    choices=["run_ollama", "run_mistral"],
                    value="run_ollama",
                    label="Model"
                )
                
        def respond(message, chat_history, format_type, module_name):
            response, history = owl.process_request(message, module_name, format_type)
            chat_history.append((message, response))
            return "", chat_history
            
        def export_pdf(chat_history):
            if not chat_history:
                return "No content to export"
            text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in chat_history])
            filepath = export_to_pdf(text, f"owl_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            return f"Exported to {filepath}"
            
        def export_docx(chat_history):
            if not chat_history:
                return "No content to export"
            text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in chat_history])
            filepath = export_to_docx(text, f"owl_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
            return f"Exported to {filepath}"
        
        msg.submit(
            respond,
            [msg, chatbot, format_type, module_select],
            [msg, chatbot]
        )
        
        submit.click(
            respond,
            [msg, chatbot, format_type, module_select],
            [msg, chatbot]
        )
        
        clear.click(lambda: None, None, chatbot, queue=False)
        
        pdf_btn.click(
            export_pdf,
            chatbot,
            gr.Textbox(label="Export Status")
        )
        
        docx_btn.click(
            export_docx,
            chatbot,
            gr.Textbox(label="Export Status")
        )
        
    return interface

if __name__ == "__main__":
    setup_logging()
    app = create_ui()
    app.launch()
