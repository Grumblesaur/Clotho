from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser
from dicelang.result import Result

interpreter = DicelangInterpreter()


def execute(owner: str, server: str, dicelang_script: str):
    try:
        ast = parser.parse(dicelang_script)
    except Exception as e:
        result = Result(console="Parsing error. You may have mistyped a keyword, failed to put a string in quotes"
                                " or misused an operator.", error=str(e).split('Expected')[0])
    else:
        result = interpreter.execute(ast, as_owner=owner, on_server=server)
    return result


if __name__ == '__main__':
    tests = [
        """my x + our y"""
    ]
    for t in tests:
        output = execute('james', 'test', t)
        print(output)
