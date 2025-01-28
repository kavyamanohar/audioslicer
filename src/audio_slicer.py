import os
import json
import logging
from pydub import AudioSegment
import srt

def parse_srt(srt_path):
    """Parse SRT file and return list of segments with transcripts"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        subtitles = list(srt.parse(f.read()))
    
    return [
        {
            'start': subtitle.start.total_seconds() * 1000,
            'end': subtitle.end.total_seconds() * 1000,
            'text': subtitle.content
        } 
        for subtitle in subtitles
    ]

def slice_audio(audio_path, srt_path, output_dir, split, metadata):
    """
    Slice audio and collect metadata
    
    Args:
        audio_path (str): Path to input audio file
        srt_path (str): Path to SRT subtitle file
        output_dir (str): Directory to save sliced audio files
        split (str): Data split type (train, test, val, etc.)
        metadata (list): List to store segment metadata
    """
    os.makedirs(output_dir, exist_ok=True)
    audio = AudioSegment.from_mp3(audio_path)
    segments = parse_srt(srt_path)
    base_filename = os.path.splitext(os.path.basename(audio_path))[0]
    
    for i, segment in enumerate(segments, 1):
        try:
            # Slice audio segment
            sliced_audio = audio[segment['start']:segment['end']]
            
            # Calculate duration in seconds
            duration_seconds = len(sliced_audio) / 1000.0
            
            # Generate output filename
            output_name = f"{base_filename}-{i}.wav"
            output_filename = os.path.join(output_dir, output_name)
            
            # Export sliced audio
            sliced_audio.export(output_filename, format="wav")
            
            # Add metadata with split directory in file_name
            metadata.append({
                'file_name': os.path.join(split, output_name),
                'transcript': segment['text'].strip(),
                'duration': round(duration_seconds, 2)
            })
            
            logging.info(f"Exported: {output_filename} (Duration: {duration_seconds:.2f}s)")
        except Exception as e:
            logging.error(f"Failed to slice segment {i}: {e}")

def audio_slicing_pipeline(audio_dir, srt_dir, output_dir, metadata_file, test_contains=[]):
    """
    Process all audio files and generate metadata in JSONL format
    
    Args:
        audio_dir (str): Directory containing source audio files
        srt_dir (str): Directory containing SRT files
        output_dir (str): Base directory for output
        metadata_file (str): Path to save metadata JSONL file
        test_contains (list): List of strings contained in test split filenames 
    """
    metadata = []
    
    # Process audio files and collect metadata
    for srt_filename in os.listdir(srt_dir):
        if srt_filename.endswith('.srt'):
            base_filename = os.path.splitext(srt_filename)[0]
            audio_path = os.path.join(audio_dir, f"{base_filename}.mp3")
            srt_path = os.path.join(srt_dir, srt_filename)
            
            # Determine split based on filename
            current_split = "train"
            if any(test_str in srt_filename.lower() for test_str in test_contains):
                current_split = 'test'
                
            # Create split-specific output directory
            split_dir = os.path.join(output_dir, current_split)
            os.makedirs(split_dir, exist_ok=True)
                
            if os.path.exists(audio_path):
                slice_audio(audio_path, srt_path, split_dir, current_split, metadata)
            else:
                logging.warning(f"No audio file found for {srt_filename}")
    
    # Write metadata to JSONL file - each entry on a new line
    with open(metadata_file, 'w', encoding='utf-8') as f:
        for entry in metadata:
            json_line = json.dumps(entry)
            f.write(json_line + '\n')
    
    logging.info(f"Metadata saved to {metadata_file}")
