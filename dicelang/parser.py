from lark import Lark
with open('./dicelang.lark', 'r') as f:
    parser = Lark(f)
