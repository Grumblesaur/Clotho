from lark import Lark, UnexpectedInput
from pathlib import Path

class MissingGrammar(Exception):
    pass

class DicelangSyntaxError(SyntaxError):
    label = "Syntax error"

    def __init__(self, *args, **kwargs):
        self.context = args[0]
        super().__init__(*args, **kwargs)

    def __str__(self):
        context, line, column = self.args
        return f'{self.label} at line {line}, column {column}.\n{context}'

class MissingConstruct(DicelangSyntaxError):
    label = "Missing construct"

    def __str__(self):
        ctx = self.args[0]
        return f'{self.label}:\n{ctx}'

class MissingOperand(MissingConstruct):
    label = "Missing value"

class MissingLeftOperand(MissingOperand):
    label = "Missing left operand"
    examples = ["* 1"]

class MissingRightOperand(MissingOperand):
    label = "Missing right operand"
    examples = ["1 +"]

class MissingDelimiter(MissingConstruct):
    label = "Missing delimiter"

class MissingComma(MissingDelimiter):
    label = "Missing comma"
    examples = ["[1 2]"]

class MissingBrace(MissingDelimiter):
    label = "Missing brace"

class MissingOpenParen(MissingBrace):
    label = "Missing open parenthesis"
    examples = ['[1, )]']

class MissingCloseParen(MissingBrace):
    label = "Missing close parenthesis"
    examples = ['(1, ']

class MissingOpenCurly(MissingBrace):
    label = "Missing open curly brace"
    examples = ['(1, })']

class MissingCloseCurly(MissingBrace):
    label = "Missing close curly brace"
    examples = ['{1: 5']

class MissingOpenBracket(MissingBrace):
    label = "Missing open bracket"
    examples = ['[1, ]]']

class MissingCloseBracket(MissingBrace):
    label = "Missing close bracket"
    examples = ['[1, ', '[1, 2']


# NEVER use the 'lalr' parser option. Dicelang's grammar has loads of
# shift/reduce conflicts which 'earley' can handle.
class DicelangParser:
    Paths = [Path(x) for x in ('./dicelang.lark', './dicelang/dicelang.lark')]
    _syntax_errors = {MissingLeftOperand, MissingRightOperand, MissingComma, MissingOpenParen, MissingCloseParen,
                      MissingOpenCurly, MissingCloseCurly, MissingOpenBracket, MissingCloseBracket,}

    def __init__(self, path: Path = None):
        for path in self.Paths:
            try:
                with open(path, 'r', encoding='utf-8') as grammar_file:
                    self.grammar = grammar_file.read()
                    break
            except FileNotFoundError:
                pass
        else:
            paths = ', '.join(str(p) for p in self.Paths)
            raise MissingGrammar(f'Grammar not found along following path(s): {paths}')
        self.kernel = Lark(self.grammar, parser='earley')

    @classmethod
    def make_examples(cls):
        return {error_type: error_type.examples for error_type in cls._syntax_errors}

    def parse(self, code: str, start=None):
        try:
            ast = self.kernel.parse(code, start=start)
        except UnexpectedInput as u:
            exc_class = u.match_examples(self.kernel.parse, self.make_examples(), use_accepts=True) or DicelangSyntaxError
            raise exc_class(u.get_context(code), u.line, u.column)
        return ast


parser = DicelangParser()


def main():
    code = """1, 5]"""
    try:
        ast = DicelangParser().parse(code)
    except DicelangSyntaxError as e:
        print(e)
    else:
        print(ast)

if __name__ == '__main__':
    main()
