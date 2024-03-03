from datetime import datetime
import argparse
from stanza.utils.conll import CoNLL

from preprocessing import *
from extract_coords import *
from output_files import *


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', nargs='+') # list files to be processed
arg_parser.add_argument('-p', action='store_true') # parsed flag, if the input are conllu files
args = arg_parser.parse_args()


def run(filename):
    if args.p:
        print('loading the .conllu file...')
        s = datetime.now()
        doc = CoNLL.conll2doc(os.getcwd() + '/files/' + filename)
        e = datetime.now()
        print('loaded, that took ' + str(e - s))

        genre = re.search('acad|news|fic|mag|blog|web|tvm', filename).group()
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


run('test_acad_2137.tsv')
