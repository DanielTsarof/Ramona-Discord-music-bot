import os
from typing import List


def get_file_paths(dir_path: str) -> List[str]:
    '''Returns a list of paths to each file in the passed directory
    '''
    return [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]


def get_paths(dir_path: str, extension: str = 'jpg') -> List[str]:
    """
    function returns the paths to all files in the tree with the specified extension

    :param dir_path:
    :param extension:
    :return:
    """
    res_lst: List[str] = []
    for file in get_file_paths(dir_path):
        if file.endswith(extension):
            res_lst.append(file)
        elif os.path.isdir(file):
            res_lst.extend(get_paths(file, extension))
    return res_lst