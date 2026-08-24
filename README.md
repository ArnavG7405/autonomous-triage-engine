# Autonomous Support Triage Engine

An enterprise-grade, autonomous AI triage engine designed to ingest, classify, and prioritize messy customer support tickets. 

Built with a hybrid architecture that combines **Deterministic NLP (Bayesian Noisy Channel)** for typo correction, **Pre-Inference Tool Routing (SQL/RAG)** for factual grounding, and **Llama 3 on Groq** for sub-second zero-shot classification. Engineered for production with graceful degradation, prompt-injection shields, and exponential backoff.

## Features
* **Zero-Shot JSON Triage:** Categorizes issues, assigns P0-P3 priority, and generates resolution summaries in `< 1.0s` per message.
* **Deterministic NLP Pre-processor:** Uses Levenshtein distance and Bayesian vocabularies to sanitize typos without wasting LLM tokens.
* **Autonomous RAG & DB Tooling:** Queries simulated internal databases and runbooks *before* triage to enforce factual accuracy.
* **Adversarial Shielding:** Fast-rejects prompt injections (`DROP TABLE`, etc.) to protect agent bandwidth.
* **Graceful Degradation:** Survives API rate limits and network drops without crashing, automatically flagging tickets for human review.

---

## Local Setup Instructions (Windows CMD)
Follow these steps to run the pipeline on your native Windows machine using the Command Prompt.

### 1. Prerequisites
* **Python 3.8+** installed and added to your system PATH.
* A free [Groq API Key](https://console.groq.com/keys).

### 2. Clone and Initialize
Open your Command Prompt (`cmd`), navigate to where you want to save the project, and run:
```cmd
git clone [https://github.com/ArnavG7405/autonomous-triage-engine.git](https://github.com/YOUR_USERNAME/autonomous-triage-engine.git)
cd autonomous-triage-engine
```

### 3. Create a Virtual Environment
Isolate the dependencies to keep your system clean:
```cmd
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 5.Set Your API Key
Get your Groq Api key from https://console.groq.com/keys

Set your Groq API key as an environment variable for the current session:
```cmd
set GROQ_API_KEY=gsk_your_actual_api_key_here
```

---

## Running the Engine (3 Modes)
The system is built to operate in three distinct modes. Make sure your virtual environment is activated and your API key is set before running these.

### Mode 1: Benchmark Evaluation Suite
Runs the engine against a hand-labeled ground-truth dataset to verify adversarial defense, translation, and overriding capabilities.
```cmd
python eval_suite.py
```


### Mode 2: High-Throughput Terminal Batch Processor
Streams an entire dataset (JSON, CSV, or TXT) through the pipeline, rendering a live terminal table and generating CSV/JSON artifact reports.
```cmd
python batch_runner.py dataset.json
```
Look for the highlighted "Tools Used" badges to see the pre-inference RAG/DB routing in action.


### Mode 3: Interactive Web Application
Launches a clean, dark-mode ready Streamlit UI. Features a Live Triage Simulator for single messages and a drag-and-drop Dataset Processor.
```cmd
streamlit run web_app.py
```
This will automatically open a local web server in your default browser at http://localhost:8501


---

## Project Structure
[engine.py] : The core LLM routing logic and exponential backoff network handlers.

[preprocessor.py] : The Bayesian typo-corrector and Fast-Reject injection shield.

[tools.py] : Deterministic pre-inference RAG knowledge base and SQL database simulator.

[auditor.py] : Post-inference deterministic guardrails (escalating legal/GDPR threats to P0).

[batch_runner.py] : Rich terminal UI and CSV artifact generator. Can handle original unseen dataset in all three formats (.txt, .csv, .json) 

[web_app.py] : Streamlit frontend application.
