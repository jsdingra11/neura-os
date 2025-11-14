# /Users/astrodingra/Downloads/neura-os/agents/main_orchestrator.py

#purpose: to create new files or edit 

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Dict, Any 

# Import the necessary tools and the memory instance
from tools import execute_shell_command, semantic_file_search, NEURA_MEMORY 

# Load API key from .env file
load_dotenv()

# --- Helper Function for Robust Function Call Extraction ---
def get_function_calls(response: types.GenerateContentResponse) -> List[types.FunctionCall]:
    """Safely extracts all function calls from the model's response."""
    if not response.candidates:
        return []
        
    candidate = response.candidates[0]
    
    if not candidate.content or not candidate.content.parts:
        return []

    function_calls = []
    for part in candidate.content.parts:
        if part.function_call:
            function_calls.append(part.function_call)
            
    return function_calls
# --- End of Helper Function ---


# 1. System Role Prompt (The Neura OS Identity)
SYSTEM_ROLE = (
    "You are **Neura**, the central intelligence kernel of an autonomous macOS/Linux OS. "
    "Your core mission is to manage files, system resources, and answer user questions based on system memory. "
    "You have two tools: `execute_shell_command` for real-time system actions (like creating a file) "
    "and `semantic_file_search` for accessing long-term file knowledge. "
    
    "**RULE 1:** If the user asks a question about past actions or file content, you MUST use `semantic_file_search` first. "
    "**RULE 2:** If the user requests a system change (create, delete, list), use `execute_shell_command`. "
    "**RULE 3:** You MUST only output a final response to the user once the task is fully completed or verified. Be concise."
)

def run_neura_agent(user_prompt: str):
    # Initialize Gemini Client
    client = genai.Client()
    
    # Define the list of tools the AI can use 
    tools_list = [execute_shell_command, semantic_file_search]
    
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_prompt)])
    ]
    
    print(f"\n[NEURA] User Goal: {user_prompt}")
    
    # Set the system role and tools
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_ROLE,
        tools=tools_list
    )

    while True:
        # 1. Call the model with the current history and tool definitions
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=messages,
            config=config
        )

        # 2. Extract tool calls and prepare for next iteration
        function_calls = get_function_calls(response) 
        messages.append(response.candidates[0].content) 

        if function_calls:
            # --- ACTION REQUESTED ---
            function_call = function_calls[0]
            function_name = function_call.name
            args = dict(function_call.args)
            
            print(f"[NEURA] Thinking: Calling tool '{function_name}' with args: {args}")

            # Execute the actual Python function based on the requested name
            if function_name == "execute_shell_command":
                tool_result = execute_shell_command(**args)
            elif function_name == "semantic_file_search":
                tool_result = semantic_file_search(**args)
            else:
                tool_result = {"success": False, "error": f"Unknown tool: {function_name}"}

            print(f"[NEURA] Execution Result: Success={tool_result.get('success', 'N/A')}")
            
            # 3. Send the tool result back to the model for the next turn
            messages.append(
                types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(
                        name=function_name,
                        response=tool_result
                    )]
                )
            )

        # If no function call, the model has given the final text response
        else:
            print(f"\n[NEURA] Final Response: {response.text}")
            break

if __name__ == "__main__":
    # --- CRITICAL PRE-INDEXING STEP ---
    # This ensures files from previous runs are in memory BEFORE search tests.
    print("[INIT] Running pre-indexing of system files...")
    NEURA_MEMORY.pre_index_files()
    print("[INIT] Pre-indexing complete.")
    print("\n" + "=" * 60 + "\n")
    # ---------------------------------
    
    # Test 1: File creation (stores knowledge via the hook inside tools.py)
    run_neura_agent("Create a file named 'research_summary.txt' and put the text 'We need a full report on vector database search latency.' inside it.")
    
    print("\n" + "=" * 60 + "\n")
    
    # Test 2: Semantic Retrieval (The agent should now successfully retrieve memory)
    run_neura_agent("What files are related to the OS's internal design?")

    print("\n" + "=" * 60 + "\n")
    
    # Test 3: Simple Command (should use the shell command tool)
    run_neura_agent("List all text files in the current folder.")