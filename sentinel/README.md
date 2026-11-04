# Sentinel

**AI-Powered Incident Investigation Platform**

Sentinel is an AI-powered application designed to detect data quality incidents, investigate supporting evidence, and identify potential root causes using an AI agent.

It combines deterministic data validation with dynamic tool calling to generate evidence-based investigation reports.

## Features

- CSV data ingestion
- Automated data quality monitoring
- Missing value detection
- Duplicate record detection
- Schema drift detection
- Data type mismatch detection
- SQLite-based incident persistence
- Incident status management and history
- AI-powered incident investigation
- Dynamic agent tool calling
- Evidence-based investigation reports
- Root cause analysis with uncertainty reporting
- Interactive web dashboard

## Technology

**Backend**
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

**AI Agent**
- Google GenAI SDK
- Custom agent execution loop
- Dynamic tool calling

**Frontend**
- HTML
- CSS
- JavaScript

**Testing**
- Pytest
- FastAPI TestClient

## Project Structure

```text
sentinel/
├── app/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── services/
│   ├── config.py
│   └── main.py
├── static/
│   └── index.html
├── tests/
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/vishal-benake/sentinel
cd sentinel
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file using `.env.example` as a reference.

Configure the required AI API credentials locally.

Never commit your `.env` file or expose API keys.

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

Open the dashboard:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

## Run Tests

```bash
pytest -v
```

## Current Status

Core functionality implemented.

**Latest test results: 34 passed.**

## Future Improvements

- Investigation report persistence
- Additional data quality checks
- Improved investigation evaluation
- Human-reviewed remediation workflows

---

Built as an AI engineering portfolio project.