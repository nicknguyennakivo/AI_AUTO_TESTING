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

## 📖 Stagehand QA Test Prompt Standard

A standardized guide for QA engineers writing automated Stagehand tests. Designed to be stable, intention-driven, and idempotent.

### 1️⃣ Core Principles

1. Intent over mechanics
   - Describe what the test should do, not how to click it.
   - ❌ `Click checkbox "Enable backup"`
   - ✅ `Ensure "Enable backup" is selected.`

2. State over action
   - `Ensure` = setup / make sure state is correct  
   - `Expect` = assert / check state  
   - `Click` = only for discrete actions (button, link)

3. Idempotency
   - Steps should be safe to repeat without breaking the test.

4. Human-readable
   - Use labels or visible text, not DOM selectors.

### 2️⃣ Verb Usage

| Element Type | Verb / Template |
|--------------|------------------|
| Checkbox / Toggle | Ensure "<label>" is selected / not selected |
| Radio Button | Ensure radio option "<option>" is selected |
| Button | Click button "<label>" |
| Link | Click link "<label>" |
| Input / Text Field | Type "<text>" into "<field label>" |
| Dropdown | Select "<option>" from "<dropdown label>" |
| Menu / Accordion / Panel | Open "<name>" menu / section |
| Visibility / Assertion | Expect "<text>" is visible / not visible |
| Async / Wait | Wait until "<text>" is visible / not visible / state changes |

### 3️⃣ Checkbox / Toggle

- Select
```
Ensure checkbox "<label>" is selected.
```

- Unselect
```
Ensure checkbox "<label>" is not selected.
```

- Verify only
```
Expect checkbox "<label>" is selected.
```

> Do not use `Click` for checkboxes.

### 4️⃣ Buttons / Links

- Click action
```
Click button "<label>"
Click link "<label>"
```

- Assert state
```
Expect button "<label>" is enabled / disabled
```

### 5️⃣ Inputs / Text Fields

- Type
```
Type "<text>" into "<field label>"
```

- Clear before typing (if needed)
```
Clear "<field label>"
Type "<text>" into "<field label>"
```

### 6️⃣ Dropdowns / Select

- Select option
```
Select "<option>" from "<dropdown label>"
```

- Verify selection
```
Expect "<option>" is selected in "<dropdown label>"
```

### 7️⃣ Navigation / Menus / Panels

- Open menu / panel
```
Open the "<menu / panel name>"
```

- Expand accordion / section
```
Open section "<section name>"
```

> Use `Open` for stateful navigation, not `Click`.

### 8️⃣ Visibility / Assertions

- Expect visible
```
Expect "<text>" is visible.
```

- Expect not visible
```
Expect "<text>" is not visible.
```

- Expect exists
```
Expect "<text>" exists.
```

### 9️⃣ Async / Wait

- Wait until element appears
```
Wait until "<text>" is visible.
```

- Wait until element disappears
```
Wait until "<text>" is not visible.
```

- Wait until state changes
```
Wait until job status is not "Running".
```

### 🔟 Full Example

```
Type "admin" into "Username"
Type "admin" into "Password"
Click button "Log In"

Expect "Data Protection" is visible
Open the "Data Protection" menu
Click button "Create new job"

Expect "Backup for Microsoft 365" is visible
Select "Backup for Microsoft 365" from "Job type"
Click button "Next"

Ensure "Do not schedule, run on demand" is selected
Click button "Next"
Expect "Source" is visible
```

### ✅ Rules of Thumb

1. Use `Ensure` for setup, `Expect` for assertions, `Click` only for discrete actions.
2. Use labels / text, not selectors.
3. Steps should be idempotent.
4. Human-readable, intention-focused prompts improve AI reasoning.

---