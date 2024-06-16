# without conversation, vlog, interview
import re

ud = True

with open('en_compare-ud-dev.conllu', mode='r') as file:
    source = file.read()
    if not ud:
        heading = re.match('# global\.columns.*\\n', source)
        source = source.removeprefix(heading.group())
        spok = heading.group()
        docs = source.split(sep='#  = # newdoc')
    else:
        spok = ''
        docs = source.split(sep='# newdoc')
    for doc in docs:
        genre = re.match(' id = GUM_interview| id = GUM_vlog| id = GUM_conversation', doc)
        if not genre:
            spok += '#' + doc

with open('en_comp-writ_dev.conllu', mode='w') as file:
    file.write(spok)