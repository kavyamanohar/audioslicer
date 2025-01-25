import os

# Create csv directory
def create_directories():
    temp_files = './temp_files'

    if not os.path.exists(temp_files):
        try:
            os.mkdir(temp_files)
        except OSError:
            print('Creation of directory %s failed' %temp_files)

    sliced_audio = './sliced_audio'

    if not os.path.exists(sliced_audio):
        try:
            os.mkdir(sliced_audio)
        except OSError:
            print('Creation of directory %s failed' %sliced_audio)

    metadata = './metadata'

    if not os.path.exists(metadata):
        try:
            os.mkdir(metadata)
        except OSError:
            print('Creation of directory %s failed' %metadata)
