<p align="center">
  <img src="https://storage.googleapis.com/gweb-uniblog-publish-prod/images/gemini_2.max-1000x1000.png" width="250" alt="Gemini Logo" />
</p>

# 🌙 AAOIFI Standards Enhancement System

**AAOIFI Standards Enhancement System** is a multi-agent orchestration system designed to analyze, enhance, and validate AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards to ensure their Shariah compliance, clarity, and completeness.

# Table of Contents

- [🌙 AAOIFI Standards Enhancement System](#-aaoifi-standards-enhancement-system)
- [Features](#features)
  - [Standards Analysis](#standards-analysis)
  - [Shariah Compliance Verification](#shariah-compliance-verification)
  - [Content Enhancement](#content-enhancement)
  - [Quality Assurance](#quality-assurance)
  - [Knowledge Integration](#knowledge-integration)
- [System Architecture](#system-architecture)
- [Implementation](#implementation)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Usage](#cli-usage)
  - [API Server](#api-server)
- [Output](#output)
- [Docker Deployment](#docker-deployment)
- [Contact](#contact)
- [License](#license)

## Features

### Standards Analysis

- 📝 Parses and structures standards input for optimal processing
- 🔍 Identifies missing content, inconsistencies, and structural issues
- 📊 Analyzes document organization and flow

### Shariah Compliance Verification

- ✅ Evaluates standards against Shariah principles and requirements
- 🔄 Assigns quality scores based on compliance level (0-100)
- ⚖️ Highlights potential compliance issues for review

### Content Enhancement

- ✨ Improves language clarity and technical precision
- 📚 Enhances completeness and usability of standards
- 🧩 Restructures content for better flow and comprehension

### Quality Assurance

- 🔒 Final validation to ensure coherence and compliance
- 📋 Comprehensive quality checks before finalization
- 🛡️ Ensures all issues identified are properly addressed

### Knowledge Integration

- 🌐 Retrieves authoritative references from integrated PDF documents
- 📖 Incorporates relevant scholarly opinions and rulings through RAG
- 🔗 Links standards to authoritative Islamic finance references

## System Architecture

The system is composed of several specialized agents that work together in a pipeline:

1. **Orchestrator Agent**: The brain of the system that manages the flow between modules.
   - Keeps track of the context throughout the process
   - Makes decisions based on quality scores
   - Handles transitions between different agents

2. **Processing Pipeline**:
   - **Preprocessor**: Parses and structures the input. Flags missing content or structure.
   - **Reviewer**: Evaluates the quality and Shariah compliance. Assigns a score (0-100).
   - **Enhancer**: Improves language, clarity, completeness, and usability.
   - **Validator**: Final QA stage before output. Verifies the enhanced standard is coherent, complete, and compliant.

3. **RAG System**: Supports the pipeline by retrieving relevant information from PDF documents to enhance the quality of outputs.

## Implementation

This project uses:

- **Flask**: For building the REST API server
- **Google Gemini API**: Providing the LLM models for analysis and enhancement
- **RAG (Retrieval-Augmented Generation)**: For augmenting LLM outputs with domain-specific knowledge
- **PyPDF2**: For processing PDF documents containing AAOIFI standards and related information

## Project Structure

```
├── main.py                    # Main CLI entry point
├── server.py                  # Flask server for API access
├── pipeline/                  # Core pipeline components
│   └── orchestrator.py        # Orchestrator implementation
├── services/                  # Service components
│   └── llm_service.py         # LLM service using Gemini API
├── utils/                     # Utility functions
│   ├── gemini_client.py       # Gemini API client
│   ├── pdf_processor.py       # PDF document processor
│   ├── rag_system.py          # RAG implementation
│   └── vector_store.py        # Vector storage for document retrieval
├── data/                      # Storage for PDF documents used by RAG
```

## Getting Started

Follow these steps to set up and run the AAOIFI Standards Enhancement System locally.

### Prerequisites

Before you begin, ensure you have the following installed:

- [Python 3.9+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

### Installation

1. **Clone the repository**:

```bash
# Clone the repository
git clone https://github.com/IsDBI-Renaissance/Standard-Enhancement.git
cd Standard-Enhancement
```

2. **Set up a virtual environment**:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**:

```bash
# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with the following variables:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key

# Model Configuration
GEMINI_MODEL=gemini-1.5-pro

# Optional configurations
DEFAULT_QUALITY_SCORE=60
MAX_RETRIES=5
TEMPERATURE=0.7
MAX_OUTPUT_TOKENS=2048
TOP_P=0.9
TOP_K=40
```

## Usage

You can use the AAOIFI Standards Enhancement System in two ways: through the command-line interface (CLI) or as an API server.

### CLI Usage

For the full system (requires Gemini API key):

```bash
# Basic usage (RAG enabled by default)
python main.py --input "path/to/standard.txt" --output "output"

# Disable RAG if needed
python main.py --input "path/to/standard.txt" --output "output" --disable-rag

# Specify a custom directory for PDF documents
python main.py --input "path/to/standard.txt" --output "output" --rag-data-dir "custom_docs"
```

### API Server

You can also run the system as a Flask server:

```bash
python server.py
```

This will start a server at `http://localhost:8000` with the following endpoints:

- **POST /enhance**: Submit a standard text for enhancement
- **GET /**: Health check endpoint for the server

#### Example API Request Using cURL

```bash
curl -X POST "http://localhost:8000/enhance" \
  -H "Content-Type: application/json" \
  -d '{
    "standard_text": "Your standard text here...",
    "max_retries": 5,
    "default_quality": 60
  }'
```

#### Example API Request Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/enhance",
    json={
        "standard_text": "Your standard text here...",
        "max_retries": 5,
        "default_quality": 60
    }
)

if response.status_code == 200:
    result = response.json()
    enhanced_standard = result["enhanced_standard"]
    audit_trail = result["audit_trail"]
    
    # Do something with the results
    print(f"Enhanced standard length: {len(enhanced_standard)}")
    print(f"Audit trail length: {len(audit_trail)}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Output

The system produces the following outputs:

### CLI Output

When using the CLI interface, the system produces several output files:

1. **enhanced_standard.md**: The enhanced version of the AAOIFI standard
2. **audit_trail.md**: A detailed audit trail of the enhancement process
3. **rag_usage.md**: Information about the RAG system usage (when RAG is enabled)
4. **quality_scores.md**: Detailed quality scores for each pipeline stage (when debug mode is enabled)

### API Output

When using the API, the response includes:

1. **enhanced_standard**: The enhanced version of the AAOIFI standard text
2. **audit_trail**: A detailed audit trail of the enhancement process

## Docker Deployment

You can run the application using Docker:

```bash
# Build the Docker image
docker build -t standard-enhancement-api .

# Run the Docker container
docker run -p 8000:8000 -e GEMINI_API_KEY=your_gemini_api_key standard-enhancement-api
```

Alternatively, you can set up environment variables in a .env file and use:

```bash
docker run -p 8000:8000 --env-file .env standard-enhancement-api
```
    
## Contact

For inquiries or feedback, reach out to us at:

- 📧 Email: [ma_fellahi@esi.dz](mailto:ma_fellahi@esi.dz)
- 🌐 WhatsApp: +213 551 61 19 83
- **GitHub :** [flh-raouf](https://github.com/flh-raouf)

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](./LICENSE) file for more information.