from lark import Lark
with open('./dicelang.lark', 'r') as f:
    # NEVER use the 'lalr' parser option. Dicelang's grammar has loads of
    # shift/reduce conflicts which 'earley' can handle.
    parser = Lark(f, parser='earley')
