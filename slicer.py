import pandas as pd
import os, io, re, sys, time, datetime
from glob import glob
import numpy as np
import shutil
from utils.creating_directories import create_directories
from utils.convert_srt_to_csv import convert_srt_to_csv
from utils.slice_audio import split_files
from utils.create_DS_csv import create_DS_csv
from utils.merge_csv import merge_csv
from utils.merge_transcripts_and_files import merge_transcripts_and_wav_files


def main():

    start_time = time.time()

    #Check if srt_files directory exists and contains srt files

    srt_path = './srt_files'

    if os.path.exists(srt_path):
        print('Folder %s exists.. continuing processing..' %srt_path)
    else:
        print('Folder "srt_files" is missing')
        try:
            os.mkdir(srt_path)
        except OSError:
            print('Creation of directory %s failed' %srt_path)
        else:
            print('Successfully created the directory %s' %srt_path)
        print('--> Please add srt files to folder %s' %srt_path)
        sys.exit()

        #Check if audio directory exists and contains wmv or wav files

    audio_path = './audio/'

    if os.path.exists(audio_path):
        print('Folder %s exists.. continuing processing..' %audio_path)
    else:
        print('Folder "audio" is missing')
        try:
            os.mkdir(audio_path)
        except OSError:
            print('Creation of directory %s failed' %audio_path)
        else:
            print('Successfully created the directory %s' %audio_path)
        print('--> Please add wav or wmv files to folder %s' %audio_path)
        sys.exit()

    srt_counter = len(glob('./srt_files/' + '*.srt'))

    if srt_counter == 0:
        print('!!! Please add srt_file(s) to %s-folder' %srt_path)
        sys.exit()

    #Create directories
    print("Creating output directories")
    create_directories()


    # Extracting information from srt-files to csv
    print('Extracting information from srt_file(s) to csv_files')
    for file in glob('./srt_files/*.srt'):
        convert_srt_to_csv(file)
    print('%s-file(s) converted and saved as csv-files to ./temp_files' %srt_counter)
    print('---------------------------------------------------------------------')

    temp_files = './temp_files/'
    print("Copying audio files to ./temp_files")
    for file in os.listdir(audio_path):
            if(file.endswith('.wav')):
                shutil.copy(audio_path+file, temp_files+file )

    # Slicing audio
    print('Slicing audio according to start- and end_times of transcript_csvs...')
    for item in glob('./temp_files/*.csv'):
        print(item)
        wav_item = item.replace('.csv','.wav')
        print(wav_item)
        if os.path.exists(wav_item):
            split_files(item, wav_item)
        else:
           next
    wav_counter = len(glob('./sliced_audio/' + '*.wav'))
    print('Slicing complete. {} files in dir "sliced_audio"'.format(wav_counter))
    print('---------------------------------------------------------------------')


   #Now create list of filepaths and -size of dir ./sliced_audio
    create_DS_csv('./sliced_audio/')
    print('DS_csv with Filepaths - and sizes created.')
    print('---------------------------------------------------------------------')

    #now join all seperate csv files
    merge_csv('./temp_files/')
    print('Merged csv with all transcriptions created.')
    print('---------------------------------------------------------------------')
    #merge the csv with transcriptions and the file-csv with paths and sizes
    transcript_path = './metadata/Full_Transcript.csv'
    DS_path = './metadata/Filepath_Filesize.csv'
    merge_transcripts_and_wav_files(transcript_path, DS_path)
    print('Final DS csv generated.')
    print('---------------------------------------------------------------------')

    #evaluate the scripts execution time
    end_time = time.time()
    exec_time = str(datetime.timedelta(seconds=end_time-start_time))

    print('The script took {} to run'.format(exec_time))
    print('********************************************************************************************************')



if __name__ == "__main__":
    main()