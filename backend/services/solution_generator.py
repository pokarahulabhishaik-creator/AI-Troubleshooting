"""LLM Solution Generator Service.

Generates structured technical solutions grounded in RAG context.
Connects to an OpenAI-compatible LLM endpoint if configured in .env,
and provides a comprehensive grounded fallback solution if no API key is set.
"""

import os
import re
from typing import Dict, Any, List
import requests
from dotenv import load_dotenv

load_dotenv()


def is_valid_api_key(api_key: str) -> bool:
    """Checks whether the API key is non-empty and not a placeholder."""
    if not api_key:
        return False
    placeholders = {
        "your_key_here",
        "your_api_key_here",
        "placeholder",
        "none",
        "xxx",
        "<your_api_key_here>",
    }
    return api_key.strip().lower() not in placeholders and len(api_key.strip()) > 8


def generate_fallback_solution(
    error_text: str,
    classification: Dict[str, Any],
    diagnosis: Dict[str, Any],
    retrieved_documents: List[Dict[str, Any]]
) -> str:
    """Synthesizes a structured troubleshooting solution grounded in RAG retrieved docs.

    Follows the 6 mandatory sections:
    1. Problem explanation
    2. Likely cause
    3. Step-by-step solution
    4. Commands/code where required
    5. Verification step
    6. Prevention/tip
    """
    error_type = classification.get("error_type", "UnknownError")
    category = classification.get("category", "General")
    summary = diagnosis.get("summary", "")
    likely_causes = diagnosis.get("likely_causes", [])

    # Extract target entity if present (e.g. module name, filename, port)
    target_match = re.search(r"['\"]([^'\"]+)['\"]", error_text)
    target_entity = target_match.group(1) if target_match else ""

    # Check retrieved content for resolution steps
    doc_steps: List[str] = []
    doc_code_blocks: List[str] = []

    for doc in retrieved_documents:
        content = doc.get("content", "")
        # Extract code blocks
        codes = re.findall(r"```(?:bash|powershell|cmd|python)?\s*(.*?)```", content, re.DOTALL)
        for c in codes:
            clean_c = c.strip()
            if clean_c and clean_c not in doc_code_blocks:
                doc_code_blocks.append(clean_c)

        # Extract step lines (e.g. "### 1. ...", "1. ...")
        for line in content.split("\n"):
            line_str = line.strip()
            if re.match(r"^###?\s*\d+\.", line_str) or re.match(r"^\d+\.\s+\*\*", line_str):
                clean_step = re.sub(r"^#+\s*", "", line_str)
                if clean_step not in doc_steps:
                    doc_steps.append(clean_step)

    # 1. Problem Explanation
    explanation = (
        f"The error `{error_type}` occurred in the **{category}** domain. "
        f"{summary}"
    )

    # 2. Likely Cause
    causes_formatted = "\n".join([f"- {c}" for c in likely_causes[:3]]) or "- Configuration or path inconsistency."

    # 3. Step-by-Step Solution & 4. Commands
    if error_type == "ModuleNotFoundError":
        pkg = target_entity or "backend"
        solution_steps = (
            f"1. **Navigate to the Project Root Directory**:\n"
            f"   Ensure your shell is positioned in the repository root containing `{pkg}`.\n"
            f"2. **Activate the Virtual Environment**:\n"
            f"   Switch to the isolated environment where your project dependencies reside.\n"
            f"3. **Verify Package Existence & Structure**:\n"
            f"   Ensure `{pkg}` exists as a directory with Python files or `__init__.py`.\n"
            f"4. **Run Application with Module Flag (`-m`)**:\n"
            f"   Avoid executing nested scripts directly. Run via Python's module launcher from the root.\n"
            f"5. **Test the Import**:\n"
            f"   Execute a quick Python one-liner to verify that `{pkg}` can be loaded."
        )
        commands = (
            "```powershell\n"
            "# 1. Ensure project root directory\n"
            "cd /path/to/project_root\n\n"
            "# 2. Activate virtual environment (Windows)\n"
            ".\\venv\\Scripts\\Activate.ps1\n\n"
            "# 3. Test the import directly\n"
            f"python -c \"import {pkg}; print('Successfully imported {pkg}')\"\n\n"
            "# 4. Launch with module runner\n"
            f"python -m {pkg}.main\n"
            "```"
        )
        verification = (
            f"Run `python -c \"import {pkg}; print('OK')\"` in your terminal. "
            f"If it prints `OK` with exit code 0, the import resolution is verified."
        )
        prevention = (
            "Always run commands and servers from the project root using `python -m <module>`. "
            "Never `cd` into subpackages to run scripts directly, as this alters `sys.path[0]`."
        )

    elif error_type == "ImportError":
        solution_steps = (
            "1. **Check for Circular Dependencies**:\n"
            "   Look for bidirectional imports between modules (Module A importing Module B, which imports Module A).\n"
            "2. **Use Deferred / Local Imports**:\n"
            "   Move the offending import statement inside the specific function that uses it.\n"
            "3. **Eliminate File Shadowing**:\n"
            "   Ensure no local script in your project shares a name with standard libraries (e.g., `typing.py`, `random.py`).\n"
            "4. **Clear Bytecode Caches**:\n"
            "   Remove outdated `__pycache__` directories."
        )
        commands = (
            "```powershell\n"
            "# Clear compiled bytecode caches\n"
            "Get-ChildItem -Path . -Recurse -Filter '__pycache__' | Remove-Item -Recurse -Force\n\n"
            "# Test import directly\n"
            f"python -c \"import {target_entity or 'module'}; print('Import successful')\"\n"
            "```"
        )
        verification = "Run `python -m <entrypoint>` and verify that no circular import warnings or tracebacks occur."
        prevention = "Place shared schemas and data models in independent leaf modules (e.g., `models/schemas.py`)."

    elif error_type == "FileNotFoundError":
        solution_steps = (
            "1. **Verify Current Working Directory**:\n"
            "   Check `os.getcwd()` to see where Python is evaluating relative paths from.\n"
            "2. **Anchor Paths Using `pathlib.Path`**:\n"
            "   Construct paths relative to `__file__` rather than assuming relative working directory.\n"
            "3. **Check File Existence and Permissions**:\n"
            "   Confirm that the target file path exists on disk and has read access."
        )
        commands = (
            "```python\n"
            "from pathlib import Path\n\n"
            "# Safely anchor path relative to current script\n"
            "BASE_DIR = Path(__file__).resolve().parent\n"
            "target_file = BASE_DIR / 'data' / 'file.txt'\n"
            "print('Exists:', target_file.exists())\n"
            "```"
        )
        verification = "Check that `Path(target_file).exists()` evaluates to `True` before opening the resource."
        prevention = "Always use `pathlib.Path(__file__).resolve().parent` for internal project file references."

    elif "10048" in error_text or "Address already in use" in error_text:
        solution_steps = (
            "1. **Identify the Process Using the Port**:\n"
            "   Query network connections to find the process ID occupying the port (e.g., 8000).\n"
            "2. **Terminate the Conflicting Process**:\n"
            "   Stop the lingering process or service.\n"
            "3. **Alternative: Run on an Available Port**:\n"
            "   Launch the server on a different port like 8001 or 8080."
        )
        commands = (
            "```powershell\n"
            "# Find process using port 8000 on Windows\n"
            "Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess\n\n"
            "# Terminate the process (replace <PID> with the number from above)\n"
            "Stop-Process -Id <PID> -Force\n\n"
            "# Or start Uvicorn on another port\n"
            "python -m uvicorn backend.main:app --port 8001 --reload\n"
            "```"
        )
        verification = "Run `Test-NetConnection -Port 8000 -ComputerName 127.0.0.1` or visit the new port in your browser."
        prevention = "Always gracefully stop development servers using Ctrl+C instead of closing terminal windows abruptly."

    elif error_type in ("ConnectionError", "ConnectionRefusedError") or "10061" in error_text:
        solution_steps = (
            "1. **Start the Backend Service First**:\n"
            "   Ensure the FastAPI backend API is up and running before launching frontend clients.\n"
            "2. **Verify Host and Port Configuration**:\n"
            "   Confirm that the client URL matches the server URL (default `http://127.0.0.1:8000`).\n"
            "3. **Check Firewall & Localhost Permissions**:\n"
            "   Ensure local socket connections to 127.0.0.1 are allowed."
        )
        commands = (
            "```powershell\n"
            "# Start FastAPI backend in first terminal\n"
            "python -m uvicorn backend.main:app --reload\n\n"
            "# Check health in second terminal\n"
            "curl http://127.0.0.1:8000/health\n\n"
            "# Start Streamlit in second terminal\n"
            "python -m streamlit run frontend/app.py\n"
            "```"
        )
        verification = "Run `curl http://127.0.0.1:8000/health` or open the URL in your browser to verify a 200 OK status."
        prevention = "Implement retry mechanisms and informative error screens in frontend clients when the API is starting up."

    else:
        # Generic technical troubleshooting template grounded in retrieved documents
        if doc_steps:
            solution_steps = "\n".join(doc_steps[:5])
        else:
            solution_steps = (
                "1. **Inspect Error Details & Environment**:\n"
                "   Review the stack trace and check environment variables.\n"
                "2. **Validate Configuration & Dependencies**:\n"
                "   Ensure all necessary packages are installed and configuration parameters are valid.\n"
                "3. **Run from Project Root**:\n"
                "   Execute all CLI tools from the repository root."
            )
        commands = (
            "```powershell\n"
            + ("\n\n".join(doc_code_blocks[:2]) if doc_code_blocks else "pip check\npython -m pip install -r requirements.txt")
            + "\n```"
        )
        verification = "Re-run the command with debug or verbose logging enabled to verify clean execution."
        prevention = "Maintain an up-to-date requirements.txt and adhere to standard project layouts."

    # Combine into standard Markdown output
    solution_text = f"""### 1. Problem Explanation
{explanation}

### 2. Likely Cause
{causes_formatted}

### 3. Step-by-Step Solution
{solution_steps}

### 4. Commands / Code
{commands}

### 5. Verification Step
{verification}

### 6. Prevention & Best Practices
{prevention}"""

    return solution_text


def generate_solution(
    error_text: str,
    classification: Dict[str, Any],
    diagnosis: Dict[str, Any],
    retrieved_documents: List[Dict[str, Any]]
) -> str:
    """Generates a complete step-by-step solution using LLM with RAG context,

    or falls back gracefully to local RAG synthesis if LLM is unavailable.

    Args:
        error_text: Original error string.
        classification: Error classifier output.
        diagnosis: Grounded diagnosis output.
        retrieved_documents: Context chunks from RAG retriever.

    Returns:
        Structured step-by-step solution string in Markdown.
    """
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    # Check if a real LLM API key is configured
    if is_valid_api_key(api_key):
        try:
            # Build context from retrieved documents
            context_pieces = []
            for idx, doc in enumerate(retrieved_documents, 1):
                context_pieces.append(
                    f"--- Source {idx} ({doc.get('source', 'unknown')}) ---\n{doc.get('content', '')}"
                )
            context_str = "\n\n".join(context_pieces)

            system_prompt = (
                "You are an expert AI Technical Troubleshooting Assistant. "
                "Your role is to diagnose software errors and generate accurate, clear, and actionable step-by-step solutions.\n"
                "CRITICAL REQUIREMENTS:\n"
                "- Ground your answer in the provided RETRIEVED KNOWLEDGE BASE CONTEXT.\n"
                "- Do not hallucinate unsupported technical causes.\n"
                "- Structure your response strictly into these 6 numbered sections:\n"
                "  1. Problem Explanation\n"
                "  2. Likely Cause\n"
                "  3. Step-by-Step Solution\n"
                "  4. Commands / Code\n"
                "  5. Verification Step\n"
                "  6. Prevention & Best Practices\n"
                "- Use clean Markdown formatting."
            )

            user_prompt = (
                f"ERROR MESSAGE:\n{error_text}\n\n"
                f"CLASSIFICATION:\nType: {classification.get('error_type')}\nCategory: {classification.get('category')}\n\n"
                f"DIAGNOSIS SUMMARY:\n{diagnosis.get('summary')}\n"
                f"PROBABLE CAUSES:\n" + "\n".join(f"- {c}" for c in diagnosis.get("likely_causes", [])) + "\n\n"
                f"RETRIEVED KNOWLEDGE BASE CONTEXT:\n{context_str}\n\n"
                "Please generate the complete 6-part troubleshooting solution."
            )

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1500
            }

            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=25
            )

            if response.status_code == 200:
                res_data = response.json()
                content = res_data["choices"][0]["message"]["content"]
                if content and content.strip():
                    return content.strip()
            else:
                print(f"[LLM Warning] LLM request returned status {response.status_code}: {response.text[:150]}. Falling back.")

        except Exception as exc:
            print(f"[LLM Warning] Exception while calling LLM API: {exc}. Using RAG fallback solution.")

    # High quality RAG grounded fallback generator
    return generate_fallback_solution(
        error_text=error_text,
        classification=classification,
        diagnosis=diagnosis,
        retrieved_documents=retrieved_documents
    )


if __name__ == "__main__":
    from backend.rag.retriever import retrieve_documents
    from backend.services.error_classifier import classify_error
    from backend.services.diagnosis import diagnose_error

    err = "ModuleNotFoundError: No module named 'backend'"
    cls = classify_error(err)
    docs = retrieve_documents(err, top_k=2)
    diag = diagnose_error(err, cls, docs)
    sol = generate_solution(err, cls, diag, docs)
    print("Generated Solution:\n")
    print(sol)
