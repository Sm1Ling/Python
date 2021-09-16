import io
import re
import tokenize


class TokenizeParser(object):
    """
        Variable and function instantiation, definitions is also usages
        Function doesn't check correctness of given method
        Kind of baseline

        Accumulates number of variables and functions usage in given method-string
        Accumulates number of given special words in comments
    """

    key_words = frozenset(['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
                           'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if',
                           'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
                           'while', 'with', 'yield', 'self'])

    def __init__(self, special_words_arr):
        self.__special_words_dict = {}
        for word in special_words_arr:
            self.__special_words_dict[word] = 0
        self.__clear_fields__()

    def __clear_fields__(self):
        self.__var_dict = {}
        self.__func_dict = {}
        for key in self.__special_words_dict.keys():
            self.__special_words_dict[key] = 0

    # region Getters
    @property
    def var_dict(self):
        return self.__var_dict.copy()

    @property
    def func_dict(self):
        return self.__func_dict.copy()

    @property
    def special_words_num(self):
        return self.__special_words_dict.copy()

    # endregion

    def tokenize(self, function_text, clear_fields=True, show_parsed=False):
        """
        Each call of this method will rewrite data about previous tokenization
        Cannot find difference between self.field.variable, self.variable, variable
        :param clear_fields: rewrite tokens or append them
        :param function_text: string with method code
        :param show_parsed: show the tokenization of each element
        """
        if clear_fields:
            self.__clear_fields__()
        current = ""
        function_text += "\n"  # из-за особенности обработки токенов

        for tpl in tokenize.tokenize(io.BytesIO(function_text.encode('utf-8')).readline):
            if show_parsed:
                print('Type ', tpl.type)
                print('String ', tpl.string)
                print('Line', tpl.line)

            # не стал разбивать на подметоды, т.к. не хочу возиться с оберткой над immutable string
            if tpl.type == 53:
                if tpl.string == "(":
                    TokenizeParser.__check_in_dict__(current, self.__func_dict)
                else:
                    TokenizeParser.__check_in_dict__(current, self.__var_dict)
                current = ""
                continue

            if tpl.type == 1:
                TokenizeParser.__check_in_dict__(current, self.__var_dict)
                if tpl.string not in TokenizeParser.key_words:
                    current = tpl.string.strip()
                else:
                    current = ""
                continue

            isdocstr = False
            if tpl.type == 3:
                self.__check_in_dict__(current, self.__var_dict)
                current = ""
                if tpl.string.strip().startswith("f"):
                    self.__parse_f_string__(tpl.string)
                    continue
                isdocstr = tpl.string.strip().startswith("\"\"\"") and tpl.string.endswith("\"\"\"")
                isdocstr = isdocstr or (tpl.string.strip().startswith("\'\'\'") and tpl.string.endswith("\'\'\'"))

            if tpl.type == 55 or isdocstr:
                self.__check_in_dict__(current, self.__var_dict)
                current = ""
                self.__parse_specials__(tpl.string)

    def __parse_f_string__(self, fstring):
        open_idx = -1
        open_brackets = 0
        for letter, i in zip(fstring, range(len(fstring))):
            if letter == "{":
                if open_brackets == 0:
                    open_idx = i
                open_brackets += 1
            if letter == "}":
                open_brackets -= 1
                if open_brackets == 0:
                    self.tokenize(fstring[open_idx:i + 1], clear_fields=False)

    def __parse_specials__(self, comment):
        word_list = re.split('[#,.|;\'\"(){}\[\]\s]+', comment.strip())
        for word in word_list:
            if word in self.__special_words_dict:
                self.__special_words_dict[word] += 1

    @staticmethod
    def __check_in_dict__(token, dict):
        if token != "":
            if token in dict:
                dict[token] += 1
            else:
                dict[token] = 1

    def __str__(self):
        return f"Variables : {self.__var_dict}\nFunctions : {self.__func_dict}" \
               f"\nSpecial words : {self.__special_words_dict}"
