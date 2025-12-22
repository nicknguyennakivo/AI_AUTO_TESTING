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

- [USAGE_GUIDE.md](./USAGE_GUIDE.md) - How to write test steps and run tests
- [NO_ACTION_INVENTION.md](./NO_ACTION_INVENTION.md) - **IMPORTANT: AI never invents steps not in steps.txt**
- [PRESS_ENTER_SUPPORT.md](./PRESS_ENTER_SUPPORT.md) - Support for keyboard actions (Press Enter, Tab, etc.)
- [HYBRID_EXECUTION_STRATEGY.md](./HYBRID_EXECUTION_STRATEGY.md) - Primary execution strategy with page.act()
- [AGENT_EXECUTE_FALLBACK.md](./AGENT_EXECUTE_FALLBACK.md) - Advanced agent.execute() fallback for recovery
- [AGENT_FALLBACK_VALIDATION_FIX.md](./AGENT_FALLBACK_VALIDATION_FIX.md) - Fix for fallback validation logic
- [AUTO_VERIFICATION_GUIDE.md](./AUTO_VERIFICATION_GUIDE.md) - Auto-verification feature
- [FIX_SILENT_FAILURES.md](./FIX_SILENT_FAILURES.md) - How failures are detected
- [AGENT_FALLBACK_GUIDE.md](./AGENT_FALLBACK_GUIDE.md) - Intelligent agent recovery overview
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions

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

> ⚠️ Requires [Poetry](https://python-poetry.org/docs/#installation)

```bash
sudo apt-get update && sudo apt-get install -y libpq-dev python3-dev build-essential

poetry install
```

## 🛠️ Running the App

### Run API Server

```bash
poetry run python manage.py
```