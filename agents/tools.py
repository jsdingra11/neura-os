# /Users/astrodingra/Downloads/neura-os/agents/tools.py

import subprocess
from typing import Dict, Any, List # <-- FIXED: Explicitly imported List
import os
from memory_core import MemoryCore 
import time

# --- Initialize Memory Core Globally ---
# This instance is imported and used by the orchestrator AND the file watcher
NEURA_MEMORY = MemoryCore() 
# --- End Initialize ---


def execute_shell_command(command: str) -> Dict[str, Any]:
    """
    Executes a macOS/Linux shell command and returns the output.
    Use this tool ONLY to execute necessary commands like 'ls', 'pwd', 'cat', 'date', or 'echo'.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        # --- Memory Hook: Index new/modified files ---
        # This is a PROTOTYPE hook; the daemon handles real-time watching
        if ' > ' in command or ' >> ' in command: # Simple check for file creation/modification
            # Assume file is created/modified in current directory for simplicity
            file_name = command.split('>')[-1].strip().split()[0]
            if os.path.exists(file_name):
                with open(file_name, 'r') as f:
                    content = f.read(250)
                summary = f"Content Snippet: '{content.strip()}...'"
                
                # Add/update the document in memory
                NEURA_MEMORY.add_document(os.path.abspath(file_name), summary)
        # --- End Memory Hook ---

        return {
            "success": True,
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "command": command,
            "error": f"Command failed with code {e.returncode}. Stderr: {e.stderr.strip()}"
        }
    except Exception as e:
        return {"success": False, "command": command, "error": str(e)}


def semantic_file_search(query: str) -> List[dict]:
    """
    Searches the Neura memory (Vector Database) for file information semantically related to the query.
    Returns a list of relevant file paths and their summaries. 
    """
    return NEURA_MEMORY.semantic_search(query)