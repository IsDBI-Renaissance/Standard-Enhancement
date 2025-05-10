<p align="center">
  <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" width="250" alt="FastAPI Logo" />
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

- 🌐 Retrieves authoritative references from external sources
- 📖 Incorporates relevant scholarly opinions and rulings
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

3. **Knowledge Retrieval Tool**: Supports the pipeline by fetching authoritative references from external sources when needed.

## Implementation

This project uses:

- **LangGraph**: For building the multi-agent orchestration graph with conditional transitions
- **LangChain**: For integrating with LLMs and building agent components
- **OpenAI**: Providing the LLM models for analysis and enhancement
- **SerpAPI**: For web searches to retrieve external knowledge

## Project Structure

```
├── main.py                    # Main entry point
├── demo_main.py               # Simplified demo version
├── pipeline/                  # Core pipeline components
│   ├── orchestrator.py        # Orchestrator implementation
│   ├── agents/                # Agent implementations
│   │   ├── base_agent.py      # Base agent class
│   │   ├── preprocessor.py    # Preprocessor agent
│   │   ├── reviewer.py        # Reviewer agent
│   │   ├── enhancer.py        # Enhancer agent
│   │   └── validator.py       # Validator agent
│   ├── knowledge_retrieval/   # Knowledge retrieval components
│   │   └── retriever.py       # Knowledge retriever implementation
│   ├── models/                # Data models
│   │   └── models.py          # Pydantic models for the pipeline
│   └── utils/                 # Utility functions
│       └── helpers.py         # Helper functions
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
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_api_key

# Optional configurations
ENHANCEMENT_MIN_SCORE=60
MAX_RETRY_ATTEMPTS=5
```

## Usage

You can use the AAOIFI Standards Enhancement System in two ways: through the command-line interface (CLI) or as an API server.

### CLI Usage

For the full system (requires OpenAI API key and SerpAPI key):

```bash
python main.py --input "path/to/standard.txt" --output "output"
```

For the demonstration version (no API keys required):

```bash
python demo_main.py --input "path/to/standard.txt" --output "output"
```

### API Server

You can also run the system as a FastAPI server:

```bash
python server.py
```

This will start a server at `http://localhost:8000` with the following endpoints:

- **POST /enhance**: Submit a standard text for enhancement
- **GET /health**: Check the health of the server

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

When using the CLI interface, the system produces two main output files:

1. **enhanced_standard.md**: The enhanced version of the AAOIFI standard
2. **audit_trail.md**: A detailed audit trail of the enhancement process

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
docker run -p 8000:8000 -e OPENAI_API_KEY=your_openai_api_key -e SERPAPI_API_KEY=your_serpapi_api_key standard-enhancement-api
```

Alternatively, you can set up environment variables in a .env file and use:

```bash
docker run -p 8000:8000 --env-file .env aaoifi-standard-api
```
    
## Contact

For inquiries or feedback, reach out to us at:

- 📧 Email: [ma_fellahi@esi.dz](mailto:ma_fellahi@esi.dz)
- 🌐 WhatsApp: +213 551 61 19 83
- **GitHub :** [flh-raouf](https://github.com/flh-raouf)

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](./LICENSE) file for more information.