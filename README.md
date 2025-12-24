# AI-Powered QA Testing with Intelligent Agent Fallback

This project provides an automated QA testing system powered by Stagehand AI that:
- Converts human-written test steps into executable actions
- Executes UI automation with strict validation
- **Uses AI agent fallback for intelligent error recovery**
- Captures detailed screenshots and diagnostics
- Auto-generates verification steps after each action

## Key Features

- 🤖 **AI-Powered Step Conversion**: Automatically converts plain text test steps into structured JSON actions
- ⚡ **Hybrid Execution Strategy**: Uses `page.act()` for fills (fast) and `page.act(useVision=True)` for clicks (intelligent vision-based)
- ✅ **Automatic Verification**: Adds verification steps after each click action
- 🔍 **Strict Failure Detection**: Validates every action to ensure it actually succeeded
- 🧠 **Advanced Agent Fallback**: Uses `agent.execute()` with multi-step reasoning for intelligent recovery when primary actions fail
- 🎯 **Multi-Step Recovery**: Agent can try up to 10 different strategies (alternative selectors, scrolling, modal handling, diagnostics)
- 📸 **Comprehensive Screenshots**: Captures before/after/error/fallback screenshots for every step
- 📊 **Detailed Logging**: Provides step-by-step execution logs with validation details and agent reasoning traces

## Documentation

Most standalone docs were removed. Use the inline comments and these entry points:
- `app/utils/step_converter.py` – Step conversion rules, action schema, and natural-language mapping
- `app/services/main.py` – Execution flow, wait logic, hybrid/agent fallback behavior
- `storage/steps.txt` – Author your test steps here
- `storage/actions.json` and `storage/actions_natural.txt` – Generated outputs for review

Notes:
- The converter strictly avoids inventing steps and preserves locator/instruction steps verbatim.
- Supports navigate, fill, click, press, expect, select, and instruction action types.

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in the required variables:

```bash
cp .env.example .env
```

Edit `.env` to provide actual values.

---

### 3. Install Dependencies

> Requires Poetry. Install from https://python-poetry.org/docs/#installation

- Linux/macOS:

```bash
sudo apt-get update && sudo apt-get install -y libpq-dev python3-dev build-essential
poetry install
```

- Windows (PowerShell):

```powershell
python --version
pip install poetry
poetry --version
poetry install
```

## 🛠️ Running the App

### Run API Server

```bash
poetry run python manage.py
```

### Run Test Case

Place your test case file (e.g., `create_backup_job_365.txt`) at `./storage/testcase/create_backup_job_365.txt`, then run:

```bash
poetry run flask process --testcase=create_backup_job_365.txt --mode=ai
```