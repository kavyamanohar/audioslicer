# Split audio according to information in srt-file.


This repo enables easy splitting of audio files based on the subtitle-info in srt-files and prepare audio corpus ready to be pushed to huggingface hub.

## Project Structure

```.
├── data
│   ├── processed
│   │   └── corpus
│   │       ├── metadata.jsonl
│   │       ├── test
│   │       └── train
│   └── raw
│       ├── audio
│       │   ├── audio1.mp3
│       │   └── audio2.mp3
│       └── srt
│           ├── audio1.srt
│           └── audio2.srt
├── audio-cleanup.py
├── forced-alignment.py
├──src
|   └──audio_slicer.py
├── main.py
├── push_tohub.py
├── LICENSE
├── README.md
└── requirements.txt
```

## Prerequisites

* [Python 3.6](https://www.python.org/)
* [pydub](https://pypi.org/project/pydub/)
* [datasets](https://pypi.org/project/datasets/)
* [soundfile](https://pypi.org/project/soundfile/)
* [librosa](https://pypi.org/project/librosa/)

## Setup
1. Clone repository
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`

## Trim Audio based on Voice Activity Detection

* Place the audio in mp3/mp4 format in `./data/raw/audio_original` directory

```
python audio-cleanup.py
```

* Resultant cleanedup audio will be placed in `./data/raw/audio_cleaned` in mp3 format

## Forced Alignment

* Ensure cleaned up audios are in  `./data/raw/audio_cleaned`
* Ensure the cleaned up transcripts created by https://github.com/kavyamanohar/pdf-to-transcript is placed in the `./data/raw/text` directory.
* Make sure every mp3 file has a matching transcript filename.


```
python forced-alignment.py
```

* The resultant time-stamps in `.srt` format is stored in `./data/raw/srt`

# How to slice

* Ensure the cleaned audio in mp3 format in `.data/raw/audio_cleaned` directory
* Ensure subtitle of the audio in `data/raw/srt` directory
* Make sure every mp3 file has a matching `.srt` filename.

```
python main.py
```

* `.data/processed/corpus` directory stores the generated slices, by default in the `train` directory and associated metadata in jsonl format.
* Audio slices will be created and stored in test split, if you pass `test_contains=["TESTFILE"]` argument to `audio_slicing_pipeline`. If any audio file contains the string `"TESTFILE"` in the file name it will be in the test split of the corpus.
* Metadata file for the slices are created in jsonline format.
* If you have your huggingface_hub token stored locally, you can push the corpus sirectly to huggingface hub by:

```
python push_tohub.py
```

## DOCUMENTATION

https://kavyamanohar.gitbook.io/court-room-asr