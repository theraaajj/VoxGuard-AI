# This file defines schema (the "Shape" of data) and handles saving/loading.

import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Setup SQLite (The file will be created automatically)
DATABASE_URL = "sqlite:///./voxguard.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the "VideoMemory" Table
class VideoMemory(Base):
    __tablename__ = "video_memories"

    id = Column(String, primary_key=True, index=True) # YouTube Video ID
    title = Column(String)
    url = Column(String)
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # The Core Data
    transcript_text = Column(Text)  # Full raw text
    summary_report = Column(Text)   # The AI's final email/report
    
    # Metrics
    avg_confidence = Column(Float)
    lowest_confidence = Column(Float)
    is_flagged = Column(Boolean, default=False)   #True if "Suspicious" was found

# Create the tables (Run this once on import)
Base.metadata.create_all(bind=engine)



# Helper Functions 

def get_video_by_id(video_id: str):
    """Check if we have already processed this video."""
    db = SessionLocal()
    try:
        return db.query(VideoMemory).filter(VideoMemory.id == video_id).first()
    finally:
        db.close()

def save_analysis(video_id: str, title: str, url: str, transcript: str, report: str, segments: list):
    """Save the full analysis to the DB."""
    db = SessionLocal()
    
    # Calculate simple stats from the segments
    confidences = [s['confidence'] for s in segments]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    min_conf = min(confidences) if confidences else 0.0
    
    # Check if any segment was suspicious
    flagged = any(s['status'] == "⚠️ Suspicious" for s in segments)

    new_memory = VideoMemory(
        id=video_id,
        title=title,
        url=url,
        transcript_text=transcript,
        summary_report=report,
        avg_confidence=round(avg_conf, 2),
        lowest_confidence=round(min_conf, 2),
        is_flagged=flagged
    )
    
    try:
        db.add(new_memory)
        db.commit()
        print(f"💾 Memory Saved: {title} (Trust Score: {avg_conf:.2f})")
    except Exception as e:
        print(f"❌ Database Error: {e}")
        db.rollback()
    finally:
        db.close()