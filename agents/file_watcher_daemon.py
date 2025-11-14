# /Users/astrodingra/Downloads/neura-os/agents/file_watcher_daemon.py

#pipeline: watches for file changes and updates Neura's memory in real-time

import time
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# --- FIXED IMPORTS ---
from memory_core import MemoryCore, MEMORY_FILE, METADATA_FILE
# ---------------------

# Set up logging for the daemon
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Configuration ---
# WATCH_PATH: Watch the directory where the agent scripts are running
WATCH_PATH = os.path.expanduser((os.path.abspath(__file__))) 

# IGNORED_FILES: Ignore internal files to prevent infinite loops/corruption
IGNORED_FILES = [MEMORY_FILE, METADATA_FILE, '.env', 'venv'] 
# --- End Configuration ---


class NeuraFileHandler(FileSystemEventHandler):
    """
    Custom handler to process file system events and update Neura's memory.
    """
    def __init__(self, memory_instance):
        self.memory = memory_instance
    
    def _process_file(self, event):
        """Helper to handle create/modify events."""
        src_path = event.src_path
        
        # 1. Ignore directories and internal files
        if event.is_directory or any(f in os.path.basename(src_path) for f in IGNORED_FILES):
            return

        # 2. Get file content snippet for indexing
        try:
            with open(src_path, 'r') as f:
                content_snippet = f.read(250)
            
            summary = f"Content Snippet: '{content_snippet.strip()}...'"
            
            # 3. Add/Update memory
            # Uses the add_document function which handles vector creation and saving
            self.memory.add_document(src_path, summary)
            logging.info(f"Indexed/Updated: {os.path.basename(src_path)}")
            
        except UnicodeDecodeError:
            logging.warning(f"Skipped indexing binary file: {os.path.basename(src_path)}")
        except Exception as e:
            logging.error(f"Error processing {src_path}: {e}")

    # --- Event Hooks ---
    def on_created(self, event):
        self._process_file(event)

    def on_modified(self, event):
        self._process_file(event)

    def on_deleted(self, event):
        # NOTE: For simplicity, we only log deletions in the prototype.
        logging.info(f"Detected deletion: {os.path.basename(event.src_path)}")
    # --- End Event Hooks ---


if __name__ == "__main__":
    # Initialize the global MemoryCore instance for the daemon
    neura_memory_instance = MemoryCore() 
    
    event_handler = NeuraFileHandler(neura_memory_instance)
    observer = Observer()
    
    # Start watching the configured path
    observer.schedule(event_handler, WATCH_PATH, recursive=False)
    observer.start()

    print(f"\n[NEURA DAEMON] Starting File Watch on: {WATCH_PATH}")
    print("Press Ctrl+C to stop the daemon.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        
    observer.join()
    print("[NEURA DAEMON] Shut down.")