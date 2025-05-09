# AAOIFI Standards Enhancement System

A multi-agent orchestration system designed to analyze, enhance, and validate AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) standards to ensure their Shariah compliance, clarity, and completeness.

## Overview

This solution automates and structures the way Islamic financial standards are reviewed and improved using a combination of AI tools in a modular pipeline built with LangGraph and LangChain.

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

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aaoifi-standards-enhancement.git
cd aaoifi-standards-enhancement

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit the .env file with your API keys
```

## Usage

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

Example API request using curl:

```bash
curl -X POST "http://localhost:8000/enhance" \
  -H "Content-Type: application/json" \
  -d '{
    "standard_text": "Your standard text here...",
    "max_retries": 5,
    "default_quality": 60
  }'
```

Example API request using Python:

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

## Requirements

- Python 3.9+
- OpenAI API key
- SerpAPI key (for web search capabilities)

## Configuration

Create a `.env` file with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_api_key
```

## License

[MIT](LICENSE)
