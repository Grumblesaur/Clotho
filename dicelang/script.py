import lark
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser
from dicelang.result import Result, failure

interpreter = DicelangInterpreter()


def execute(owner: str, server: str, dicelang_script: str) -> Result:
    try:
        ast = parser.parse(dicelang_script)
    except lark.LarkError as e:
        r = failure(error=e, console="Parsing error. You may have mistyped a keyword, forgot"
                                     " string quotes, mismatched parentheses or brackets, or used"
                                     " an operator incorrectly.")
    else:
        r = interpreter.execute(ast, as_owner=owner, on_server=server)
    return r


if __name__ == '__main__':
    tests = [
        """my x = 10""",
        """our y = 20""",
        """my x + our y""",
        """delete my x, our y""",
        """14 @ (1, 5, 9, 15, 19)""",
        """3 @! [1, 5, 9, 15, 19]""",
        """3d6 repeat 6 # ability scores""",
        """'heads' ! 'tails'""",
        """my s = dnd.stats_named; my q = dnd.stats_named""",
        """dnd.modifiers(my s)""",
        """dnd.modifiers(my q)""",
        """delete my s, my q""",
        # """help("for")""",  # this is working correctly but currently doesn't do anything useful
    ]
    for t in tests:
        output = execute('james', 'test', t)
        print(output)
