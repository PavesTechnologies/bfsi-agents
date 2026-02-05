# OCR Setup Guide (Ollama + glm-ocr)

This document explains how to install **Ollama v0.15.5** and download the **`glm-ocr`** model for local OCR processing.

---

## Prerequisites

- **Operating System:** Windows 10 / 11 (64-bit)
- **RAM:** Minimum 8 GB recommended

  > ⚠️ `glm-ocr` requires ~3.5 GB of free system memory

- **Python:** 3.10+ (if integrating with FastAPI or other services)

---

## Step 1: Download and Install Ollama (v0.15.5)

1. Open your browser and go to the official Ollama releases page:

   ```
   https://github.com/ollama/ollama/releases
   ```

2. Download **Ollama v0.15.5 for Windows**:
   - File name similar to:

     ```
     OllamaSetup.exe
     ```

3. Run the installer and follow the on-screen steps.

4. After installation, open **PowerShell** and verify the version:

   ```powershell
   ollama --version
   ```

   Expected output:

   ```
   ollama version 0.15.5
   ```

---

## Step 2: Start the Ollama Service

Ollama runs as a background service automatically.

To verify it’s running:

```powershell
ollama list
```

If no models are installed yet, the list will be empty — this is expected.

---

## Step 3: Download the `glm-ocr` Model

Run the following command in PowerShell:

```powershell
ollama run glm-ocr
```

This will:

- Download the model weights
- Cache them locally
- Make the model available for OCR requests

> ⏳ The download may take several minutes depending on your network speed.

---

## Step 4: Verify Model Installation

List installed models:

```powershell
ollama list
```

You should see:

```
glm-ocr
```

---

## Step 5: Test the Model (Optional)

Run a quick interactive test:

```powershell
ollama run glm-ocr
```

If the model loads successfully, you’re ready to integrate it with your application.

---

## Common Issues & Notes

### ❗ Memory Error

If you see an error like:

```
model requires more system memory than is available
```

**Fixes:**

- Close other heavy applications
- Avoid running FastAPI with `--reload`
- Run with a single worker:

  ```bash
  uvicorn main:app --workers 1
  ```

---

### ❗ Model Not Found (404)

If you see:

```
model 'glm-ocr' not found
```

Make sure you have run:

```powershell
ollama pull glm-ocr
```

And confirm it appears in:

```powershell
ollama list
```

---

## Recommended Usage Notes

- Do **not** load OCR models in hot-reload environments
- Prefer preprocessing images before OCR to improve accuracy and reduce memory usage
- Catch Ollama runtime errors in production code to prevent service crashes

---

## Example Python Integration (Snippet)

```python
from ollama import chat

response = chat(
    model="glm-ocr",
    messages=[
        {
            "role": "user",
            "content": "Extract all readable text from this image.",
            "images": [image_base64],
        }
    ],
)

print(response.message.content)
```

---

## Summary

- ✅ Ollama version: **0.15.5**
- ✅ OCR model: **glm-ocr**
- ⚠️ Requires sufficient free RAM (~3.5 GB)
- 🚫 Avoid FastAPI reload mode with OCR models

---
