# VoxGuard AI Project Explanation

This document provides a detailed breakdown of the VoxGuard AI project, its structure, workflow, and a file-by-file analysis of its functions and parameters.

## Project Overview
VoxGuard AI is an autonomous intelligence agent designed to monitor, transcribe, and analyze YouTube audio content. It leverages state-of-the-art AI models for speech-to-text, speaker identification, and natural language understanding to provide users with actionable intelligence reports and a searchable "neural memory" of all processed content.

## Workflow Detail
1. **Monitoring**: The `monitor.py` script periodically checks a list of YouTube channels for new uploads. 
2. **Ingestion**: When a new video is detected (or manually submitted via the dashboard), `ingestion.py` downloads the audio in WAV format.
3. **Perception**: The `PerceptionEngine` in `perception.py` performs speaker diarization (who is speaking when) and transcription (what is being said). It also calculates a "Trust Score" for each segment based on model confidence and noise levels.
4. **Intelligence**: The transcribed text is sent to the LLM (Llama 3.1 via Groq) in `intelligence.py`. For long videos, it uses a Map-Reduce strategy to summarize chunks before generating a final report.
5. **Memory & Persistence**: 
    - Full transcripts and reports are stored in a SQLite database (`database.py`).
    - Individual segments are vectorized and stored in a ChromaDB vector store (`memory.py`) for semantic search.
6. **Notification**: The final report is formatted into HTML and emailed to the user (`notifier.py`).
7. **User Interface**: A Streamlit dashboard (`dashboard.py`) provides a visual feed of reports, a search interface for the "neural memory," and a settings panel.

---

## File Breakdown

### 1. `main.py`
The orchestrator of the entire pipeline.
- **`extract_video_id(url: str)`**:
    - **Purpose**: Extracts the unique ID from a YouTube URL.
    - **Parameters**: `url` (The YouTube video URL).
- **`run_voxguard(youtube_url: str)`**:
    - **Purpose**: Executes the full ingestion-to-notification pipeline for a single video.
    - **Parameters**: `youtube_url` (The URL of the video to process).

### 2. `dashboard.py`
The Streamlit-based web interface.
- **Purpose**: Provides a frontend for users to interact with the agent, view analysis results, search through past videos, and configure settings.

### 3. `components/ingestion.py`
Handles fetching audio from external sources.
- **`download_audio(youtube_url: str, output_dir: str = "data")`**:
    - **Purpose**: Downloads the audio stream from YouTube and converts it to WAV.
    - **Parameters**: 
        - `youtube_url`: The URL of the video.
        - `output_dir`: The directory where the audio file will be saved.

### 4. `components/perception.py`
The core audio processing module.
- **`PerceptionEngine` (Class)**:
    - **`__init__()`**: Initializes the Whisper model and Pyannote speaker diarization pipeline.
    - **`analyze_audio(audio_path: str)`**:
        - **Purpose**: Transcribes the audio, identifies speakers, and calculates trust scores for each segment.
        - **Parameters**: `audio_path` (Path to the WAV file).

### 5. `components/intelligence.py`
The LLM-based analysis layer.
- **`chunk_transcript_text(text: str, chunk_size=6000)`**:
    - **Purpose**: Splits long transcripts into manageable chunks for the LLM.
- **`generate_report(video_title: str, segments: list)`**:
    - **Purpose**: Determines whether to use Single-Shot or Map-Reduce summarization based on transcript length and coordinates the report generation.
- **`_generate_single_shot(title, transcript, audit_log)`**:
    - **Purpose**: Generates a report in a single LLM call for shorter videos.
- **`_generate_map_reduce(title, transcript, audit_log)`**:
    - **Purpose**: Summarizes long transcripts by processing chunks individually and then synthesizing a final report.
- **`answer_user_query(query: str, context_chunks: list)`**:
    - **Purpose**: Uses RAG (Retrieval-Augmented Generation) to answer user questions based on retrieved transcript segments.

### 6. `components/database.py`
Handles structured data persistence using SQLAlchemy.
- **`VideoMemory` (SQLAlchemy Model)**: Defines the schema for storing video metadata, transcripts, and reports.
- **`get_video_by_id(video_id: str)`**:
    - **Purpose**: Checks if a video has already been processed.
- **`save_analysis(video_id, title, url, transcript, report, segments)`**:
    - **Purpose**: Commits the full analysis results to the SQL database.

### 7. `components/memory.py`
Handles the vector-based "Neural Memory."
- **`vector_store_segments(video_id: str, title: str, segments: list)`**:
    - **Purpose**: Converts transcript segments into embeddings and stores them in ChromaDB.
- **`query_memory(query_text: str, n_results=5)`**:
    - **Purpose**: Performs a semantic search against the stored transcript segments.

### 8. `components/monitor.py`
Handles automated channel monitoring.
- **`check_feeds()`**:
    - **Purpose**: Scans configured YouTube channels for new videos and triggers `run_voxguard` if any are found.
- **`start_scheduler()`**:
    - **Purpose**: Sets up a background job to run `check_feeds` every 6 hours.

### 9. `components/notifier.py`
Handles communication with the user.
- **`markdown_to_html(text)`**:
    - **Purpose**: Converts the LLM's markdown output into a styled HTML format for emails.
- **`send_alert(subject, markdown_body, video_title, video_url, dry_run)`**:
    - **Purpose**: Sends the intelligence report via Gmail SMTP.

### 10. `components/utils.py`
General utility functions.
- **`load_config()`**: Reads the `config.json` file.
- **`save_config(channels, email, smtp_password)`**: Updates the configuration file with user settings.
