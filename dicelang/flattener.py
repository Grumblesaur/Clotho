import lark

def init_class(cls):
    cls._clsinit()
    return cls

@init_class
class Flattener(lark.InlineTransformer):
    passthrough_rules = {'dice', 'special', 'factor', 'power', 'term',
                         'arithm', 'bitwise_and', 'bitwise_or', 'bitwise_xor',
                         'comparison', 'logical_not', 'logical_and',
                         'logical_xor', 'logical_or' 'repeat', 'flow',
                         'inline_if', 'compound', 'flow_control', 'expr',
                         'assignment', 'augmented', 'conditional'}

    def flatten(self, tree):
        if isinstance(tree, lark.Token):
            return tree
        if tree.data in self.passthrough_rules:
            return tree.children[0]
        return self.transform(tree)

    @classmethod
    def _clsinit(cls):
        for rule_name in cls.passthrough_rules:
            setattr(cls, rule_name, cls.flatten)