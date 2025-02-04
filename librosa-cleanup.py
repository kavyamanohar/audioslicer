import librosa
import numpy as np
import ffmpeg
import subprocess
import tempfile
from pathlib import Path
import math
import shutil

def convert_to_mp3(input_file):
    """Convert input file to MP3 using ffmpeg"""
    temp_mp3 = tempfile.mktemp(suffix='.mp3')
    try:
        (
            ffmpeg
            .input(input_file)
            .output(temp_mp3, acodec='libmp3lame', ar='16000', ac=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return temp_mp3
    except ffmpeg.Error as e:
        print(f"Error converting file: {e.stderr.decode()}")
        raise

def process_audio_chunk(y, sr, noise_thresh, silence_threshold=-50, min_silence_duration=1.0, pad_duration=0.1):
    """Process a single audio chunk"""
    S = librosa.stft(y)
    mag = np.abs(S)
    phase = np.angle(S)
    
    # Apply noise reduction
    mask = (mag > noise_thresh)
    mag_cleaned = mag * mask
    y_cleaned = librosa.istft(mag_cleaned * np.exp(1j * phase))
    
    # Silence removal with padding
    intervals = librosa.effects.split(
        y_cleaned,
        top_db=-silence_threshold,
        frame_length=2048,
        hop_length=512
    )
    
    # Add padding to intervals
    pad_samples = int(pad_duration * sr)
    padded_intervals = []
    
    for start, end in intervals:
        new_start = max(0, start - pad_samples)
        new_end = min(len(y_cleaned), end + pad_samples)
        
        if (new_end - new_start) / sr >= min_silence_duration:
            padded_intervals.append((new_start, new_end))
    
    # Merge overlapping intervals
    if padded_intervals:
        merged = [padded_intervals[0]]
        for current in padded_intervals[1:]:
            previous = merged[-1]
            if current[0] <= previous[1]:
                merged[-1] = (previous[0], max(previous[1], current[1]))
            else:
                merged.append(current)
        
        y_processed = np.concatenate([
            y_cleaned[start:end] for start, end in merged
        ])
    else:
        y_processed = np.zeros(int(0.1 * sr))
    
    return y_processed

def process_audio(input_file, output_file, chunk_duration=3600, target_sr=16000, 
                   silence_threshold=-50, min_silence_duration=1.0, pad_duration=0.1):
    """Process long audio file in chunks and concatenate"""
    # Create temporary copy of input file
    temp_input = tempfile.mktemp(suffix=Path(input_file).suffix)
    shutil.copy2(input_file, temp_input)
    
    # Convert input to MP3 if needed
    if temp_input.endswith(".mp4"):
        print("Converting to MP3")
        converted_file = convert_to_mp3(temp_input)
        Path(temp_input).unlink()  # Remove temporary input copy
    else:
        converted_file = temp_input
    
    try:
        # Load entire audio
        print("Loading Entire Audio")
        y, sr = librosa.load(converted_file, sr=target_sr, mono=True)
        
        # Estimate noise profile
        print("estimating noise profile from first 1 second of audio")
        n_fft = 2048
        y1 = y[:sr]
        S = librosa.stft(y1)
        mag = np.abs(S)
        phase = np.angle(S)
        noise_mag = mag[:, :int(sr/n_fft)]
        noise_thresh = np.mean(noise_mag, axis=1) * 2
        noise_thresh = noise_thresh.reshape(-1, 1)
        
        # Calculate chunk size
        print("Computing Chunk Size")
        chunk_samples = chunk_duration * sr
        num_chunks = math.ceil(len(y) / chunk_samples)
        
        # Process and store chunks
        processed_chunks = []
        for i in range(num_chunks):
            print(f"Processing chunk {i+1}/{num_chunks}")
            start = i * chunk_samples
            end = min((i + 1) * chunk_samples, len(y))
            chunk = y[start:end]
            
            processed_chunk = process_audio_chunk(
                chunk, sr, noise_thresh,
                silence_threshold, 
                min_silence_duration, 
                pad_duration
            )
            processed_chunks.append(processed_chunk)
        
        # Concatenate processed chunks
        y_processed = np.concatenate(processed_chunks)
        
        # Normalize and save
        y_processed = y_processed / np.max(np.abs(y_processed))
        audio_data = y_processed.astype(np.float32)
        
        # Save using ffmpeg
        process = (
            ffmpeg
            .input('pipe:', format='f32le', ar=str(target_sr), ac=1)
            .output(output_file, acodec='libmp3lame', ar=str(target_sr), q=2)
            .overwrite_output()
            .compile()
        )
        
        with subprocess.Popen(process, stdin=subprocess.PIPE) as p:
            try:
                p.stdin.write(audio_data.tobytes())
                p.stdin.close()
                p.wait()
            except BrokenPipeError:
                print("Error: FFmpeg process terminated unexpectedly")
                raise
        
        print("Processing complete!")
    
    finally:
        # Clean up only temporary files
        Path(converted_file).unlink()

# Example usage
if __name__ == "__main__":
    input_file = "MP3 14-03-2024.mp3"
    output_file = "processed_output.mp3"
    
    process_audio(
        input_file=input_file,
        output_file=output_file,
        chunk_duration=600,  # 10 minute chunks
        target_sr=16000,
        silence_threshold=-50,
        min_silence_duration=1.0,
        pad_duration=0.1
    )