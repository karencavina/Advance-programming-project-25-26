#Imports Section
'''Bringing in everything we need'''

import gzip #Reads and writes .gz compressed files

from typing import Iterable #We will use this for opening files and telling Python that they are strings

from dataclasses import dataclass #Skips defining the init method by having Python generate it for us

import pandas as pd #Helps with parsing information and building dataframes


#Creating DataBundle Class
''' This will help us organize the annotations'''

@dataclass(frozen=True) #Decorator that creates init method automatically
class DataBundle: #We create a class to act as a bundle that holds 3 dataframes
    terms_df: pd.DataFrame #Provides type hints
    edges_df: pd.DataFrame #Stores parent-child relationships
    annotations_df: pd.DataFrame #Stores annotations


#Opening Files
'''This opens the text file'''
'''The first return handles compressed files, the second non compressed ones'''

def _open_text_file(path: str) -> Iterable[str]: #Private method to open the file that specifies it is looking for strings
    if path.endswith(".gz"): #Checks if the file is compressed
        return gzip.open(path, mode="rt", encoding="utf-8", errors="replace")
    return open(path, mode="rt", encoding="utf-8", errors="replace")

'''mode="rt" means we are reading it as text'''
'''encoding="utf-8" tells the program how to interpret the tex (utf-8 is standard encoding)'''
'''errors="replace" replaces unreadable characters with a placeholder so the program does not crash'''

