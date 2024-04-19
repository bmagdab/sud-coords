from datetime import datetime
import argparse
from stanza.utils.conll import CoNLL
from collections import deque
import stanza
from preprocessing import *
from extract_coords import *
from output_files import *

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', nargs='+') # list files to be processed
arg_parser.add_argument('-p', action='store_true') # parsed flag, if the input are conllu files
arg_parser.add_argument('-d', action='store_true') # processes the whole directory
arg_parser.add_argument('-s', action='store_true') # use the sud models
args = arg_parser.parse_args()


if 'out_files' not in os.listdir():
    os.mkdir('out_files')


if args.s and not args.p:
    config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
        'use_gpu': True,
        'pos_model_path': './saved_models/en_combined-sud_charlm_tagger.pt',
        'depparse_model_path': './saved_models/en_combined-sud_charlm_parser.pt',
        'tokenize_pretokenized': False,
        'tokenize_no_ssplit': True,
        'download_method': stanza.DownloadMethod.REUSE_RESOURCES
    }
    nlp = stanza.Pipeline(**config)  # Initialize the pipeline using a configuration dict
    print('using the sud model')
elif not args.p:
    config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
        'use_gpu': True,
        'pos_model_path': './saved_models/en_compare-ud_charlm_tagger.pt',
        'depparse_model_path': './saved_models/en_compare-ud_charlm_parser.pt',
        'tokenize_pretokenized': False,
        'tokenize_no_ssplit': True,
        'download_method': stanza.DownloadMethod.REUSE_RESOURCES
    }
    nlp = stanza.Pipeline(**config)
    print('using the ud model')


def run(filename):
    if args.p:
        genre = re.search('acad|news|fic|mag|blog|web|tvm|spok', filename).group()
        year = re.search('[0-9]+', filename).group()
        print(f'processing {filename}')
        with open(os.getcwd() + '/files/' + filename, mode='r') as file:
            coordinations = []
            text = file.read()
            sents = text.split('\n\n')
            sents = deque(sents)
        for _ in tqdm(range(len(sents))):
            sent = sents.popleft()
            if sent: # do not process an empty string, the function below doesn't understand it
                conllu = CoNLL.conll2doc(input_str=sent)
                coordinations += extract_coords(conllu)
    else:
        print(f'processing {filename}')
        clean_tsv(filename)
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

        if f'sud_{genre}_{year}.csv' in os.listdir(os.getcwd() + '/out_files/'):
            continue
        else:
            run(file)
else:
    for file in args.f:
        run(file)
        # clean_tsv(file)
        # just_parse(file)
