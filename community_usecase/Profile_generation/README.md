# Scholar Profile Generation

This project provides an end-to-end pipeline for automatically generating a polished HTML profile for an academic **scholar** starting from their Google Scholar (or similar) profile link.

The pipeline is powered by [CAMEL-AI](https://github.com/camel-ai/camel) agents and Playwright-based headless browsing and is exposed both as a **CLI tool** and as a **Flask REST API** with an accompanying (very) minimal front-end.

---

## Key Features

* **Smart link discovery** – Uses the Exa search engine, via `camel-ai`'s `SearchToolkit`, to find high-quality links related to the scholar (homepage, Google Scholar, institutional pages, social media, etc.).
* **Headless crawling & markdown extraction** – `BrowserNonVisualToolkit` (Playwright under the hood) visits each link, extracts the main content, and stores it as individual markdown files.
* **Asynchronous Web Agent** – Link crawling and content extraction are orchestrated with **asyncio**, allowing multiple pages to be processed **concurrently** and cutting the end-to-end runtime significantly compared with sequential scraping.
* **Automatic HTML generation** – Aggregated markdown is parsed with an LLM to fill an HTML template (`template.html`) resulting in a share-ready profile page.
* **Progress tracking** – Long-running jobs execute in a background thread. Progress can be polled via `/api/progress/<job_id>`.
* **Dual usage modes** –
  * **CLI**: `python app.py --url <scholar_url>`
  * **Web**: `python app.py` (serves on `http://localhost:5000`)

---

## Project Structure

```
community_usecase/Profile_generation/
├── app.py                # Main entry point (CLI & Flask server)
├── template.html         # Bootstrap-based HTML template filled by the pipeline
├── templates/            # Front-end assets (index.html, CSS, JS)
└── workflow.png          # Architecture diagram
```

---

## Quick Start

1. **Install Python dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate          # On Windows use: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Set environment variables**

   The pipeline relies on LLMs and Exa search.

   ```bash
   export OPENAI_API_KEY=<your-openai-key>
   export EXA_API_KEY=<your-exa-key>
   ```

3. **Run the web server**

   ```bash
   python app.py
   # Open http://localhost:5000 in your browser
   ```

   Or generate a profile once via CLI:

   ```bash
   python app.py --url "https://scholar.google.com/citations?user=<SCHOLAR_ID>"
   ```

   The resulting HTML file will be placed in the project directory (e.g. `profile.html`).

---

