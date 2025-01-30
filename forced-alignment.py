import os
from aeneas.executetask import ExecuteTask
from aeneas.task import Task

audio_folder = "data/raw/audio_trimmed"  # Replace with your actual path
text_folder = "data/raw/text"    # Replace with your actual path
srt_folder = "/data/raw/srt"      # Replace with your actual path

# Create srt folder if it doesn't exist
if not os.path.exists(srt_folder):
    os.makedirs(srt_folder)


# Configuration for Aeneas
config_string = u"task_language=eng|is_text_type=plain|os_task_file_format=srt"

# Iterate through audio files
for filename in os.listdir(audio_folder):
    if filename.endswith(".mp3"):
        audio_filepath = os.path.join(audio_folder, filename)
        text_filename = filename[:-4] + ".txt"  # Assuming text files have the same name
        text_filepath = os.path.join(text_folder, text_filename)
        srt_filepath = os.path.join(srt_folder, filename[:-4] + ".srt")

        # Check if corresponding text file exists
        if os.path.exists(text_filepath):
            print("processing...", audio_filepath)
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = audio_filepath
            task.text_file_path_absolute = text_filepath
            task.sync_map_file_path_absolute = srt_filepath

            try:
                ExecuteTask(task).execute()
                task.output_sync_map_file()
                print(f"Successfully processed {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
        else:
            print(f"Text file not found for {filename}")
