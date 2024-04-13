from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser

interpreter = DicelangInterpreter()


def execute(owner: str, dicelang_script: str):
    ast = parser.parse(dicelang_script)
    result = interpreter.execute(ast, as_owner=owner)
    return result


if __name__ == '__main__':
    tests = [
        """my x + our y"""
    ]
    for t in tests:
        output = execute('james', t)
        print(output)
