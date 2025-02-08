from pydub import AudioSegment
from pydub.silence import split_on_silence
from pathlib import Path
import ffmpeg
import tempfile
import shutil
import os

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

def apply_bandpass_filter(audio, low_freq=300, high_freq=3000):
    """
    Apply bandpass filter to audio
    
    Parameters:
        audio: AudioSegment object
        low_freq: Lower frequency cutoff in Hz
        high_freq: Higher frequency cutoff in Hz
    """
    # Apply lowpass and highpass filters in sequence to create a bandpass
    filtered_audio = audio.low_pass_filter(high_freq).high_pass_filter(low_freq)
    return filtered_audio

def process_audio(input_file, output_file, silence_threshold=-50, min_silence_len=500, 
                 pad_duration=100, low_freq=300, high_freq=3000):
    """
    Process audio file with bandpass filter and silence removal
    
    Parameters:
        input_file: Path to input audio file
        output_file: Path to save processed audio
        silence_threshold: in dB (negative values, where -50 is a moderate threshold)
        min_silence_len: minimum length of silence to detect (in milliseconds)
        pad_duration: amount of padding to keep around non-silent sections (in milliseconds)
        low_freq: Lower frequency cutoff for bandpass filter in Hz
        high_freq: Higher frequency cutoff for bandpass filter in Hz
    """
    # Create temporary copy of input file
    temp_input = tempfile.mktemp(suffix=Path(input_file).suffix)
    shutil.copy2(input_file, temp_input)
    
    try:
        # Convert input to MP3 if needed
        if temp_input.endswith(".mp4"):
            print("Converting to MP3")
            converted_file = convert_to_mp3(temp_input)
            Path(temp_input).unlink()
        else:
            converted_file = temp_input
            
        # Load audio file
        print("Loading audio file")
        audio = AudioSegment.from_file(converted_file)
        
        # Convert to mono and set sample rate
        print("Converting to mono and setting sample rate")
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Apply bandpass filter
        print(f"Applying bandpass filter ({low_freq}Hz - {high_freq}Hz)")
        filtered_audio = apply_bandpass_filter(audio, low_freq, high_freq)
        
        # Split on silence
        print("Detecting and removing silence")
        audio_segments = split_on_silence(
            filtered_audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_threshold,
            keep_silence=pad_duration
        )
        
        if not audio_segments:
            print("No non-silent segments found, returning filtered audio")
            processed_audio = filtered_audio
        else:
            # Concatenate non-silent segments
            print("Concatenating non-silent segments")
            processed_audio = sum(audio_segments, AudioSegment.empty())
        
        # Normalize audio
        print("Normalizing audio")
        normalized_audio = processed_audio.normalize()
        
        # Export
        print("Exporting processed audio")
        normalized_audio.export(
            output_file,
            format="mp3",
            parameters=["-ar", "16000", "-ac", "1", "-q:a", "2"]
        )
        
        print("Processing complete!")
        
    finally:
        # Clean up temporary files
        Path(converted_file).unlink()

if __name__ == "__main__":
    # input_file = "data/raw/audio_original/MP3 11-10-23.mp4"
    # output_file = "data/raw/audio_cleaned/FOUR.mp3"

    # Create output directory if it doesn't exist
    output_dir = "./data/raw/audio_cleaned"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process all MP3 and MP4 files in input directory
    input_dir = "./data/raw/audio_original"
    audio_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp3', '.mp4'))]
    
    if not audio_files:
        print("No MP3 or MP4 files found in input directory")
        exit()
    
    print(f"Found {len(audio_files)} audio files to process")
    
    for audio_file in audio_files:
        print(f"\nProcessing: {audio_file}")
        output_file = os.path.join(output_dir, f"{os.path.splitext(audio_file)[0]}.mp3")
        input_file = os.path.join(input_dir, audio_file)
        process_audio(
            input_file=input_file,
            output_file=output_file,
            silence_threshold=-40,    # Adjust based on your audio
            min_silence_len=2000,      # Minimum silence length in ms
            pad_duration=500,         # 500ms padding
            low_freq=200,             # Lower frequency cutoff in Hz
            high_freq=3000            # Higher frequency cutoff in Hz
        )