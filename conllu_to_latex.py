with open('test_files/output.conllu', mode='r') as conllu:
    conlines = conllu.readlines()
    out = ''
    for line in conlines:
        if line.startswith('#'):
            continue
        else:
            out += (line.replace('\t', ' & ').replace('_', '\_')[:-1] + r' \\' + '\n')

    print(out)
