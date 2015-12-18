# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Iuri Gomes Diniz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
            if len(combination) >= minimum:
                tokens.add(combination)

    for n, w in enumerate(words):
        remain = ' '.join(words[n:])
        length = len(remain)
        for i in xrange(1 if onlystart else len(w)):
            first = i + minimum
            last = maximum + i
            if last > length:
                last = length
            if first > length:
                first = length
            for j in xrange(first, last + 1):
                token = remain[i:j].strip()
                if len(token) >= minimum:
                    tokens.add(token)

    return tokens
