import subprocess
import re
import os

def convert_to_mp3(input_path, output_path):
    """Convert MP4 to MP3 using FFmpeg."""
    try:
        subprocess.run([
            "ffmpeg","-y", "-i", input_path, "-q:a", "2", "-acodec", "libmp3lame", output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def detect_silence(input_file, noise_db="-50dB", min_duration="0.5"):
    """Detect silence periods in an audio file using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-af", f"silencedetect=noise={noise_db}:d={min_duration}",
        "-f", "null",
        "-"
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    _, stderr = process.communicate()
    
    silence_starts = []
    silence_ends = []
    
    for line in stderr.split('\n'):
        if "silence_start" in line:
            match = re.search(r"silence_start:\s*([\d\.]+)", line)
            if match:
                silence_starts.append(float(match.group(1)))
        elif "silence_end" in line:
            match = re.search(r"silence_end:\s*([\d\.]+)", line)
            if match:
                silence_ends.append(float(match.group(1)))
    
    return list(zip(silence_starts, silence_ends))

def get_duration(input_file):
    """Get the duration of an audio file using ffmpeg."""
    cmd = ["ffmpeg","-y", "-i", input_file, "-f", "null", "-"]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    _, stderr = process.communicate()
    
    duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", stderr)
    if duration_match:
        hours, minutes, seconds = map(float, duration_match.groups())
        return hours * 3600 + minutes * 60 + seconds
    return None

def trim_audio(input_file, output_file, start_time, end_time):
    """Trim audio file between start_time and end_time."""
    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "panic",
        "-i", input_file,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",
        output_file
    ]
    subprocess.run(cmd)
    
def filter_audio(input_file, output_file):
    """Filter out noise from audio file using ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "panic",
        "-i", input_file,
        "-af", "highpass=f=200, anlmdn=s=2, afftdn=nf=-25, lowpass=f=3000",
        output_file
    ]
    subprocess.run(cmd)

def trim_silence(input_file, output_file, noise_db="-50dB", min_duration="2", padding=0.1):
    """Remove silence from audio file while keeping speech segments."""
    
    temp_file = "temp_file.mp3"
    filter_audio(input_file, temp_file) 
    silence_periods = detect_silence(temp_file, noise_db, min_duration)
    os.remove(temp_file)
    if not silence_periods:
        print(f"No silence detected in {input_file}")
        return False
    
    total_duration = get_duration(input_file)
    if total_duration is None:
        print(f"Could not determine duration for {input_file}")
        return False
    
    # Create segments of non-silence
    segments = []
    last_end = 0
    
    for start, end in silence_periods:
        if start - last_end > padding * 2:
            segment_start = max(0, last_end - padding)
            segment_end = min(start + padding, total_duration)
            segments.append((segment_start, segment_end))
        last_end = end
    
    # Add final segment if needed
    if total_duration - last_end > padding:
        segment_start = max(0, last_end - padding)
        segments.append((segment_start, total_duration))
        
    print("Found", len(segments), "silence segments.")
    
    # Create temporary directory for segments
    temp_dir = "temp_segments"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
    else:
        os.makedirs(temp_dir)
    
    # Create concat file and segments
    concat_file = os.path.join(temp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for i, (start, end) in enumerate(segments):
            segment_file = f"segment_{i}.mp3"
            segment_path = os.path.join(temp_dir, segment_file)
            trim_audio(input_file, segment_path, start, end)
            f.write(f"file '{segment_file}'\n")
    
    # Change to temp directory for concat operation
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    
    # Concatenate segments
    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "panic",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat.txt",
        "-c", "copy",
        os.path.join("..", output_file)
    ]
    subprocess.run(cmd)
    
    # Change back to original directory
    os.chdir(original_dir)
    
    # Clean up temporary files
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    return True

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    output_dir = "./data/raw/audio_trimmed"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process all MP3 and MP4 files in input directory
    input_dir = "./data/raw/audio_untrimmed"
    audio_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp3', '.mp4'))]
    
    if not audio_files:
        print("No MP3 or MP4 files found in input directory")
        exit()
    
    print(f"Found {len(audio_files)} audio files to process")
    
    for audio_file in audio_files:
        print(f"\nProcessing: {audio_file}")
        input_path = os.path.join(input_dir, audio_file)
        output_mp3_path = os.path.join(output_dir, f"{os.path.splitext(audio_file)[0]}.mp3")
        
        # Convert MP4 to MP3 if needed
        if audio_file.lower().endswith(".mp4"):
            print("converting", input_path, "to mp3" )
            if not convert_to_mp3(input_path, output_mp3_path):
                print(f"Failed to convert {audio_file} to MP3")
                continue
            input_path = output_mp3_path  # Use converted file for trimming
        
        success = trim_silence(
            input_path,
            output_mp3_path,
            noise_db="-45dB",
            min_duration="1",
            padding=0.1
        )
        
        if success:
            print(f"Successfully processed: {audio_file}")
        else:
            print(f"Failed to process: {audio_file}")
    
    print("\nProcessing complete!")
