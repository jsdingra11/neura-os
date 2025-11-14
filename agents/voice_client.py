import speech_recognition as sr
import pyttsx3
import requests
import time
import sys
import json

# --- Configuration ---
# Your Neura API server runs on port 5001
NEURA_API_URL = "http://localhost:5001/api/prompt" 

# --- Text-to-Speech (TTS) Function ---
def speak(text: str):
    """
    Initializes the engine, queues the text, and waits for it to finish speaking.
    CRITICAL: This uses the runAndWait() function to force the audio to play.
    """
    try:
        # Initializing inside the function ensures the engine is fresh for each output
        engine = pyttsx3.init() 
        
        # Optional: Adjust rate/volume for better results
        engine.setProperty('rate', 150)
        
        engine.say(text)
        
        # CRITICAL: Executes the audio queue and pauses until done
        engine.runAndWait() 
        
    except Exception as e:
        # Fallback print if TTS fails silently (e.g., PyAudio issue)
        print(f"[TTS ERROR] Could not speak '{text}'. Check PyAudio/system sound setup: {e}")

# --- Speech-to-Text (STT) Function ---
def take_command():
    """
    Listens to the microphone, adjusts for noise, and uses Google Speech Recognition 
    to convert audio to text.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        
        # 1. Calibration (CRITICAL for reliable STT)
        print("[STT] Calibrating ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1.0) # Listen for 1 second to set noise level
        
        speak("Listening...") 
        
        try:
            # 2. Set Timeouts for robust listening
            r.pause_threshold = 1.1  # Seconds of non-speaking to consider the phrase complete
            r.energy_threshold = 450 # Adjust sensitivity: lower is more sensitive, higher ignores background
            
            # Wait a maximum of 5 seconds for speech to start, and 5 seconds total for the phrase
            audio = r.listen(source, timeout=5, phrase_time_limit=5) 
            
        except sr.WaitTimeoutError:
            print("[STT] No speech detected within the timeout window.")
            return "" # Return empty command

    try:
        # 3. Transcribe using Google's STT
        command = r.recognize_google(audio).lower()
        print(f"[STT] User said: {command}")
        return command
        
    except sr.UnknownValueError:
        # This occurs if speech was captured but not recognized
        print("[STT] Speech captured but could not be understood.")
        speak("Sorry, I didn't catch that.")
        return ""
    except Exception as e:
        print(f"[STT ERROR] An unexpected error occurred during transcription: {e}")
        return ""

# --- Main Assistant Loop ---
def run_voice_assistant():
    """
    The main loop that controls the entire voice client process.
    """
    print("--- Neura OS Voice Client Starting ---")
    speak("Neura voice assistant ready.")
    
    # Wrap the entire loop in a try/except for a clean exit (Ctrl+C)
    try:
        while True:
            # 1. Get the command from the user
            command = take_command()

            if not command:
                continue # Go back to listening if nothing was transcribed

            # 2. Exit Condition (Voice Command)
            if "stop listening" in command or "exit assistant" in command:
                speak("Shutting down the voice client. Goodbye.")
                print("[CLIENT] Exiting loop due to voice command.")
                break

            # 3. Process Command (Send to API)
            print("[CLIENT] Sending command to Neura API...")
            
            try:
                response_json = requests.post(
                    NEURA_API_URL, 
                    json={"prompt": command}
                ).json()

                # DEBUG: Print the raw response to catch formatting errors
                print(f"[CLIENT DEBUG] Full API Response: {response_json}") 

                # 4. Handle API Response (CRITICAL FIX)
                if response_json.get('status') == 'success':
                    # Extract the actual response text; Fallback if the key is missing
                    ai_response = response_json.get('response_text', 'API text was found but the key was missing.')
                elif response_json.get('error'):
                    # The API sent a 400 or 500 error response
                    ai_response = f"API Error: {response_json['error']}"
                else:
                    # Unexpected format (e.g., empty response, or neither status/error key)
                    ai_response = "The Neura API returned an unexpected or empty response."

                print(f"[CLIENT] Final text to speak: {ai_response}")
                speak(ai_response)
                
            except requests.exceptions.ConnectionError:
                error_message = f"I could not connect to the Neura OS kernel on port 5001. Is neura_api.py running?"
                speak(error_message)
                print(f"[CLIENT ERROR] {error_message}")
            except Exception as e:
                error_message = "An unexpected error occurred while processing the command."
                speak(error_message)
                print(f"[CLIENT ERROR] General exception: {e}")
            
            # Small pause before the next listen cycle
            time.sleep(0.5) 

    except KeyboardInterrupt:
        print("\n[CLIENT] Shutting down voice client via Keyboard Interrupt.")
        sys.exit(0)


if __name__ == "__main__":
    run_voice_assistant()