import os

# EXAMPLE OF os.walk
# os.walk returns a generator, that creates a tuple of values (current_path, directories in current_path, files in current_path).
#
# Every time the generator is called it will follow each directory recursively until no further sub-directories are available from the initial directory that walk was called upon.
#
# As such,
#
# os.walk('C:\dir1\dir2\startdir').next()[0] # returns 'C:\dir1\dir2\startdir'
# os.walk('C:\dir1\dir2\startdir').next()[1] # returns all the dirs in 'C:\dir1\dir2\startdir'
# os.walk('C:\dir1\dir2\startdir').next()[2] # returns all the files in 'C:\dir1\dir2\startdir'


# Auto-clean the debug folder of empty text files.
def delete_empty_log_files(root_folder):
    for root, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.log'):
                file_path = os.path.join(root, filename)
                if os.path.getsize(file_path) == 0: # 0kb
                    os.remove(file_path)
                    print(f"Deleted empty file: {file_path}")


# Auto-clean the debug folder of empty text files.
def delete_zone_identifier_files(root_folder):
    for root, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.Identifier'):
                file_path = os.path.join(root, filename)
                if os.path.getsize(file_path) == 0: # 0kb
                    os.remove(file_path)
                    print(f"Deleted empty file: {file_path}")


