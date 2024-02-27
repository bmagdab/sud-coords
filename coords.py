import stanza
import re
import syll
import csv
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import torch
import argparse
import os
from stanza.utils.conll import CoNLL
from types import NoneType


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('-f', nargs='+')
args = arg_parser.parse_args()
# nlp = stanza.Pipeline(lang='en', use_gpu=True, processors='tokenize, lemma, pos, depparse, ner', download_method=stanza.DownloadMethod.REUSE_RESOURCES, tokenize_no_ssplit=True)
# nlpcpu = stanza.Pipeline(lang='en', use_gpu=False, processors='tokenize, lemma, pos, depparse, ner', download_method=stanza.DownloadMethod.REUSE_RESOURCES, tokenize_no_ssplit=True)
models_path = './venv/stanza-train/stanza/saved_models'
config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
        'use_gpu': True,
        'pos_model_path': models_path + '/pos/en_combined-ud_charlm_tagger.pt',
        'depparse_model_path': models_path + '/depparse/en_combined-ud_charlm_parser.pt',
        'tokenize_pretokenized': False,
        'tokenize_no_ssplit': True,
        'download_method': stanza.DownloadMethod.REUSE_RESOURCES
}
nlp = stanza.Pipeline(**config)  # Initialize the pipeline using a configuration dict


# preparing the text ---------------------------------------------------------------------------------------------------
def chunker(src):
    """
    puts the sentences from a given .tsv file into bigger chunks of text, every chunk is placed in a dictionary and is
    accessible with the @@ marker as key
    :param src: name of the source .tsv file
    :return: dictionary with the text chunks, genre, year and source of the parsed texts given in the .tsv
    """
    texts = {}
    df = pd.read_csv(src, sep='\t', quoting=csv.QUOTE_NONE, lineterminator='\n', quotechar='"')
    # przerobione od Adama
    df.dropna()
    filtered1 = df[df["SENT"].str.contains("TOOLONG") == False]
    filtered2 = filtered1[filtered1["SENT"].str.match(r"^ *\d[\d ]*$") == False]
    filtered2.to_csv(src, sep="\t", quoting=csv.QUOTE_NONE, lineterminator="\n", index=None)
    # ------
    df = pd.read_csv(src, sep='\t', quoting=csv.QUOTE_NONE, lineterminator='\n', quotechar='"')
    txt = ''
    marker = ''
    genre = df.iloc[1, 2]
    try:
        year = str(int(df.iloc[1, 3]))
    except ValueError: # może usuń to potem albo nie idk to jest przez to że w web22-34 źle był wpisany rok
        year = src[-6:-4]
    source = df.iloc[1, 4]
    for x in tqdm(range(len(df))):
        if pd.isna(df.iloc[x, 5]) or not re.match('@@[0-9]+', str(df.iloc[x, 5])):
            # if there's missing information in the line, the text of the sentence is just appended
            txt += clean(str(df.iloc[x, 1])) + '\n\n'

        elif marker != re.match('@@[0-9]+', str(df.iloc[x, 5])).group() and marker != '':
            # if there's a new @@ marker, a new entry in the dictionary is created
            m = re.match('@@[0-9]+', str(marker))
            texts[m.group()] = txt
            txt = clean(str(df.iloc[x, 1])) + '\n\n'
            marker = re.match('@@[0-9]+', str(df.iloc[x, 5])).group()

        elif marker != re.match('@@[0-9]+', str(df.iloc[x, 5])).group():
            # if this is the first marker in the file, it's just written down for later
            marker = re.match('@@[0-9]+', str(df.iloc[x, 5])).group()
            txt += clean(str(df.iloc[x, 1])) + '\n\n'

        else:
            txt += clean(str(df.iloc[x, 1])) + '\n\n'
    m = re.match('@@[0-9]+', str(marker))
    texts[m.group()] = txt
    return texts, genre, year, source


def clean(txt):
    """
    removes redundant spaces by the punctuation
    :param txt: text to clean
    :return: clean text
    """
    to_remove = []
    qm = 2
    # 0 - quotation mark was closed, 1 - quotation mark was opened, 2 - quotation mark was not set

    # this loop finds the redundant spaces and adds them to the to_remove list
    for i in range(len(txt)):
        if txt[i] == ' ':
            if i+1 == len(txt) or \
                    (len(txt) > i+3 and txt[i+1:i+3] == '...') or \
                    (txt[i + 1] in [',', '.', '!', '?', ')', '}', ']', ':', ';'] and ((i + 2 < len(txt) and txt[i + 2] == ' ') or i + 2 == len(txt))) or \
                    (txt[i - 1] in ['(', '{', '['] and txt[i - 2] == ' ') or \
                    (txt[i + 1:i + 4] == "n't"):
                to_remove.append(i)
        elif len(txt) == 1:
            break
        elif txt[i] in [',', '.', '!', '?', ')', '}', ']', '(', '{', '[', ':', ';'] and i == 0 and (len(txt) == 1 or txt[1] == ' '):
            to_remove.append(i+1)
        elif txt[i] == "'" and txt[i - 1] == ' ' and (i+1 == len(txt) or txt[i + 1] != ' '):
            to_remove.append(i-1)
        elif txt[i] == '"':
            if i == 0 and txt[1] == ' ':
                to_remove.append(1)
                qm = 1
            elif i == len(txt)-1 and txt[i-1] == ' ':
                to_remove.append(i-1)
            elif txt[i - 1] == ' ' and (i + 1 == len(txt) or txt[i + 1] == ' '):
                if qm == 1:
                    to_remove.append(i - 1)
                    qm = 0
                else:
                    to_remove.append(i + 1)
                    qm = 1

    to_remove.sort()
    to_remove.reverse()
    # removes the spaces marked by indices in the list
    for i in to_remove:
        txt = txt[:i] + txt[i+1:]
    return txt


# working with stanza sentences ----------------------------------------------------------------------------------------
def dep_children(sentence):
    """
    for every word in a given sentence finds a list of IDs of that words dependents
    :param sentence: a Stanza object
    :return: nothing
    """
    for word in sentence.words:
        word.children = []
        for w in sentence.words:
            if w.head == word.id:
                word.children.append(w.id)


def word_indexer(sentence):
    sent_text = sentence.text
    current_id = 0
    for word in sentence.words:
        match = re.search(re.escape(word.text), sent_text)
        word.start = match.start() + current_id
        word.end = match.end() + current_id
        sent_text = sent_text[match.end():]
        current_id = match.end() + current_id


def coord_info(crd, sent, conj):
    """
    collects information on elements of a coordination: text of the conjunct, number of words, tokens and syllables
    :param crd: coordination (a dictionary containing the left and right elements of coordination, its head and the conjunct, if there is one)
    :param sent: sentence (Stanza object) where the coordination was found
    :param conj: which element of a coordination is to be considered (takes values "L" or "R")
    :param other_ids: a list of word IDs, that belong to the opposite element of the coordination
    :return: a list of word IDs, that belong to the element of the coordination that was specified by the conj parameter
    """
    txt_ids = []

    for id in crd[conj].children:
        if (id not in crd['other_conjuncts'] and sent.words[id - 1].deprel != 'cc'
                and (id < crd['R'].id)*(conj == 'L')+(conj == 'R')):

            if not isinstance(sent.words[id - 1].feats, NoneType) and 'Shared=Yes' in sent.words[id - 1].feats:
                continue
            elif not isinstance(sent.words[id - 1].feats, NoneType) and 'Shared=No' in sent.words[id - 1].feats:
                txt_ids.append(id)
                continue

            if ((id < crd[conj].id)*(conj == 'L')+(id > crd[conj].id)*(conj == 'R') and
                    re.match('compound', sent.words[id - 1].deprel)):
                txt_ids.append(id)
                continue

            elif (id < crd['L'].id)*(conj == 'L')+(id > crd['R'].id)*(conj == 'R'):
                for c in [crd['L'].id]*(conj == 'R')+crd['other_conjuncts']+[crd['R'].id]*(conj == 'L'):
                    for c_child in sent.words[c - 1].children:
                        if sent.words[c_child - 1].deprel == sent.words[id - 1].deprel:
                            txt_ids.append(id)
                            break
                    if id in txt_ids:
                        break

            else:
                # all children of the head appearing between the head and other elements of the coordination are part of the conjunct
                txt_ids.append(id)

    # the loop below looks through words already included in the conjunct and adds their children, repeats until there
    # are no more words to be added
    keep_looking = True
    while keep_looking and txt_ids:
        for id in txt_ids:
            for i in sent.words[id - 1].children:
                txt_ids.append(i)
            else:
                keep_looking = False
    txt_ids.append(crd[conj].id)
    txt_ids.sort()

    # removes some of the punctuation from the beginning of the conjunct
    while (sent.words[min(txt_ids)-1].text in [',', ';', '-', ':', '--']
           or sent.words[min(txt_ids)-1].deprel == 'cc'):
        txt_ids.remove(min(txt_ids))

    words = 0
    tokens = 0
    for id in range(min(txt_ids), max(txt_ids) + 1):
        tokens += 1
        if sent.words[id - 1].deprel != 'punct':
            words += 1

    txt = sent.text[sent.words[min(txt_ids) - 1].start - sent.words[0].start:sent.words[max(txt_ids) - 1].end - sent.words[0].start]

    syllables = 0
    for w in txt.split():
        syllables += syll.count_word(w)

    crd[conj+'conj'] = txt
    crd[conj+'words'] = words
    crd[conj+'tokens'] = tokens
    crd[conj+'syl'] = syllables


def coord_finder(sentence, conjunct):
    conjuncts = [conjunct.id]
    for child in conjunct.children:
        if 'conj' in sentence.words[child-1].deprel:
            conjuncts.append(child)
            conjuncts = conjuncts + coord_finder(sentence, sentence.words[child-1])
    return conjuncts


def extract_coords(src, marker, conll_list, sentence_count):
    """
    finds coordinations in a given text, creates a conllu file containing every sentence with a found coordination
    :param src: text to parse
    :param marker: marker of the parsed text
    :param conll_list: list for sentences, to later create a conllu file corresponding to the table of coordinations
    :param sentence_count: counts how many sentences from the whole source file have been parsed
    :return: list of dictionaries representing coordinations, the number of sentences that were already processed
    """
    torch.cuda.empty_cache()
    try:
        doc = nlp(src)
    except RuntimeError:
        # doc = nlpcpu(src)
        doc = nlp(src)
    coordinations = []
    for sent in doc.sentences:
        index = sent.index + 1 + sentence_count
        # updating sentence count so that it corresponds to the sentence ids in the source .tsv file
        dep_children(sent)
        word_indexer(sent)
        sent.text = re.sub(' +', ' ', sent.text)

        coords = []  # previously conjs
        # every word that has a conj dependency becomes a key in the conjs dictionary, its values are all words that are
        # connected to the key with a conj dependency
        for dep in sent.dependencies:
            if 'conj' in dep[1]:
                coord = [dep[0].id] + coord_finder(sent, dep[2])
                coords.append(list(dict.fromkeys(coord)))

        rem = []
        for i, coord in enumerate(coords):
            for coord2 in coords:
                if set(coord).intersection(set(coord2)) == set(coord) and coord != coord2:
                    rem.append(i)
                    break

        for r in reversed(rem):
            coords.remove(coords[r])

        if coords:
            # if there are any valid conj dependencies in a sentence, it will be included in the .conllu file
            # a sentence id including the @@ marker from COCA source files is assigned and will be both in the .conllu
            # and .csv file
            sent.coca_sent_id = str(marker) + '-' + str(index)
            conll_list.append(sent)

        # this loop writes down information about every coordination based on the list of elements of a coordination
        for crd in coords:
            if len(crd) > 1:
                crd.sort()
                coord = {'L': sent.words[min(crd) - 1], 'R': sent.words[max(crd) - 1]}
                crd.pop(0)
                crd.pop(-1)
                coord['other_conjuncts'] = crd
                if coord['L'].head != 0:
                    coord['gov'] = sent.words[coord['L'].head - 1]
                for child in coord['R'].children:
                    if sent.words[child-1].deprel == 'cc':
                        coord['conj'] = sent.words[child-1]
                        break
                coord_info(coord, sent, 'R')
                coord_info(coord, sent, 'L')
                coord['sentence'] = sent.text
                coord['sent_id'] = sent.coca_sent_id
                coordinations.append(coord)

    sentence_count += len(doc.sentences)
    return coordinations, sentence_count


def extract_coords_from_conll(doc):
    coordinations = []
    for sent in tqdm(doc.sentences):
        # updating sentence count so that it corresponds to the sentence ids in the source .tsv file
        dep_children(sent)
        word_indexer(sent)

        coords = []  # previously conjs
        # every word that has a conj dependency becomes a key in the conjs dictionary, its values are all words that are
        # connected to the key with a conj dependency
        for dep in sent.dependencies:
            if 'conj' in dep[1]:
                coord = [dep[0].id] + coord_finder(sent, dep[2])
                coords.append(coord)

        rem = []
        for i, coord in enumerate(coords):
            coord = list(dict.fromkeys(coord))
            for coord2 in coords:
                if set(coord).intersection(set(coord2)) == set(coord) and coord != coord2:
                    rem.append(i)
                    break

        for r in reversed(rem):
            coords.remove(coords[r])

        # this loop writes down information about every coordination based on the list of elements of a coordination
        for crd in coords:
            if len(crd) > 1:
                crd.sort()
                coord = {'L': sent.words[min(crd) - 1], 'R': sent.words[max(crd) - 1]}
                crd.pop(0)
                crd.pop(-1)
                coord['other_conjuncts'] = crd
                if coord['L'].head != 0:
                    coord['gov'] = sent.words[coord['L'].head - 1]
                for child in coord['R'].children:
                    if sent.words[child - 1].deprel == 'cc':
                        coord['conj'] = sent.words[child - 1]
                        break
                coord_info(coord, sent, 'R')
                coord_info(coord, sent, 'L')
                coord['sentence'] = sent.text
                coord['sent_id'] = sent.sent_id
                coordinations.append(coord)
    return coordinations


# creating files -------------------------------------------------------------------------------------------------------
def create_conllu(sent_list, genre, year):
    """
    creates a conllu file with sentences with coordinations, with every tree comes the text of the sentence and the same
    sentence id that is in the csv file
    this function is based on doc2conll from stanza.utils.conll, described as deprecated and to be removed
    :param sent_list: list of sentences (stanza object) that had a coordination in them
    :param file_path: name for the conllu file
    """
    doc_conll = []
    for sentence in sent_list:
        sent_conll = []
        for com in sentence.comments:
            if re.match('# sent_id = ', com):
                sent_conll.append('# sent_id = ' + sentence.coca_sent_id)
            else:
                sent_conll.append(com)
        for token in sentence.tokens:
            sent_conll.extend(token.to_conll_text().split('\n'))
        doc_conll.append(sent_conll)

    path = os.getcwd() + '/sud_' + str(genre) + '_' + str(year) + '.conllu'
    with open(path, mode='w', encoding='utf-8') as conll_file:
        for sent in doc_conll:
            for line in sent:
                conll_file.write(line + '\n')
            conll_file.write('\n')


def create_csv(crd_list, genre, year, source):
    """
    creates a .csv table where every row has information about one coordination
    :param crd_list: list of dictionaries, each dictionary represents a coordination
    :param genre: genre of the parsed file, information included in the filename and in the table
    :param year: year in which the parsed text was published, included in the filename and the table
    :param source: name of the source file
    :return: nothing
    """
    path = os.getcwd() + '/sud_' + str(genre) + '_' + str(year) + '.csv'
    with open(path, mode='w', newline="", encoding='utf-8-sig') as outfile:
        writer = csv.writer(outfile)
        col_names = ['governor.position', 'governor.word', 'governor.tag', 'governor.pos', 'governor.ms',
                     'conjunction.word', 'conjunction.tag', 'conjunction.pos', 'conjunction.ms', 'no.conjuncts',
                     'L.conjunct', 'L.dep.label', 'L.head.word', 'L.head.tag', 'L.head.pos', 'L.head.ms', 'L.words',
                     'L.tokens', 'L.syllables', 'L.chars', 'R.conjunct', 'R.dep.label', 'R.head.word', 'R.head.tag',
                     'R.head.pos', 'R.head.ms', 'R.words', 'R.tokens', 'R.syllables', 'R.chars', 'sentence', 'sent.id',
                     'genre', 'converted.from.file']
        writer.writerow(col_names)

        for coord in crd_list:
            writer.writerow(['0' if 'gov' not in coord.keys() else 'L' if coord['L'].id > coord['gov'].id else 'R',     # governor.position
                             str(coord['gov'].text) if 'gov' in coord.keys() else '',                                   # governor.word
                             coord['gov'].xpos if 'gov' in coord.keys() else '',                                        # governor.tag
                             coord['gov'].upos if 'gov' in coord.keys() else '',                                        # governor.pos
                             coord['gov'].feats if 'gov' in coord.keys() else '',                                       # governor.ms
                             str(coord['conj'].text) if 'conj' in coord.keys() else '',                                 # conjunction.word
                             coord['conj'].xpos if 'conj' in coord.keys() else '',                                      # conjunction.tag
                             coord['conj'].upos if 'conj' in coord.keys() else '',                                      # conjunction.pos
                             coord['conj'].feats if 'conj' in coord.keys() else '',                                     # conjunction.ms
                             int(2 + len(coord['other_conjuncts'])),                                                    # no.conjuncts
                             str(coord['Lconj']),                                                                       # L.conjunct
                             coord['L'].deprel,                                                                         # L.dep.label
                             str(coord['L'].text),                                                                      # L.head.word
                             coord['L'].xpos,                                                                           # L.head.tag
                             coord['L'].upos,                                                                           # L.head.pos
                             coord['L'].feats,                                                                          # L.head.ms
                             int(coord['Lwords']),                                                                      # L.words
                             int(coord['Ltokens']),                                                                     # L.tokens
                             int(coord['Lsyl']),                                                                        # L.syllables
                             len(coord['Lconj']),                                                                       # L.chars
                             str(coord['Rconj']),                                                                       # R.conjunct
                             coord['R'].deprel,                                                                         # R.dep.label
                             str(coord['R'].text),                                                                      # R.head.word
                             coord['R'].xpos,                                                                           # R.head.tag
                             coord['R'].upos,                                                                           # R.head.pos
                             coord['R'].feats,                                                                          # R.head.ms
                             int(coord['Rwords']),                                                                      # R.words
                             int(coord['Rtokens']),                                                                     # R.tokens
                             int(coord['Rsyl']),                                                                        # R.syllables
                             len(coord['Rconj']),                                                                       # R.chars
                             str(coord['sentence']),                                                                    # sentence
                             coord['sent_id'],                                                                          # sent.id
                             genre,                                                                                     # genre
                             source])                                                                                   # converted.from.file


# running --------------------------------------------------------------------------------------------------------------
def run(path):
    s = datetime.now()

    txts, genre, year, source = chunker(path)
    crds_full_list = []
    conll_list = []
    sent_count = 0

    # extracts coordinations one chunk at a time
    for mrk in tqdm(txts.keys()):
        coordinations, sent_count = extract_coords(txts[mrk], mrk, conll_list, sent_count)
        crds_full_list += coordinations

    print('creating a csv...')
    create_csv(crds_full_list, genre, year, source)
    print('csv created!')

    print('processing conll...')
    create_conllu(conll_list, genre, year)
    print('done!')

    e = datetime.now()
    print(e-s)


def run_from_conll(file):
    s = datetime.now()
    doc = CoNLL.conll2doc(os.getcwd() + '/' + file)
    e = datetime.now()
    print(e-s)
    coordinations = extract_coords_from_conll(doc)
    genre = re.search('acad|news|fic|mag|blog|web|tvm', file).group()
    year = re.search('[0-9]+', file).group()
    print('writing to csv...')
    create_csv(coordinations, genre=genre, year=year, source=f'text_{genre}_{year}.txt')
    print('done!\n' + 30*'--')


# normalna wersja do terminala:

# for file in args.f:
#     print('processing ' + file)
#     with torch.no_grad():
#         run(os.getcwd() + '/split/' + file)

# jakieś moje nienormalne wersje nwm:

# run_from_conll('acad_2048.conllu')

# genre = args.f[0]
# if args.f[1] == '7':
#     files = [f'split_{genre}_{year}.tsv' for year in range(1991, 2007, 2)]
#     files.remove(f'split_{genre}_2001.tsv')
# elif args.f[1] == '6':
#     files = [f'split_{genre}_{year}.tsv' for year in range(2007, 2021, 2)]
#     files.remove(f'split_{genre}_2011.tsv')
# for file in files:
#     print('processing ' + file)
#     with torch.no_grad():
#         run(os.getcwd() + '/split/' + file)
# PAMIĘTAJ ŻEBY WYPAKOWAĆ PLIKI ZANIM TO PUŚCISZ

# files = [f'stanza_trees_acad_{year}.conllu' for year in range(2008, 2020, 2)]
# print(files)
# for file in files:
#     print('processing ' + file)
#     run_from_conll(file)

# run('split_news_2046.tsv')
# run_from_conll('sud_news_2009.conllu')
