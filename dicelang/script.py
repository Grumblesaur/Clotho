import lark
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser
from dicelang import result

interpreter = DicelangInterpreter()


def execute(owner: str, server: str, dicelang_script: str):
    try:
        ast = parser.parse(dicelang_script)
    except lark.LarkError as e:
        r = result.failure(error=e, console="Parsing error. You may have mistyped a keyword, failed "
                                            "to put a string in quotes, or misused an operator.")
    else:
        r = interpreter.execute(ast, as_owner=owner, on_server=server)
    return r


if __name__ == '__main__':
    tests = [
        """my x + our y"""
    ]
    for t in tests:
        output = execute('james', 'test', t)
        print(output)
