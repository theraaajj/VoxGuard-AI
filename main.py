import os
import sys

# Import components
from components.ingestion import download_audio
from components.perception import PerceptionEngine
from components.intelligence import generate_report
from components.database import save_analysis, get_video_by_id
from components.notifier import send_alert
from components.memory import vector_store_segments

def extract_video_id(url: str):
    # Fallback method to get ID from URL string
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    return "unknown_id"

def run_voxguard(youtube_url: str):
    # Initial ID extraction for logging
    temp_id = extract_video_id(youtube_url)

    print(f"\n🚀 VoxGuard Agent Activated for URL containing: {temp_id}")
    print("="*60)

    # 1. INGESTION
    # We now unpack three values: path, title, and ID
    audio_path, video_title, video_id = download_audio(youtube_url)
    
    # Check if download failed
    if not audio_path:
        print("❌ Pipeline failed at Ingestion.")
        return

    # 0. MEMORY CHECK (Moved after ingestion to use the real Video ID)
    # Check if we have processed this specific ID before
    if get_video_by_id(video_id):
        print(f"🧠 I remember '{video_title}'! Skipping processing.")
        # Cleanup the downloaded file since we don't need it
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return

    # 2. PERCEPTION
    try:
        engine = PerceptionEngine()
        # Analyze the audio file
        segments = engine.analyze_audio(audio_path)
    except Exception as e:
        print(f"❌ Pipeline failed at Perception: {e}")
        return

    # 3. INTELLIGENCE
    # Generate report using the REAL video title
    final_report = generate_report(video_title, segments)

    # 4. SAVE MEMORY
    full_transcript = " ".join([s['text'] for s in segments])
    save_analysis(video_id, video_title, youtube_url, full_transcript, final_report, segments)

    # 5. VECTORIZE & STORE
    vector_store_segments(video_id, video_title, segments)

    # 6. LIFECYCLE MANAGEMENT
    # Remove the large audio file to free up space
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f"🧹 Cleanup: Deleted temp audio {audio_path}")

    print("\n" + "="*60)
    print("📄 FINAL INTELLIGENCE REPORT")
    print("="*60)
    print(final_report)
    print("="*60)

    # 7. NOTIFICATION
    # Calculate how many suspicious segments were found
    flagged_count = sum(1 for s in segments if s['status'] == "⚠️ Suspicious")
    
    # The Subject Line for the Email Inbox (Urgent)
    subject_line = f"VoxGuard Intel: {video_title}"

    # Send the email
    send_alert(
        subject=subject_line, 
        markdown_body=final_report, 
        video_title=video_title, 
        video_url=youtube_url, 
        dry_run=False
    )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    run_voxguard(url)