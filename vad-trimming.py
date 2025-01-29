import subprocess
import re
import json
import os

def detect_silence(input_file, noise_db="-50dB", min_duration="0.5"):
    """Detect silence periods in an audio file using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-af", f"silencedetect=noise={noise_db}:d={min_duration}",
        "-f", "null",
        "-"
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    _, stderr = process.communicate()
    
    print("\nRaw FFmpeg output:")
    print(stderr)
    
    silence_starts = []
    silence_ends = []
    
    for line in stderr.split('\n'):
        if "silence_start" in line:
            print(f"\nFound silence start line: {line}")
            match = re.search(r"silence_start:\s*([\d\.]+)", line)
            if match:
                silence_starts.append(float(match.group(1)))
                print(f"Extracted start time: {match.group(1)}")
        elif "silence_end" in line:
            print(f"\nFound silence end line: {line}")
            match = re.search(r"silence_end:\s*([\d\.]+)", line)
            if match:
                silence_ends.append(float(match.group(1)))
                print(f"Extracted end time: {match.group(1)}")
    
    print(f"\nFound {len(silence_starts)} silence starts: {silence_starts}")
    print(f"Found {len(silence_ends)} silence ends: {silence_ends}")
    
    return list(zip(silence_starts, silence_ends))

def get_duration(input_file):
    """Get the duration of an audio file using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-i", input_file,
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
    
    duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", stderr)
    if duration_match:
        hours, minutes, seconds = map(float, duration_match.groups())
        return hours * 3600 + minutes * 60 + seconds
    return None

def trim_audio(input_file, output_file, start_time, end_time):
    """Trim audio file between start_time and end_time."""
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-ss", str(start_time),
        "-to", str(end_time),
        "-c", "copy",
        output_file
    ]
    print(f"\nExecuting trim command: {' '.join(cmd)}")
    subprocess.run(cmd)

def trim_silence(input_file, output_file, noise_db="-50dB", min_duration="0.5", padding=0.1):
    """Remove silence from audio file while keeping speech segments."""
    print(f"\nProcessing {input_file}")
    print(f"Parameters: noise_db={noise_db}, min_duration={min_duration}, padding={padding}")
    
    # Get silence periods
    silence_periods = detect_silence(input_file, noise_db, min_duration)
    
    if not silence_periods:
        print("\nNo silence detected with current parameters")
        print("Try adjusting noise_db (e.g., -30dB, -40dB) or min_duration")
        return
    
    print(f"\nDetected {len(silence_periods)} silence periods: {silence_periods}")
    
    # Get audio duration
    total_duration = get_duration(input_file)
    if total_duration is None:
        print("Could not determine audio duration")
        return
    
    print(f"Total audio duration: {total_duration} seconds")
    
    # Create segments of non-silence
    segments = []
    last_end = 0
    
    for start, end in silence_periods:
        if start - last_end > padding * 2:  # Avoid creating tiny segments
            segment_start = max(0, last_end - padding)
            segment_end = min(start + padding, total_duration)
            segments.append((segment_start, segment_end))
            print(f"\nCreating segment: {segment_start:.2f}s to {segment_end:.2f}s")
        last_end = end
    
    # Add final segment if needed
    if total_duration - last_end > padding:
        segment_start = max(0, last_end - padding)
        segments.append((segment_start, total_duration))
        print(f"\nCreating final segment: {segment_start:.2f}s to {total_duration:.2f}s")
    
    print(f"\nTotal segments to create: {len(segments)}")
    
    # Create temporary directory for segments
    temp_dir = "temp_segments"
    if os.path.exists(temp_dir):
        # Clean up any existing temporary files
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
            # Write relative path to concat file
            f.write(f"file '{segment_file}'\n")
    
    # Change to temp directory for concat operation
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    
    # Concatenate segments
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", "concat.txt",
        "-c", "copy",
        os.path.join("..", output_file)
    ]
    print(f"\nExecuting final concat command: {' '.join(cmd)}")
    subprocess.run(cmd)
    
    # Change back to original directory
    os.chdir(original_dir)
    
    # Clean up temporary files
    print("\nCleaning up temporary files...")
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    print(f"\nProcessing complete. Output saved to: {output_file}")

if __name__ == "__main__":
    input_file = "ONE.mp3"
    output_file = "output_trimmed.mp3"
    
    trim_silence(
        input_file,
        output_file,
        noise_db="-50dB",
        min_duration="5",
        padding=0.1
    )
