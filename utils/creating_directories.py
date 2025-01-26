import os

# Create csv directory
def create_directories():
    temp_files = './temp_files'

    if not os.path.exists(temp_files):
        try:
            os.mkdir(temp_files)
        except OSError:
            print('Creation of directory %s failed' %temp_files)

    result = './result'

    if not os.path.exists(result):
        try:
            os.mkdir(result)
        except OSError:
            print('Creation of directory %s failed' %result)
