from datetime import datetime
import argparse
from stanza.utils.conll import CoNLL
from collections import deque

from preprocessing import *
from extract_coords import *
from output_files import *


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', nargs='+') # list files to be processed
arg_parser.add_argument('-p', action='store_true') # parsed flag, if the input are conllu files
arg_parser.add_argument('-d', action='store_true') # processes the whole directory
args = arg_parser.parse_args()


def run(filename):
    if args.p:
        print('loading the .conllu file...')
        s = datetime.now()
        doc = CoNLL.conll2doc(os.getcwd() + '/test_files/' + filename)
        e = datetime.now()
        print('loaded, that took ' + str(e - s))

        genre = re.search('acad|news|fic|mag|blog|web|tvm|spok', filename).group()
        year = re.search('[0-9]+', filename).group()

        coordinations = extract_coords(doc)
    else:
        txts, id_list, genre, year, source = chunker(filename)
        coordinations = []
        conll_list = []

        for mrk in tqdm(txts.keys()):
            doc = nlp(txts[mrk])
            coordinations += extract_coords(doc, mrk, conll_list, id_list)

        print('creating a .conllu file...')
        create_conllu(conll_list, genre, year)
        print('done!')

    print('creating a .csv file...')
    create_csv(coordinations, genre=genre, year=year, source=f'text_{genre}_{year}.txt')
    print('csv created!')


def just_parse(filename):
    print('processing ' + filename)
    txts, id_list, genre, year, source = chunker(filename)
    conll_list = deque()

    for mrk in tqdm(txts.keys()):
        doc = nlp(txts[mrk])
        for sent in doc.sentences:
            sent.sent_id = f'{mrk}-{id_list[mrk].pop()}'
            conll_list.append(sent)

    print('writing conllu...')
    create_conllu(conll_list, genre, year)


if args.d:
    for file in os.listdir(os.getcwd() + '/files/'):
        # check if this file has already been processed
        genre = re.search('acad|news|fic|mag|blog|web|tvm|spok', file).group()
        year = re.search('[0-9]+', file).group()
        if len(year) == 1:
            year = '0' + year

        if f'sud_{genre}_{year}.conllu' in os.listdir(os.getcwd() + '/out_files/'):
            continue
        else:
            clean_tsv(file)
            just_parse(file)
            # try:
            #     # run(file)
            #     clean_tsv(file)
            #     just_parse(file)
            # except Exception:
            #     continue
else:
    for file in args.f:
        run(file)
        # clean_tsv(file)
        # just_parse(file)
