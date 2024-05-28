import requests
import csv
import json
import os
import random
import numpy as np
from dir_path import *

def extract_wordlist(file_path):
    def extract_non_verbs(row):
        parts = [part for part in row.split('][') if part]

        noun_phrases = []

        for part in parts:

            part = part.strip('[]')
            word, pos = part.split('|')
            if not pos == "NP":
                continue
            # if word not in non_verbs and 'VP' not in pos and 'VB' not in pos and 'VBD' not in pos and 'VBG' not in pos and 'VBN' not in pos and 'VBP' not in pos and 'VBZ' not in pos:
            #     non_verbs.append(word)
            if word[:4] == "the ":
                word = word[4:]
            elif word[:2] == "a ":
                word = word[2:]
            elif word[:3] == "an ":
                word = word[3:]
            word = word.replace(" ", "_")
            noun_phrases.append(word)
        return noun_phrases
    wordlist = list()
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            last_column = row[-1]
            # Extract non-verb words
            non_verbs = extract_non_verbs(last_column)
            wordlist.append(non_verbs)
    return wordlist


