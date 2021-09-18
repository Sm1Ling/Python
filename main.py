from TokenizeParser import TokenizeParser
from AST_token_tree import AST_token_tree


def main():
    advanced_method()


def basic_method():
    parser = TokenizeParser(['TODO', 'FIX'])
    with open('method1.txt', 'r') as text:
        parser.tokenize(text.read())
    print(parser)


def advanced_method():
    parser = AST_token_tree(['TODO', 'FIX'])
    with open('method1.txt', 'r') as fp:
        data = fp.read()

    parser.parse(data)

    with open('method2.txt', 'r') as fp:
        data = fp.read()

    parser.parse(data, False)
    print(parser)


if __name__ == '__main__':
    main()

