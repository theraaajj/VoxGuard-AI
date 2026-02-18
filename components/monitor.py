import time
import schedule
import yt_dlp
from components.database import get_video_by_id
from components.utils import load_config
from main import run_voxguard

def check_feeds():
    config = load_config()
    channels = config.get("channels", [])
    
    if not channels:
        print("📭 No channels configured.")
        return

    print(f"\n📡 Executing Deep Scan on {len(channels)} channels...")

    # Configure yt-dlp to just "look" at the playlist, not download
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # Don't download video, just get metadata
        'playlistend': 5,      # Only look at the 5 most recent videos
        'ignoreerrors': True,  # Don't crash on private videos
    }

    for channel_id in channels:
        clean_id = channel_id.strip()
        channel_url = f"https://www.youtube.com/channel/{clean_id}/videos"
        
        print(f"   🔎 Scanning: {clean_id}...")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # This fetches the JSON metadata of the channel page
                info = ydl.extract_info(channel_url, download=False)
                
                if not info or 'entries' not in info:
                    print(f"     ⚠️ No videos found. Channel ID might be invalid.")
                    continue
                
                # Getting the entries (yt-dlp gives them Newest -> Oldest)
                recent_videos = list(info['entries'])

                # Oldest -> Newest chronology
                for entry in reversed(recent_videos):
                    # yt-dlp flat extraction keys are slightly different
                    video_id = entry.get('id')
                    title = entry.get('title')
                    video_url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"

                    if not video_id: 
                        continue

                    # DUPLICATE CHECK
                    if get_video_by_id(video_id):
                        # print(f"     [SKIP] {title[:20]}...")
                        pass
                    else:
                        print(f"     [NEW] 🚨 Found: {title}")
                        print(f"     Triggering Pipeline...")
                        
                        run_voxguard(video_url)
                        
                        print("     ✅ Done.")
                        # Sleep briefly to be polite
                        time.sleep(5)

        except Exception as e:
            print(f"   ❌ Monitor Error: {e}")

def start_scheduler():
    print("="*50)
    print("   VOXGUARD WATCHTOWER ACTIVE")
    print("   Engine: yt-dlp (Bulletproof)")
    print("   Schedule: Every 6 Hours")
    print("="*50)
    
    check_feeds()
    schedule.every(6).hours.do(check_feeds)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()