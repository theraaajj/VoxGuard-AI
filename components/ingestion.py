import os
import yt_dlp

def download_audio(youtube_url: str, output_dir: str = "data"):
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Configure yt dlp for best audio quality and wav conversion
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"⬇️  Downloading metadata: {youtube_url}...")
            
            # Extract video information and download
            info = ydl.extract_info(youtube_url, download=True)
            
            # Capture the critical metadata
            video_id = info['id']
            video_title = info['title']
            
            # Construct the final file path
            file_path = os.path.join(output_dir, f"{video_id}.wav")
            
            print(f"✅ Download complete: {video_title}")
            
            # Return path, title, and ID for downstream use
            return file_path, video_title, video_id
            
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        # Return tuple of Nones on failure to match unpacking expectation
        return None, None, None

# Simple test block
if __name__ == "__main__":
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    download_audio(test_url)