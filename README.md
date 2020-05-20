This is adapted from this [project](https://github.com/sjoerdapp/SRT-to-CSV-and-audio-split) by  Tobias Rordorf. 

# Split audio according to information in srt-file.


This repo enables easy splitting of audio files based on the subtitle-info in srt-files and prepare corresponding transcript files.



## Prerequisites

* [Python 3.6](https://www.python.org/)
* [pydub](https://pypi.org/project/pydub/)

## How to slice

* Place the audio in wav format in `./audio` directory
* Place the subtitle of the audio in `./srt_files` directory

```
python slicer.py
```

* `./ready_for_slice` directory stores the start_time, end_time and the transcript in csv format
* sliced audio is saved in .`/sliced_audio` directory
* `/merged_csv` directory stores audio metadata as csv files
* `./final_csv` stores the sentences ready for language model training

## TODO

* Clean up transcript by removing punctuations and unwanted characters
