import csv
import pandas as pd
import re
import os
from tqdm import tqdm
from collections import deque


def chunker(src):
    """
    puts the sentences from a given .tsv file into bigger chunks of text, every chunk is placed in a dictionary and is
    accessible with the @@ marker as key
    :param src: name of the source .tsv file
    :return: dictionary with the text chunks, genre, year and source of the parsed texts given in the .tsv
    """
    path = os.getcwd() + '/files/' + src
    texts = {} # dictionary for texts to parse
    sent_ids = {} # dictionary for ids of parsed sentences
    df = pd.read_csv(path, sep='\t', quoting=csv.QUOTE_NONE, lineterminator='\n', quotechar='"')

    # przerobione od Adama
    df.dropna()
    filtered1 = df[df["SENT"].str.contains("TOOLONG") == False]
    filtered2 = filtered1[filtered1["SENT"].str.match(r"^ *\d[\d ]*$") == False]
    filtered2.to_csv(src, sep="\t", quoting=csv.QUOTE_NONE, lineterminator="\n", index=None)
    # ------

    df = pd.read_csv(path, sep='\t', quoting=csv.QUOTE_NONE, lineterminator='\n', quotechar='"')
    txt = ''
    id_list = []
    marker = ''
    genre = df.iloc[1, 2]
    try:
        year = str(int(df.iloc[1, 3]))
    except ValueError:
        # tsv files for web22-34 have something wrong in the year column, so if anything is wrong try to look for the
        # year in the sourcefile name in the next column
        year = str(int(re.search('\d+', df.loc[1][4]).group()))
    source = df.iloc[1, 4]

    for x in tqdm(range(len(df))):
        if marker != re.match('@@[0-9]+', str(df.loc[x][5])).group() and marker != '':
            # if there's a new @@ marker, a new entry in the dictionary is created
            m = re.match('@@[0-9]+', str(marker))

            texts[m.group()] = txt
            txt = clean(re.sub(' +', ' ', str(df.loc[x][1]))) + '\n\n'

            sent_ids[m.group()] = deque(reversed(id_list))
            id_list = [int(df.loc[x][0])]

            marker = re.match('@@[0-9]+', str(df.loc[x][5])).group()

        elif marker != re.match('@@[0-9]+', str(df.loc[x][5])).group():
            # if this is the first marker in the file, it's just written down for later
            marker = re.match('@@[0-9]+', str(df.loc[x][5])).group()
            txt += clean(re.sub(' +', ' ', str(df.loc[x][1]))) + '\n\n'
            id_list.append(int(df.loc[x][0]))

        else:
            txt += clean(re.sub(' +', ' ', str(df.loc[x][1]))) + '\n\n'
            id_list.append(int(df.loc[x][0]))

    m = re.match('@@[0-9]+', str(marker))
    texts[m.group()] = txt
    sent_ids[m.group()] = deque(reversed(id_list))

    return texts, sent_ids, genre, year, source


def clean(txt):
    """
    removes redundant spaces surrounding the punctuation
    :param txt: text to clean
    :return: clean text
    """
    to_remove = []

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

    to_remove.sort()
    to_remove.reverse()
    # removes the spaces marked by indices in the list
    for i in to_remove:
        txt = txt[:i] + txt[i+1:]
    return txt
