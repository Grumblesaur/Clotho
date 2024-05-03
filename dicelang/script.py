import lark
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser
from dicelang import result

interpreter = DicelangInterpreter()


def execute(owner: str, dicelang_script: str):
    try:
        ast = parser.parse(dicelang_script)
    except lark.LarkError as e:
        r = result.failure(error=e, console="[Syntax Error]")
    else:
        r = interpreter.execute(ast, as_owner=owner)
    return r


if __name__ == '__main__':
    tests = [
        """my x + our y"""
    ]
    for t in tests:
        output = execute('james', t)
        print(output)
