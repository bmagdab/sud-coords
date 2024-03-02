import re
import random

with open('en_pronouns-ud-test.conllu', mode='r') as file:
    source = file.read()
    heading = re.match('# global\.columns.*\\n.*newdoc\\n', source)
    source = source.removeprefix(heading.group())
    train = heading.group()
    test = heading.group()
    sentences = source.split(sep='\n\n')
    # split 50/50, as recommended on Pronouns' github
    # for i, sent in enumerate(sentences):
    #     if i%2 == 0:
    #         train += sent+'\n\n'
    #     else:
    #         test += sent+'\n\n'

    # split 80/20, as I think would be better
    for i in range(len(sentences)//5):
        for_testing = random.randint(0, 4)
        for j in range(5):
            if j == for_testing:
                test += sentences[i*5 + j] + '\n\n'
            else:
                train += sentences[i*5 + j] + '\n\n'

with open('pr_test.conllu', mode='w') as file:
    file.write(test)

with open('pr_train.conllu', mode='w') as file:
    file.write(train)
