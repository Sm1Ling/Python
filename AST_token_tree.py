import ast
import io
import re
import tokenize


class AST_token_tree(object):
    """
    Accumulates number of variables and functions usage in given method-string.
    Accumulates number of given special words in comments
    """

    key_words = frozenset(['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break', 'class',
                           'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if',
                           'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
                           'while', 'with', 'yield', 'self'])

    def __init__(self, specials_list):
        """
        Creates instance of Tokens holder

        :param specials_list: list of special values that should be counted in comments and docstrings
        """
        self.__head_node = [] # list of function to parse
        self.__total_vars = {}
        self.__total_funcs = {}
        self.__total_specials = {}
        for word in specials_list:
            self.__total_specials[word] = 0

    # region Getters
    @property
    def total_variables(self):
        return self.__total_vars.copy()

    @property
    def total_functions(self):
        return self.__total_funcs.copy()

    @property
    def total_special_words(self):
        return self.__total_specials.copy()
    # endregion

    def __clear_fields__(self):
        self.__head_node = []
        self.__total_vars = {}
        self.__total_funcs = {}
        for key in self.__total_specials.keys():
            self.__total_specials[key] = 0

    class AST_parser(ast.NodeVisitor):
        """
        Subclass that helps to iterate through AST tree and extract variables, functions and special words
        """

        def __init__(self, special_words_arr, method_name):
            """
            Creates instance of local function token holder

            :param special_words_arr: iterable of special words to count
            :param method_name: name of the parsed method, including the outer method names
            """
            self.__visited_own_func = False
            self.__method_name = method_name
            self.__var_dict = {}
            self.__func_dict = {}
            self.__special_words_dict = {}
            for word in special_words_arr:
                self.__special_words_dict[word] = 0
            # список независимых функций внутри функции (когда во внутренней функции нет переменный функции родителя)
            self.__subfuncs = []

            # region Getters
            @property
            def method_name(self):
                return self.__method_name

            @property
            def variables(self):
                return self.__var_dict.copy()

            @property
            def sub_functions(self):
                return self.__subfuncs.copy()

            @property
            def functions(self):
                return self.__func_dict.copy()

            @property
            def special_words(self):
                return self.__special_words_dict.copy()

            # endregion

        def visit_FunctionDef(self, tree_node):
            """
            FunctionDef_node handler. Looks through function's arguments, annotations and body
            Adds subfunctions to the class list if exist

            :param tree_node: node of function
            :return: None
            """
            if not self.__visited_own_func:
                self.__visited_own_func = True
                for decr in tree_node.decorator_list:
                    self.generic_visit(decr)
                self.generic_visit(tree_node.args)
                for line in tree_node.body:
                    self.visit(line)
            else:
                self.__subfuncs.append(AST_token_tree.AST_parser(self.__special_words_dict.keys(),
                                                                 self.__method_name + " -> "+tree_node.name ))
                self.__subfuncs[-1].visit(tree_node)

        def visit_arg(self, tree_node):
            """
            FunctionDef's arguments handler. Adds them to the variable dictionary

            :param tree_node: node of argument
            :return: None
            """
            self.__check_in_dict__(tree_node.arg, self.__var_dict)

        def visit_Attribute(self, tree_node):
            """
            Attribute node handler. Adds attribute name to the variable dictionary

            :param tree_node: node of attribute
            :return: None
            """
            self.__check_in_dict__(tree_node.attr, self.__var_dict)
            self.generic_visit(tree_node)

        def visit_Name(self, tree_node):
            """
            Name node handler. Adds variable's name to the variable dictionary

            :param tree_node: node of Name
            :return: None
            """
            self.__check_in_dict__(tree_node.id, self.__var_dict)
            self.generic_visit(tree_node)

        def visit_Call(self, tree_node):
            """
            Function Call node handler. Adds function name to the function dictionary,
            looks through its arguments.

            :param tree_node: node of Call
            :return: None
            """
            if type(tree_node.func) == ast.Attribute:
                self.__check_in_dict__(tree_node.func.attr, self.__func_dict)
                self.visit(tree_node.func.value)
            if type(tree_node.func) == ast.Name:
                self.__check_in_dict__(tree_node.func.id, self.__func_dict)
            for keyword in tree_node.keywords:
                self.__check_in_dict__(keyword.arg, self.__var_dict)
                self.visit(keyword.value)
            for arg in tree_node.args:
                self.visit(arg)

        def visit_Expr(self, tree_node):
            """
            Expression node handler. Parses only String expressions as soon as they are docstrings

            :param tree_node: node of Expression
            :return: None
            """
            # Docstring parsing
            if type(tree_node.value) == ast.Str:
                self.__parse_specials__(tree_node.value.s)
            self.generic_visit(tree_node)

        def __parse_specials__(self, comment):
            """
            Comment and docstrings strings parser. Extracts special words out of string and adds them to the
            special words dictionary

            :param comment: string to parse
            :return: None
            """
            word_list = re.split('[#,.|;\'\"(){}\[\]\s]+', comment.strip())
            for word in word_list:
                if word in self.__special_words_dict:
                    self.__special_words_dict[word] += 1

        def __fill_dictionary__(self, total_vars, total_funcs, total_specs):
            """
            Recursive method to fill the AST_token_tree's dictionaries

            :param total_vars: AST_token_tree's variables dictionary
            :param total_funcs: AST_token_tree's functions dictionary
            :param total_specs: AST_token_tree's special words dictionary
            :return: None
            """
            self.__dict_concat__(total_vars, self.__var_dict)
            self.__dict_concat__(total_funcs, self.__func_dict)
            self.__dict_concat__(total_specs, self.__special_words_dict)
            for elem in self.__subfuncs:
                elem.__fill_dictionary__(total_vars, total_funcs, total_specs)

        @staticmethod
        def __dict_concat__(dict1, dict2):
            """
            Method to refill dict1 with dict2's content

            :param dict1: dictionary to fill
            :param dict2: dictionary from which to take keys
            :return: None
            """
            d = {}
            for key in dict2.keys():
                if key in dict1:
                    dict1[key] += dict2[key]
                else:
                    dict1[key] = dict2[key]

        @staticmethod
        def __check_in_dict__(token, dict1):
            """
            Checks whether dictionary contains token. If yes adds 1 to the proper key. If not adds key to the dict.

            :param token: string to serch in dictionary
            :param dict1: the dictionary to add token
            :return: None
            """
            if token not in AST_token_tree.key_words:
                if token in dict1:
                    dict1[token] += 1
                else:
                    dict1[token] = 1

        def __str__(self):
            return f"Method name: {self.__method_name}\n" \
                   f"Variables : {self.__var_dict}\n" \
                   f"Functions : {self.__func_dict}" \
                   f"\nSpecial words : {self.__special_words_dict}\n\n" \
                   + "".join([str(x) for x in self.__subfuncs])

    def parse(self, method_text, clear_fields=True):
        """
        Public method that handles given method text and fills dictionaries

        :param method_text: the content of parsed method. Should be given with its def
        :param clear_fields: Flag which defines whether append the method info to class or rewrite it
        :return: None
        """

        if clear_fields:
            self.__clear_fields__()

        tree = ast.parse(method_text)

        if len(tree.body) != 1 and type(tree.body[0]) != ast.FunctionDef:
            raise ValueError('Only methods are accepted')

        self.__head_node.append(AST_token_tree.AST_parser(self.__total_specials.keys(), tree.body[0].name))
        self.__head_node[-1].visit(tree)

        # если DocString еще принадлежат каким-то методам, то комментарии едва ли можно отнести к ним
        # все special words из комментариев будут помещены в коренной узел
        tokens = tokenize.tokenize(io.BytesIO(method_text.encode()).readline)
        for toknum, tokstring, tokloc, _, _ in tokens:
            if toknum is tokenize.COMMENT:
                self.__head_node[-1].__parse_specials__(tokstring[1:])

        self.__head_node[-1].__fill_dictionary__(self.__total_vars, self.__total_funcs, self.__total_specials)

    def __str__(self):
        return f"Overall Variables: {self.__total_vars}\n" \
               f"Overall Funcs: {self.__total_funcs}\n" \
               f"Overall Special Words: {self.__total_specials}\n\n" \
               f"Inner Functions:\n" + "".join([str(x) for x in self.__head_node])
