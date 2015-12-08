'''
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
from itertools import chain, combinations
from unicodedata import normalize

def iconv(input_str):
    if type(input_str) == str:
        # assume utf-8 strings
        input_str = input_str.decode('utf-8')
    return normalize("NFKD", input_str).encode('ascii', 'ignore')

def onlynumbers(obj, input_str, *args, **kwargs):
    return ''.join(filter(lambda x: x.isdigit(), str(input_str)))

def powerset(iterable):
    # from https://docs.python.org/2/library/itertools.html#recipes
    xs = list(iterable)
    # note we return an iterator rather than a list
    return chain.from_iterable(combinations(xs, n) for n in range(len(xs) + 1))

def tokenize(phrase, minimum=None, maximum=None, onlystart=True, combine=True):
    GOOD_NUMBER = 4
    if minimum is not None and maximum is None:
        # only minimum defined
        maximum = minimum + GOOD_NUMBER
    elif maximum is not None and minimum is None:
        # only maximum defined
        minimum = maximum - GOOD_NUMBER
    elif maximum is None and minimum is None:
        # both undefined
        minimum = GOOD_NUMBER
        maximum = minimum + GOOD_NUMBER

    if minimum < 1:
        minimum = 1
    if maximum < 1:
        maximum = 1

    tokens = set()
    words = str(phrase).split()
    # add each word and word combination
    if not combine:
        for word in words:
            if word >= minimum:
                tokens.add(word)
    else:
        for combination in [" ".join(s) for s in  powerset(words)]:
            if len(combination) > minimum:
                tokens.add(combination)

    for word in filter(lambda x: len(x) >= minimum, words):
        # add partial words
        length = len(word)

        for i in xrange(1 if onlystart else length):
            first = i + minimum
            last = maximum + i
            if last > length:
                last = length
            if first > length:
                first = length
            for j in xrange(i + minimum, last + 1):
                tokens.add(word[i:j])

    return tokens