# SQLAlchemy Model Generation & Fix Guide

This document describes how to generate SQLAlchemy models and apply async relationship fixes in the CMS project.

---

## Prerequisites

- Python installed and added to PATH
- Required Python packages installed:
  ```bash
  pip install sqlacodegen psycopg2-binary psycopg2

## Step 1: Open Command Prompt (CMD Only)

⚠️ **Important**  
Use **Windows Command Prompt (CMD)** only.  
Do **not** use PowerShell, Git Bash, or any other terminal.

To open CMD:

- Press `Win + R`
- Type `cmd`
- Press **Enter**

---

## Step 2: Navigate to the CMS Root Directory

```bash
cd <path-to-bsfi-agents>
Example:
cd C:\Users\Ajaykumar.Bhukya\PycharmProjects\bfsi-agents
```

## Step 3: Generate SQLAlchemy Models

Run the following command to generate `models.py`:

```bash
sqlacodegen "postgresql+psycopg2://avnadmin:password@pg-22ef5b8a-ajaykumar.h.aivencloud.com:15549/defaultdb?sslmode=require" > models.py
```

## Step 4: Fix Async Relationships in Models

After generating the models, run the fix script:

Option 1: Use default models.py (same directory as script)
```bash
python .\tools\MYSQL\fix_async_models.py
```

Option 2: Provide a relative or absolute path to models.py

```bash
python .\tools\MYSQL\fix_async_models.py agents/intake_agent/src/models/model.py
 ```
or
```bash
python .\tools\MYSQL\fix_async_models.py C:\full\path\to\models.py
```
What the Fix Script Does:

- Scans the provided models.py

- Finds all relationship() definitions

- Adds lazy="selectin" where it is missing

- Prevents N+1 query issues in async usage

- Updates the file in place

Expected Output:
- ✅ Fixed relationships in resolved path to models.py


If an invalid path is provided, the script will fall back to the default models.py:

⚠️ File not found: <provided path>
➡️ Falling back to default models.py

Recommended Workflow

- Generate models using sqlacodegen

- Run fix_async_models.py

- Verify models.py