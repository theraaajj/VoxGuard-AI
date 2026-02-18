# The Agent/Analysis logic

import os
import time  # for rate limiting
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_text_splitters import RecursiveCharacterTextSplitter 

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

def chunk_transcript_text(text: str, chunk_size=6000): 
    """
    Splits a long string into smaller chunks.
    Default 6000 chars is roughly 1.5k tokens (safe for Free Tier).
    """
    chunks = []
    while len(text) > chunk_size:
        split_index = text.rfind('\n', 0, chunk_size)
        if split_index == -1:
            split_index = chunk_size
        
        chunks.append(text[:split_index])
        text = text[split_index:]
    
    chunks.append(text) 
    return chunks

def generate_report(video_title: str, segments: list):
    """
    Generates a professional Intelligence Report.
    Automatically switches between 'Single-Shot' and 'Map-Reduce' based on length.
    """
    print("🧠 Generating Intelligence Report...")

    # Prepare Audit Log
    suspicious_segments = [s for s in segments if s['status'] == "⚠️ Suspicious"]
    audit_log = "\n".join([f"- {s['start']:.1f}s: {s['speaker']} | Confidence {s['confidence']:.2f} (Flagged)" for s in suspicious_segments])
    
    if not audit_log:
        audit_log = "No acoustic anomalies detected."

    # Prepare Full Transcript
    transcript_text = "\n".join([f"[{s['start']:.1f}s] {s['speaker']}: {s['text']}" for s in segments])

    # Check Length & Dispatch Strategy 
    if len(transcript_text) < 15000:
        print(f"   Mode: Standard (Short Video - {len(transcript_text)} chars)")
        return _generate_single_shot(video_title, transcript_text, audit_log)
    else:
        print(f"   Mode: Map-Reduce (Long Video detected: {len(transcript_text)} chars)")
        return _generate_map_reduce(video_title, transcript_text, audit_log)


def _generate_single_shot(title, transcript, audit_log):
    """
    ADAPTIVE logic for shorter videos.
    """
    word_count = len(transcript.split())
    
    if word_count < 300: # Less than ~2 minutes
        length_instruction = "Concise 3-bullet summary."
        diarization_instruction = "Note: If the text sounds like a monologue, merge speakers into 'The Host'."
    else:
        length_instruction = "Comprehensive 5-7 bullet summary."
        diarization_instruction = "Distinguish between the Host and Guests clearly."

    prompt = ChatPromptTemplate.from_template(
        """
        You are VoxGuard, an autonomous AI intelligence agent.
        Your goal is to summarize audio content while strictly highlighting data integrity issues.
        CONSTRAINT: You are NOT the speaker. Do not refer to the speaker as "VoxGuard".

        VIDEO TITLE: {title}
        
        FULL TRANSCRIPT (WITH SPEAKER DIARIZATION):
        {transcript}

        AUDIT LOG (LOW CONFIDENCE SECTIONS):
        {audit_log}

        INSTRUCTIONS:
        Synthesize an Intelligence Report with these sections:

        1. **Executive Summary:** {length_instruction}
        2. **Key Arguments:** Detailed breakdown of the main points discussed.
        3. **Data Integrity Warnings:** - List specific timestamps from the Audit Log if they exist.
           - If Audit Log is empty, write: "✅ No audio quality issues detected."
        4. **Speaker Identification:** {diarization_instruction} Infer identities (e.g., "The Host", "The Guest"). 
        5. **Key Technical Terms:** List important concepts or jargon used.
        6. **Recommendations:** Actionable insights or takeaways for the viewer.

        Keep the tone professional, objective, and concise.
        """
    )
    chain = prompt | llm | StrOutputParser()
    
    try:
        return chain.invoke({
            "title": title,
            "transcript": transcript,
            "audit_log": audit_log,
            "length_instruction": length_instruction,
            "diarization_instruction": diarization_instruction # Passed correctly now
        })
    except Exception as e:
        return f"❌ Error in Single-Shot generation: {e}"

def _generate_map_reduce(title, transcript, audit_log):
    """New logic for LONG videos (Map-Reduce)."""
    
    # A. Chunk the transcript
    chunks = chunk_transcript_text(transcript)
    print(f"   Split into {len(chunks)} parts for processing.")
    
    # B. Map Phase (Summarize each chunk)
    map_prompt = ChatPromptTemplate.from_template(
        """
        Summarize this segment of a video transcript in bullet points.
        Capture key technical terms, arguments, and speaker names.
        
        TRANSCRIPT SEGMENT:
        {transcript_part}
        """
    )
    map_chain = map_prompt | llm | StrOutputParser()
    
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"   Processing Part {i+1}/{len(chunks)}...")
        try:
            summary = map_chain.invoke({"transcript_part": chunk})
            chunk_summaries.append(summary)
            
            # --- RATE LIMIT PROTECTION ---
            time.sleep(5) 
            
        except Exception as e:
            print(f"   ⚠️ Error summarizing part {i+1}: {e}")
            
    combined_summaries = "\n\n".join(chunk_summaries)
    
    # C. Reduce Phase (Final Report)
    reduce_prompt = ChatPromptTemplate.from_template(
        """
        You are VoxGuard, an AI analyst. Create a Final Intelligence Report from these section summaries.
        CONSTRAINT: You are NOT the speaker. Do not refer to the speaker as "VoxGuard".
        
        VIDEO TITLE: {title}
        
        SECTION SUMMARIES:
        {summaries}
        
        AUDIT LOG (LOW CONFIDENCE SECTIONS):
        {audit_log}
        
        INSTRUCTIONS:
        Synthesize an Intelligence Report with these sections:

        1. **Executive Summary:** High-level overview.
        2. **Key Arguments:** Consolidate the arguments from the summaries.
        3. **Data Integrity Warnings:** List entries from the Audit Log.
        4. **Speaker Identification:** Infer identities from the context.
        5. **Key Technical Terms:** Important vocabulary or concepts.
        6. **Recommendations:** Strategic takeaways or next steps.
        
        Keep the tone professional.
        """
    )
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    
    try:
        return reduce_chain.invoke({
            "title": title,
            "summaries": combined_summaries,
            "audit_log": audit_log
        })
    except Exception as e:
        return f"❌ Error in Map-Reduce generation: {e}"


def answer_user_query(query: str, context_chunks: list):
    """
    Synthesizes an answer from retrieved vector search chunks.
    """
    if not context_chunks:
        return "I found no relevant information in the video memory to answer this."
    
    print(f"🔍 RAG Debug - Analyzing {len(context_chunks)} chunks for query: '{query}'")

    context_text = ""
    for i, chunk in enumerate(context_chunks):
        context_text += f"--- EXCERPT {i+1} ---\n{chunk}\n"
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are an intelligent video analyst. 
        Synthesize an answer based on these transcript excerpts.
        
        RULES:
        1. **Connect the Dots:** Use reasoning to piece together the meaning.
        2. **Be Direct:** Answer the question directly.
        3. **Attribution:** Refer to the information as "the video mentions".
        4. If excerpts are irrelevant, say "The retrieved context does not contain the answer."

        USER QUESTION: {query}
        
        TRANSCRIPT EXCERPTS:
        {context}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    try:
        return chain.invoke({"query": query, "context": context_text})
    except Exception as e:
        return f"I couldn't generate an answer due to an error: {e}"


# Test Block
if __name__ == "__main__":
    # Mock data to test the LLM without re-running the heavy audio processing
    mock_segments = [
        {"start": 0.0, "end": 5.0, "text": "The Q3 revenue was 50 million.", "confidence": 0.95, "status": "✅ Verified"},
        {"start": 5.0, "end": 10.0, "text": "We expect... mumble... drop... percent.", "confidence": 0.40, "status": "⚠️ Suspicious"}
    ]
    
    print(generate_report("Test Financial Update", mock_segments))