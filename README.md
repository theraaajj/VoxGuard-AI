# 🛡️ VoxGuard AI: Autonomous Intelligence Agency

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![Llama 3.1](https://img.shields.io/badge/AI-Llama%203.1-orange?style=for-the-badge)
![Whisper](https://img.shields.io/badge/ASR-Faster--Whisper-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active%20Prototype-success?style=for-the-badge)

**VoxGuard** is an autonomous open-source intelligence agency that monitors YouTube channels 24/7. It acts as a personal analyst that automatically detects new video uploads, analyzes their audio for "truth & trust" signals, and generates executive intelligence briefings using **Llama 3.1**.

Built for analysts, researchers, and content moderators, VoxGuard serves as a persistent "watchtower," converting raw audio into structured intelligence reports and allowing users to query the "memory" of processed videos using semantic search.

> **Mission:** To provide high-level intelligence summaries and data integrity warnings for geopolitical and technical content, filtering out noise, clickbait, and detecting audio anomalies.

---

## 🛠️ Tech Stack

This project leverages a high-performance stack for real-time media processing and AI analysis.

### **Core AI & Processing**
* **Groq API (Llama 3.1-8b):** Ultra-low latency LLM inference for generating summaries and detecting logical fallacies.
* **Faster-Whisper:** A highly optimized implementation of OpenAI's Whisper model (using CTranslate2) for transcription speeds up to 4x faster than real-time.
* **Pyannote.Audio:** For speaker diarization (identifying *who* is speaking).
* **Librosa:** For digital signal processing (DSP), specifically measuring RMS energy and noise floors to calculate "Trust Scores."
* **yt-dlp:** The robust backbone for extracting video metadata and handling YouTube's "Consent" cookies without downloading heavy video files.

### **Backend & Infrastructure**
* **Python 3.9+:** The core runtime environment.
* **SQLite / PostgreSQL:** Hybrid database support. Uses SQLite for local development and supports PostgreSQL (Supabase) for cloud deployment.
* **ChromaDB:** A vector database used to store verified transcript segments, enabling the "RAG" (Retrieval-Augmented Generation) chat feature.
* **Streamlit:** The interactive dashboard for visualizing data and querying the agent.

---

## 🏗️ Architecture & Data Flow

VoxGuard operates as an autonomous pipeline consisting of four distinct agents that hand off data in a linear flow:

1.  **The Watchtower (Monitor Agent):**
    * **Trigger:** Runs on a scheduled cron job (every 6 hours).
    * **Action:** Scans specific YouTube Channel IDs using `yt-dlp` (flat extraction).
    * **Logic:** Compares found video IDs against the local database to filter out duplicates.
    * **Handoff:** Passes new video URLs to the Perception Engine.

2.  **The Perception Engine (The Ears):**
    * **Action:** Downloads audio streams (m4a/webm) into memory.
    * **Transcription:** Converts audio to text using `faster-whisper` (int8 quantization).
    * **Signal Analysis & Trust Score:** We don't just transcribe; we validate. The system computes a "Trust Score" using the formula:
        `Trust Score = Model_Confidence * (1.0 - Audio_Noise)`
        *High noise correlates with low-effort content. By penalizing high-noise sections, the agent flags "Suspicious" segments where transcription might be unreliable.*

3.  **The Analyst (The Brain):**
    * **Logic:** Uses an adaptive **Map-Reduce** strategy based on video length.
        * *Short Videos (<15k chars):* Single-shot prompt to Llama 3.1.
        * *Long Videos (>15k chars):* Splits text into 1.5k token chunks, summarizes each via "Map" step, and synthesizes a final report via "Reduce" step.
    * **Constraint:** Strictly instructed to separate the AI's identity from the speaker's identity to prevent hallucinations.

4.  **The Notifier (The Deliverer):**
    * **Action:** Formats the final intelligence report into an HTML email.
    * **Delivery:** Sends via SMTP (Gmail) directly to the user's inbox with a clean, professional header.

5.  **The Memory (RAG System):**
    * **Storage:** Stores verified transcript segments in a local ChromaDB vector database.
    * **Recall:** Allows users to chat with the agent (e.g., *"What did the CEO say about Q3 revenue?"*) to retrieve exact quotes across the entire video history.

---

## 🧠 Engineering Decisions & Trade-offs

Building a local, multi-modal AI agent comes with significant engineering challenges. Here is the reasoning behind specific architectural choices:

### 1. The "Windows-Specific" Diarization Fix
* **Challenge:** `Pyannote.Audio` is notorious for failing on Windows due to `libsndfile` driver issues when loading audio paths directly.
* **Solution:** Implemented a custom "In-Memory" loading pipeline. Instead of letting Pyannote open files, we use `torchaudio` (which is robust on Windows) to load the waveform into a Tensor, then pass that dictionary directly to the pipeline.
* **Trade-off:** Slightly higher memory usage during the loading phase, but ensures cross-platform stability.

### 2. Map-Reduce for Long Contexts
* **Challenge:** Passing a 2-hour podcast transcript to an LLM often exceeds context windows or degrades reasoning quality ("lost in the middle" phenomenon).
* **Solution:** The `intelligence.py` module detects video length. If it exceeds 15k characters, it triggers a Map-Reduce workflow:
    * *Map:* Breaks the text into 6,000-character chunks and summarizes them individually.
    * *Reduce:* Synthesizes the chunk summaries into a final comprehensive report.
* **Benefit:** Guarantees no detail is lost, regardless of video length, while keeping API costs predictable.

### 3. `yt-dlp` over YouTube Data API
* **Decision:** We strictly use `yt-dlp` for both monitoring and downloading.
* **Reasoning:** The official YouTube Data API has strict quotas (10k units/day). A continuous monitoring agent would hit this limit within hours. `yt-dlp` allows for "Flat Extraction" (scraping metadata without downloading video) which is lightweight, unlimited, and resilient to API key rotations.

---

## ⚠️ Challenges & Edge Cases

* **Hallucination in Diarization:** Sometimes Pyannote struggles to distinguish speakers with similar timbres. The "Merge Speakers" prompt instruction in `intelligence.py` helps mitigate this by asking the LLM to infer logic based on context.
* **YouTube Anti-Botting:** Streaming platforms frequently change their DOM layout. The system uses specific `yt-dlp` configurations (`ignoreerrors=True`, `sleep_interval`) to be polite and avoid IP bans.
* **Private/Deleted Videos:** The pipeline includes robust `try/except` blocks at the Ingestion layer. If a video is deleted midway, the agent logs the error and cleans up partial temp files to save disk space.

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.9+
* [FFmpeg](https://ffmpeg.org/download.html) installed and added to system PATH.
* A Groq API Key (for LLM reasoning).
* HuggingFace Token (for Pyannote separation).

### 1. Clone & Install
```bash
git clone [https://github.com/theraaajj/VoxGuard-AI.git](https://github.com/theraaajj/VoxGuard-AI.git)
cd VoxGuard-AI
pip install -r requirements.txt
```
### 2. Configure Environment
Create a `.env` file in the root directory:
```bash
GROQ_API_KEY=your_groq_key_here
HF_TOKEN=your_huggingface_token_here
DATABASE_URL=postgresql://... (Optional: leave blank for local SQLite)
```

### 3. Configure Channels
Create a `config.json` file for your channels and email settings:
```bash
{
    "channels": [
        "UCsDTy8jvHcwMvSZf_JGi-FA", 
        "UCqoAEDirJPjEUFcF2FklnBA"
    ],
    "email_to": "your_email@gmail.com",
    "smtp_password": "your-app-password"
}
```

---

## 🖥️ Usage
### Run the Dashboard (UI)
To view analyzed videos, read reports, and query the vector database:
```bash
streamlit run dashboard.py
```

### Run the Monitor (Background Agent)
To start the autonomous background scheduling loop:
```bash
python components/monitor.py
```

### Manual Trigger (Testing)
To force-analyze a specific video immediately without waiting for the scheduler:
```bash
python main.py "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)"
```

---

## Future Roadmap

* **Visual Analysis:** Integrating OpenCV to extract text (OCR) from video frames (e.g., presentation slides) to augment audio transcripts.
* **Multi-Agent Debate:** Having two LLM agents analyze the same transcript from different perspectives (e.g., "Skeptic" vs "Optimist") to reduce bias in the final report.

* ---

## 📂 Project Structure

```text
voxguard/
├── components/
│   ├── monitor.py       # The Watchdog: Scheduled scanner for new YouTube videos
│   ├── ingestion.py     # The Collector: Handles video downloading via yt-dlp
│   ├── perception.py    # The Ears: Transcription (Whisper) & signal analysis
│   ├── intelligence.py  # The Brain: Llama 3.1 summarization & map-reduce logic
│   ├── memory.py        # The Memory: Vector DB (ChromaDB) management for RAG
│   ├── notifier.py      # The Messenger: Email formatting & dispatch system
│   ├── database.py      # The Ledger: SQLite/PostgreSQL metadata abstraction
│   └── utils.py         # Shared utilities & configuration loaders
├── data/                # Temporary storage for downloading audio files
├── voxguard_vectors/    # Persistent vector database storage (ChromaDB)
├── dashboard.py         # Streamlit User Interface
├── main.py              # CLI Orchestrator for manual triggers
├── requirements.txt     # Python dependencies
└── config.example.json  # Template for channel configuration
  ```
