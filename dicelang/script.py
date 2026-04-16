import lark
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser, DicelangSyntaxError
from dicelang.result import Result, failure

interpreter = DicelangInterpreter()

class Flattener(lark.InlineTransformer):
    passthrough = {'dice', 'special', 'factor', 'power', 'term', 'arithm',
                   'bitwise_and', 'bitwise_or', 'bitwise_xor', 'comparison',
                   'logical_not', 'logical_and', 'logical_xor', 'logical_or'
                   'repeat', 'flow', 'inline_if', 'compound', 'flow_control'}

    def flatten(self, tree):
        if isinstance(tree, lark.Token):
            return tree
        if tree.data in self.passthrough:
            return tree.children[0]
        return self.transform(tree)

    dice = special = factor = power = term = arithm = flatten
    bitwise_and = bitwise_or = bitwise_xor = flatten
    comparison = logical_not = logical_and = logical_xor = logical_or = flatten
    repeat = flow = inline_if = compound = flow_control = flatten
    augmented = assignment = expr = flatten


def execute(owner: str, server: str, channel: str, dicelang_script: str) -> Result:
    try:
        ast = parser.parse(dicelang_script)
        print(ast)
        fl = Flattener()
        print(ast := fl.transform(ast))
    except lark.LarkError as e:
        r = failure(error=e, console="Parsing error. You may have mistyped a keyword, forgot"
                                     " string quotes, mismatched parentheses or brackets, or used"
                                     " an operator incorrectly.")
    except DicelangSyntaxError as e:
        r = failure(error=e.context, console=f'Syntax error: {e.label}')
    else:
        r = interpreter.execute(ast, as_owner=owner, on_server=server, in_channel=channel)
    return r


if __name__ == '__main__':
    tests = [
        "3r6xl2",
    ]

    for t in tests:
        output = execute('james', 'test', 'general', t)
        print(output)
        if output.error:
            print(output.error)
