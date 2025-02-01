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
│       │   ├── bajaj.mp3
│       │   └── data.mp3
│       └── srt
│           ├── bajaj.srt
│           └── data.srt
├── LICENSE
├── main.py
├── push_tohub.py
├── README.md
├── requirements.txt
└── src
    └──audio_slicer.py
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

* Place the audio in mp3/mp4 format in `.data/raw/audio_untrimmed` directory

```
python audio-cleanup.py
```

* Resultant trimmed audio will be palced in `.data/raw/audio_trimmed` in mp3 format

## How to slice

* Place the audio in mp3 format in `.data/raw/audio_trimmed` directory
* Place the subtitle of the audio in `data/raw/srt` directory
* Make sure every mp3 file has a matching transcript filename.

```
python main.py
```

* `.data/processed/corpus` directory stores the generated slices, by default in the `train` directory and associated metadata in jsonl format.
* Audio slices will be created and stored in test split, if you pass `test_contains=["TEST", "VALID"]` argument to `audio_slicing_pipeline`. If any audio file contains the string `test` or `valid` in the file name it will be in the test split of the corpus.
* If you have your huggingface_hub token stored locally, you can push the corpus sirectly to huggingface hub by:

```
python push_tohub.py
```

## DOCUMENTATION

https://kavyamanohar.gitbook.io/court-room-asr