import os
from collections import deque

import pandas as pd
from stanza.utils.conll import CoNLL
from extract_coords import *
from output_files import create_csv


def get_coords():
    filename = 'en_combined-ud-test-conj.conllu'
    genre = 'test'
    year = '0000'

    with open(os.getcwd() + '/eval/' + filename, mode='r', encoding='utf-8') as file:
        coordinations = []
        text = file.read()
        sents = text.split('\n\n')
        sents = deque(sents)
    for _ in tqdm(range(len(sents))):
        sent = sents.popleft()
        if sent: # do not process an empty string, the function below doesn't understand it
            conllu = CoNLL.conll2doc(input_str=sent)
            coordinations += extract_coords(conllu)

    create_csv(coordinations, genre=genre, year=year, source=f'text_{genre}_{year}.txt')
    os.rename(os.path.join(os.getcwd(), 'out_files', 'sud_test_0000.csv'), os.path.join(os.getcwd(), 'eval', 'sud-conj-test.csv'))


if 'sud-conj-test.csv' not in os.listdir('eval'):
    get_coords()

