import os
import re
import sys

# Configuration
FORBIDDEN_STRINGS = [
    r"openai",
    r"gpt-4",
    r"gpt-3",
    r"grok",
    r"xai"
]

EXCLUDED_DIRS = [
    ".venv",
    "venv",
    "scripts",
    "tests",
    "node_modules",
    "__pycache__",
    ".git"
]

EXCLUDED_FILES = [
    "verify_mistral.py",
    "ai_client.py",
    "voice_agent.py"
]

def audit_file(file_path):
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in FORBIDDEN_STRINGS:
                if re.search(pattern, content, re.IGNORECASE):
                    # For agent.py, we allow the specific OpenAIChat import line
                    if "agent.py" in file_path and "agno.models.openai" in content and pattern.lower() == "openai":
                        # If there's only one occurrence and it's that import, it's okay
                        occurrences = len(re.findall(pattern, content, re.IGNORECASE))
                        if occurrences == 1:
                            continue
                    
                    issues.append(f"Forbidden pattern '{pattern}' found in {file_path}")
    except Exception as e:
        pass
    return issues

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_issues = []
    
    for root, dirs, files in os.walk(root_dir):
        # Filter directories to skip excluded ones
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if file.endswith('.py') and file not in EXCLUDED_FILES:
                file_path = os.path.join(root, file)
                all_issues.extend(audit_file(file_path))
                
    if all_issues:
        print("MISTRAL PURITY AUDIT FAILED:")
        for issue in all_issues:
            print(f"- {issue}")
        sys.exit(1)
    else:
        print("MISTRAL PURITY AUDIT PASSED: No OpenAI/Grok traces found in sanitized areas.")
        sys.exit(0)

if __name__ == "__main__":
    main()
