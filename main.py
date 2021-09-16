import ast
import re

from TokenizeParser import TokenizeParser

def main():
    base_sol()


def base_sol():
    parser = TokenizeParser(['TODO','FIX'])
    with open('method.txt', 'r') as text:
        parser.tokenize(text.read())
    print(parser)


if __name__ == '__main__':
    main()


