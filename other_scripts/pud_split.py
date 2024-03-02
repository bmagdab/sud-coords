import re

with open('en_pud-ud-test.conllu', mode='r') as file:
    source = file.read()
    heading = re.match('# global\.columns.*\\n.*newdoc.*\\n', source)
    source = source.removeprefix(heading.group())
    train = heading.group()
    test = heading.group()
    sentences = source.split(sep='\n\n')
    for i, sent in enumerate(sentences):
        if i%5 == 0:
            test += sent + '\n\n'
        else:
            train += sent + '\n\n'

with open('pud_test.conllu', mode='w') as file:
    file.write(test)

with open('pud_train.conllu', mode='w') as file:
    file.write(train)