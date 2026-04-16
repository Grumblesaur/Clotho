import lark
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser, DicelangSyntaxError
from dicelang.result import Result, failure
from dicelang.flattener import Flattener

interpreter = DicelangInterpreter()
fl = Flattener()

def execute(owner: str, server: str, channel: str, dicelang_script: str) -> Result:
    try:
        ast = parser.parse(dicelang_script)
        print(ast)
        ast_flattened = fl.transform(ast)
        print(ast_flattened)
    except lark.LarkError as e:
        r = failure(error=e, console="Parsing error. You may have mistyped a keyword, forgot"
                                     " string quotes, mismatched parentheses or brackets, or used"
                                     " an operator incorrectly.")
    except DicelangSyntaxError as e:
        r = failure(error=e.context, console=f'Syntax error: {e.label}')
    else:
        r = interpreter.execute(ast_flattened, as_owner=owner, on_server=server, in_channel=channel)
    return r


if __name__ == '__main__':
    tests = [
        "((a, b) -> a + b)(1, 2)",
    ]

    for t in tests:
        output = execute('james', 'test', 'general', t)
        print(output)
        if output.error:
            print(output.error)
