# conversation, vlog, interview
import re

with open('en_gum-ud-test.conllu', mode='r') as file:
    source = file.read()
    heading = re.match('# global\.columns.*\\n', source)
    if heading:
        source = source.removeprefix(heading.group())
        spok = heading.group()
    else:
        spok = ''
    docs = source.split(sep='#  = # newdoc')
    for doc in docs:
        genre = re.match(' id = GUM_interview| id = GUM_vlog| id = GUM_conversation', doc)
        if genre:
            spok += '#' + doc

with open('gum_spok_test.conllu', mode='w') as file:
    file.write(spok)
