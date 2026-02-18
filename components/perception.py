import os
import numpy as np
import librosa
from faster_whisper import WhisperModel
import torch
import torchaudio
from pyannote.audio import Pipeline
from pyannote.core import Segment 
from dotenv import load_dotenv
from huggingface_hub import login

load_dotenv()

#configuration
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    print("⚠️ WARNING: HF_TOKEN is missing in .env file! Diarization will fail.")

MODEL_SIZE = "tiny"
COMPUTE_TYPE = "int8"


class PerceptionEngine:
    def __init__(self):
        print(f"Loading Whisper model ({MODEL_SIZE}) & Pyannote Speaker Diarization...")
        self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)

        # HuggingFace login
        if HF_TOKEN:
            login(token=HF_TOKEN)

        # Load Diarization (Speaker ID)
        try:
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
            )
            
            # Optimize for CPU if no GPU available
            if torch.cuda.is_available():
                self.diarization_pipeline.to(torch.device("cuda"))
        except Exception as e:
            print(f"⚠️ Diarization Pipeline failed to load: {e}")
            self.diarization_pipeline = None


    def analyze_audio(self, audio_path: str):
        """
        Runs the triple-pipeline: Speaker Diarization + Transcription + Signal Audit.
        Returns a list of 'Verified Segments' with speaker labels.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 1 Load Audio for Signal Processing (Librosa)
        print("📊 Loading audio for signal analysis...")
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Calculate distinct noise metrics
        rms_energy = librosa.feature.rms(y=y)[0]

        # 2 DIARIZATION [The Identity Layer]
        print("👥 Identifying speakers (Diarization)...")
        diarization = None
        
        if self.diarization_pipeline:
            try:
                # --- THE WINDOWS FIX ---
                # We bypass the 'AudioDecoder' crash by loading the file ourselves 
                # using torchaudio, which works reliably on Windows.
                
                # 1. Load the audio into a Tensor
                waveform, sample_rate = torchaudio.load(audio_path)
                
                # 2. Wrap it in a dictionary (Pyannote In-Memory format)
                audio_in_memory = {
                    "waveform": waveform, 
                    "sample_rate": sample_rate
                }
                
                # 3. Pass the dictionary instead of the file path
                diarization = self.diarization_pipeline(audio_in_memory)
                
            except Exception as e:
                print(f"⚠️ Diarization run failed (using fallback 'Speaker ?'): {e}")
                diarization = None
        else:
            print("⚠️ Skipping Diarization (Pipeline not loaded).")

        # 3 TRANSCRIBE (Whisper) [The Content Layer]
        print("🗣️  Transcribing...")
        segments, info = self.model.transcribe(audio_path, beam_size=5)

        verified_segments = []
        print(f"   Detected language: {info.language} (Probability: {info.language_probability:.2f})")

        for segment in segments:
            # The Cross-Modal Verification Logic
            
            # Assign Speaker (Who spoke the most during this segment?)
            speaker_label = "Speaker ??"
            
            if diarization:
                try:
                    # Use segment.start/end
                    t_segment = Segment(segment.start, segment.end)
                    
                    # Crop the diarization timeline to this text segment
                    overlap = diarization.crop(t_segment)
                    
                    # argmax() returns the label with the most duration in this crop
                    if len(overlap) > 0:
                        speaker_label = overlap.argmax() 
                except Exception:
                    pass # Keep default label if matching fails

            # Extract the noise profile
            # mapping the timestamp to the array index of the RMS signal
            start_frame = int(segment.start * sr / 512)
            end_frame = int(segment.end * sr / 512)
            
            # Safe indexing
            segment_noise = rms_energy[start_frame:end_frame]
            avg_noise = np.mean(segment_noise) if len(segment_noise) > 0 else 0.0

            # THE TRUST SCORE FORMULA
            """
            This further needs more scientific approach, intended in future scopes.!!!
            """
            confidence = np.exp(segment.avg_logprob) 
            trust_score = confidence * (1.0 - min(avg_noise, 0.5)) 
            status = "✅ Verified" if trust_score > 0.6 else "⚠️ Suspicious"

            verified_segments.append({
                "start": segment.start,
                "end": segment.end,
                "speaker": speaker_label,
                "text": segment.text.strip(),
                "confidence": round(confidence, 2),
                "noise_level": round(float(avg_noise), 3),
                "trust_score": round(trust_score, 2),
                "status": status
            })

            # Print concise progress
            print(f"[{segment.start:.1f}s] {speaker_label}: {segment.text[:40]}... ({status})")

        return verified_segments


# Test Block
if __name__ == "__main__":
    data_dir = "data"
    if not os.path.exists(data_dir):
         print("❌ Data folder not found.")
    else:
        wav_files = [f for f in os.listdir(data_dir) if f.endswith(".wav")]
        
        if wav_files:
            test_file = os.path.join(data_dir, wav_files[0])
            print(f"🧪 Testing on: {test_file}")
            
            engine = PerceptionEngine()
            results = engine.analyze_audio(test_file)
            
            print(f"\n✅ Completed! Analyzed {len(results)} segments.")
        else:
            print("❌ No .wav files found in data/ folder. Run ingestion.py first!")