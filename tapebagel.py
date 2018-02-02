import tatsu
from tatsu import parser
from pprint import pprint
import sys

'''
    Interpreter for the CLASSIC esoteric programming language TapeBagel
    Written by an elusive S R Farmer circa 2006
'''

class TapeBagelSemantics(object):

    # instantiate memory
    def __init__(self):
        self.memory = [0, 0, 0]
        self.i = 0
        self.alpha = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def index(self, ast):
        if ast == '%%':
            self.i = 0
        elif ast == '%++':
            self.memory[self.i] += 1
        elif ast == '%#':
            self.i += 1
            if self.i >= len(self.memory):
                self.i = 0
        elif ast == '%-':
            self.memory[self.i] = 0
        else:
            pass

    def integer(self, ast):
        if ast == '*':
            return self.memory[0]
        elif ast == '**':
            return self.memory[1]
        elif ast == '***':
            return self.memory[2]
        else:
            return 0

    def output(self, ast):
        if ast[0] == '@':
            sys.stdout.write(self.alpha[ast[1]])

    def _default(self, ast):
        pass


def parse_factored():
    grammar = open('./grammars/tapebagel.ebnf').read()

    parser = tatsu.compile(grammar)
    ast = parser.parse(
        '%% %++ %++ %++ %++ %++ %++ %++ %++ @* %- %++ %++ %++ %++ %++ @* %- %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ @* @* %- %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ @* %- @* %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ @* %- %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ @* %- %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ @* %- %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ %++ @* %- %++ %++ %++ %++ @* %-',
        semantics=TapeBagelSemantics()
    )

    print('\n# FACTORED SEMANTICS RESULT')
    pprint(ast, width=20, indent=4)
    print()

parse_factored()