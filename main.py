from datetime import datetime
import argparse
from stanza.utils.conll import CoNLL

from preprocessing import *
from extract_coords import *
from output_files import *


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', nargs='+')
args = arg_parser.parse_args()


def run(path):
    txts, id_list, genre, year, source = chunker(path)
    crds_full_list = []
    conll_list = []

    # extracts coordinations one chunk at a time
    for mrk in tqdm(txts.keys()):
        coordinations = extract_coords(txts[mrk], mrk, conll_list, id_list)
        crds_full_list += coordinations

    print('creating a csv...')
    create_csv(crds_full_list, genre, year, source)
    print('csv created!')

    print('processing conll...')
    create_conllu(conll_list, genre, year)
    print('done!')


def run_from_conll(file):
    s = datetime.now()
    doc = CoNLL.conll2doc(os.getcwd() + '/files/' + file)
    e = datetime.now()
    print(e-s)
    coordinations = extract_coords_from_conll(doc)
    genre = re.search('acad|news|fic|mag|blog|web|tvm', file).group()
    year = re.search('[0-9]+', file).group()
    print('writing to csv...')
    create_csv(coordinations, genre=genre, year=year, source=f'text_{genre}_{year}.txt')
    print('done!\n' + 30*'--')


# run('split_acad_2014.tsv')
# run_from_conll('kontr_sud_fic_2046.conllu')
