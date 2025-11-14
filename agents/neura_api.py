import speech_recognition as sr
import pyttsx3
import requests
import time
import sys
import json
import os
import io
import contextlib # Used to capture print() statements from exec()

# --- Configuration ---
FIREWORK_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
FIREWORK_API_KEY = os.environ.get("FIREWORKS_API_KEY") 
FIREWORK_MODEL = "accounts/fireworks/sitee/sitee-0.0.7" # sitee LLM (private linkage might now work for you)

# --- NEW: General-Purpose Agent System Prompt ---
SYSTEM_PROMPT = """
You are 'Neura', an advanced AI desktop agent. Your primary purpose is to
accomplish tasks on the user's local machine by generating and executing
Python code. You are a 'doer', not just a 'talker'.

You MUST respond ONLY with a JSON object. Do not add any text
before or after the JSON.

You have two actions: "talk" and "execute_python".

1. "action": "talk"
   - Use this for general conversation, or if you cannot possibly
     fulfill the user's request with code.
   - Example: {"action": "talk", "response_text": "Hello, how can I help?"}

2. "action": "execute_python"
   - This is your main action. Use this for 99% of requests.
   - The user's request will be a task. You must write a Python 3
     script to accomplish it.
   - The code will be run via `exec()`.
   - **CRITICAL:** ALWAYS `import` any modules you need (e.g., `import os`).
   - **CRITICAL:** ALWAYS use `print()` statements in your code to
     provide feedback on what you are doing (e.g., `print(f"File {filename} created.")`).
     This is the *only* way the user will know what you did.
   - Your code string must be a single JSON-compatible string,
     with newlines as \\n.

---
TASK EXAMPLES:
User: "create a new website project"
AI:
{
  "action": "execute_python",
  "code_to_run": "import os\n\nprint('Creating project structure...')\nos.makedirs('my-website/css', exist_ok=True)\nos.makedirs('my-website/js', exist_ok=True)\n\nwith open('my-website/index.html', 'w') as f:\n    f.write('<h1>Welcome!</h1>')\n\nwith open('my-website/css/style.css', 'w') as f:\n    f.write('body { font-family: sans-serif; }')\n\nprint('Project 'my-website' created with index.html and style.css.')"
}

User: "add a new route to my flask app.py"
AI:
{
  "action": "execute_python",
  "code_to_run": "import os\n\ncode_to_add = \"\"\"\\n\\n@app.route('/new')\ndef new_route():\\n    return 'This is the new route!'\\n\"\"\"\n\nif os.path.exists('app.py'):\n    with open('app.py', 'a') as f:\n        f.write(code_to_add)\n    print('Added new route to app.py.')\nelse:\n    print('File app.py not found.')"
}

User: "what is the capital of France"
AI:
{
  "action": "talk",
  "response_text": "The capital of France is Paris."
}
---
Now, process the user's command.
"""

# --- Text-to-Speech (TTS) Function ---
def speak(text: str):
    """Speaks the given text using pyttsx3."""
    try:
        engine = pyttsx3.init() 
        engine.setProperty('rate', 210)
        engine.say(text)
        engine.runAndWait() 
    except Exception as e:
        print(f"[TTS ERROR] {e}")

# --- Speech-to-Text (STT) Function ---
def take_command():
    """Listens for a command and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[STT] Calibrating...")
        r.adjust_for_ambient_noise(source, duration=1.0) 
        speak("Listening...") 
        
        try:
            r.pause_threshold = 1.1  
            r.energy_threshold = 450 
            audio = r.listen(source, timeout=5, phrase_time_limit=5) 
        except sr.WaitTimeoutError:
            print("[STT] Timeout.")
            return "" 

    try:
        command = r.recognize_google(audio).lower()
        print(f"[STT] User said: {command}")
        return command
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""
    except Exception as e:
        print(f"[STT ERROR] {e}")
        return ""

# --- NEW: Code Execution Function ---
def execute_python_code(code_to_run: str):
    """
    Executes the string of Python code.
    Captures stdout and stderr and speaks them.
    """
    print(f"[ACTION] Executing code:\n{code_to_run}")
    
    # Use io.StringIO to capture print() statements
    code_output = io.StringIO()
    
    try:
        # Redirect stdout to our StringIO object
        with contextlib.redirect_stdout(code_output):
            # Execute the code
            exec(code_to_run)
        
        # Get the captured output
        output_str = code_output.getvalue()
        if output_str:
            print(f"[CODE OUTPUT] {output_str}")
            speak(output_str) # Speak the success message
        else:
            # If the code ran but didn't print, give a generic success
            print("[CODE OUTPUT] Executed successfully, no output.")
            speak("Task completed.")

    except Exception as e:
        # If the code fails, speak the error
        print(f"[CODE ERROR] {e}")
        speak(f"I ran into an error: {e}")

# --- MODIFIED Firework AI API Function ---
def get_ai_action(prompt: str) -> dict:
    """
    Calls the Firework AI API.
    The AI is instructed to return a JSON object (action).
    """
    if not FIREWORK_API_KEY:
        print("[CLIENT (Firework)] FAILED. FIREWORKS_API_KEY not set.")
        return {"action": "talk", "response_text": "My Firework API key is not set."}

    headers = {
        "Authorization": f"Bearer {FIREWORK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": FIREWORK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096, # Increased for larger code blocks
    }

    try:
        response = requests.post(
            FIREWORK_API_URL, 
            headers=headers, 
            json=payload,
            timeout=30.0 # Increased timeout for model
        )
        response.raise_for_status() 
        
        response_text = response.json()['choices'][0]['message']['content']
        print(f"[AI RAW RESPONSE] {response_text}")

        # The AI *must* return a valid JSON string.
        action_json = json.loads(response_text)
        return action_json

    except json.JSONDecodeError:
        print("[AI ERROR] AI did not return valid JSON.")
        return {"action": "talk", "response_text": "I had a system error. The AI did not return a valid command."}
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return {"action": "talk", "response_text": f"I ran into an API error: {e}"}


# --- NEW: Main Agent Loop ---
def run_voice_assistant():
    """
    The main agent loop.
    Gets a command, asks the AI for a JSON *action*, and executes it.
    """
    
    if not FIREWORK_API_KEY:
        print("="*50)
        print("WARNING: FIREWORKS_API_KEY is not set.")
        print("Set it as an environment variable to enable it.")
        print("="*50)

    print("--- Neura OS Agent (Gen-Purpose) Starting ---")
    speak("Neura agent is ready.")
    
    try:
        while True:
            # 1. Get voice command
            command = take_command()
            if not command:
                continue 

            # 2. Exit Condition
            if "stop listening" in command or "exit agent" in command:
                speak("Shutting down agent. Goodbye.")
                print("[CLIENT] Exiting loop.")
                break

            # 3. Get Action from AI
            print(f"[CLIENT] Getting AI action for: '{command}'")
            action_data = get_ai_action(command)
            
            if not action_data or not action_data.get("action"):
                speak("I'm sorry, the AI returned a blank action.")
                continue

            # 4. Execute the Action
            action = action_data.get("action")

            if action == "talk":
                speak(action_data.get("response_text", "I have nothing to say."))
            
            elif action == "execute_python":
                code = action_data.get("code_to_run")
                if code:
                    execute_python_code(code)
                else:
                    speak("The AI wanted to run code but didn't provide any.")
            
            else:
                speak(f"The AI returned an unknown action: {action}.")
            
            time.sleep(0.5) 

    except KeyboardInterrupt:
        print("\n[CLIENT] Shutting down agent.")
        sys.exit(0)


if __name__ == "__main__":
    run_voice_assistant()
