# Neura OS: The OS That Just *Listens*

**Stop clicking menus and start talking.**

Neura OS is an AI-native shell that prototypes the end of traditional desktop interfaces. It is powered by our own LLM with 1.2 B+ parameters (sitee LLM).  We believe typing repetitive commands and clicking through menus is tedious. Neura OS replaces that friction by turning your voice and high-level intent into **immediate, executed action**. AND CODING AND SAVING THE FILES + SUMMARIZE AND COMPLETING YOUR ASSIGNMENTS!!

##  What Does It Do?

Neura OS is your personal desktop agent. You talk to it, and it **takes action** on your computer.

1.  **You Talk:** You ask for a complex task (e.g., "Set up a new React project, add a login component, and install Tailwind").
2.  **The Brain Thinks:** The AI engine orchestrates a plan and writes a multi-step Python script.
3.  **It Acts:** The system automatically executes the code, creating files, installing packages, and performing system operations—all from one voice command.

##  The Technical & Security Lineage

**Why isn't the whole OS here?** This is a critical question. The base assembly code is derived from the Debian operating system, making the full installation image large and sensitive.

For maximum security and clarity, this repository only contains the **Neura Lineage Code** and the UI shell. This showcases our actual innovation and allows the user to securely build the final Virtual Appliance locally, ensuring a **minimal attack surface** for the AI agent.

## 🛠️ Technology Stack

| Component | Technology | Human Role |
| :--- | :--- | :--- |
| **The Brain** | Python 3 + Flask | The core logic that thinks, plans, and manages execution. |
| **The Voice** | `PyAudio`, `espeak`, `flac` | Handles all the talking and listening functions. |
| **The Intelligence** | Sitee (https://www.instagram.com/sitee.in) (LLM) | Provides the ability to turn unstructured human requests into code. |
| **The Shell** | Debian (ARM64) + UTM | The secure, isolated sandbox where the code runs safely. |

## 🚀 Getting Started (Run the Future)

This project requires a secure environment (the VM) to run the code agent.

### Prerequisites

1.  A Mac with **Apple Silicon (M1/M2/M3)** or equavalent windows systems.
2.  **UTM** (Virtual Machine software) + Debian ARM64.
3.  **Node.js / npm** (For the Electron frontend).
4.  A **Fireworks AI API Key** for sitee (private).

## 🧑‍💻 Team

  * Jashanpreet Singh Dingra - Leader (BSc. Physics, Guru Nanak Dev University, Amritsar)
  * Himanshi Gupta (Btech CSE, tiet)
  * Harjot Singh (Btech AI/ML, tiet)
  * Gurleen Kaur (Btech CSE, tiet)
