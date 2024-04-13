from lark import Lark

# NEVER use the 'lalr' parser option. Dicelang's grammar has loads of
# shift/reduce conflicts which 'earley' can handle.
try:
    with open('./dicelang.lark', 'r') as f:
        parser = Lark(f, parser='earley')
except FileNotFoundError:
    with open('./dicelang/dicelang.lark', 'r') as f:
        parser = Lark(f, parser='earley')
