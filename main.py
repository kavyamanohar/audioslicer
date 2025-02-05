import os
import logging
from src.audio_slicer import audio_slicing_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

def create_data_directories():
    """Create necessary project directories"""
    directories = [
        'data/raw',
        'data/raw/audio_trimmed',
        'data/raw/srt',
        'data/processed',
        'data/processed/corpus'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Execute complete ASR data processing pipeline"""
    # Create required directories
    create_data_directories()

    # Audio Slicing and Metadata Generation
    audio_slicing_pipeline(
        audio_dir="data/raw/audio_cleaned",
        srt_dir="data/raw/srt",
        output_dir="data/processed/corpus",
        metadata_file="data/processed/corpus/metadata.jsonl",
        test_contains=["TWO"]
    )

if __name__ == "__main__":
    main()
