# 🧭 Stagehand Prompt Style Guide

A **stable, intention-driven prompt standard** for Stagehand UI automation.
Designed to be **idempotent**, **LLM-friendly**, and **low-flake**.

---

## 1️⃣ Core Principles (MUST FOLLOW)

### ✅ 1. Describe **INTENT**, not mechanics
❌ `Click checkbox "Enable backup"`  
✅ `Ensure "Enable backup" is selected.`

---

### ✅ 2. Prefer **STATE** over **ACTION**
State-based prompts are safe to retry.

| ❌ Avoid | ✅ Prefer |
|--------|----------|
| Click | Ensure |
| Toggle | Ensure |
| Select (checkbox) | Ensure |

---

### ✅ 3. Prompts must be **UI-agnostic**
Tests should survive:
- Checkbox → toggle
- Button → link
- DOM refactor

---

### ✅ 4. One prompt = one intent
❌ `Click Next and wait for Destination`

✅
```
Click button "Next"
Expect "Destination" is visible
```

---

## 2️⃣ Canonical Vocabulary

### 🔹 Action Verbs
- Click
- Type
- Select
- Open
- Close

### 🔹 State / Assertion Verbs
- Ensure
- Expect
- Wait until

---

## 3️⃣ Checkbox & Toggle Standard ⭐

### ✔️ Select checkbox
```
Ensure checkbox "<label>" is selected.
```

### ❌ Unselect checkbox
```
Ensure checkbox "<label>" is not selected.
```

### ✔️ Verify only
```
Expect checkbox "<label>" is selected.
```

### 🚫 Forbidden
```
Click checkbox "<label>"
Toggle "<label>"
```

---

## 4️⃣ Radio Button Standard

### Select option
```
Ensure radio option "<option>" is selected.
```

### Verify
```
Expect radio option "<option>" is selected.
```

---

## 5️⃣ Button Standard

### Click
```
Click button "<label>"
```

### Verify state
```
Expect button "<label>" is enabled.
Expect button "<label>" is disabled.
```

---

## 6️⃣ Input / Text Field Standard

### Type text
```
Type "<text>" into "<field label>"
```

### Clear then type (only if needed)
```
Clear "<field label>"
Type "<text>" into "<field label>"
```

---

## 7️⃣ Dropdown / Select Standard

### Select option
```
Select "<option>" from "<dropdown label>"
```

### Verify selection
```
Expect "<option>" is selected in "<dropdown label>"
```

---

## 8️⃣ Navigation & Menu Standard

### Open menu
```
Open the "<menu name>" menu.
```

### Expand section
```
Expand section "<section name>".
```

---

## 9️⃣ Visibility & Assertions

### Visible
```
Expect "<text>" is visible.
```

### Not visible
```
Expect "<text>" is not visible.
```

### Exists
```
Expect "<text>" exists.
```

---

## 🔟 Waiting / Async Handling

### Wait for appearance
```
Wait until "<text>" is visible.
```

### Wait for disappearance
```
Wait until "<text>" is not visible.
```

### Wait for state change
```
Wait until job status is not "Running".
```

---

## 1️⃣1️⃣ Table / List Standard

### Select item
```
Select item "<name>" from the list.
```

### Verify exists
```
Expect item "<name>" is visible in the list.
```

### Verify selected
```
Expect item "<name>" is selected.
```

---

## 1️⃣2️⃣ Messages & Errors

### Success message
```
Expect success message "<message>" is visible.
```

### Error message
```
Expect error message "<message>" is visible.
```

---

## 1️⃣3️⃣ Full Example (Best Practice)

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
```

---

## 🚫 Common Anti-Patterns

| Anti-pattern | Why |
|-------------|-----|
| Clicking checkboxes | Causes toggle bugs |
| Combined steps | Hard to debug |
| Selector-based prompts | Fragile |
| DOM-heavy language | Limits AI reasoning |

---

## 🏆 Golden Rules

1. **Ensure for setup, Expect for validation**
2. **Never click a checkbox**
3. **State > Action**
4. **Human language > DOM language**
5. **Idempotent steps only**

---
**Filename:** `stagehand-prompt-style-guide.md`