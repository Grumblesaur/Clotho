import tomllib

placeholder = """[bot]
prefix = "+"

[auth]
token = "insert-token-here"
"""

try:
    with open('clotho.toml', 'rb') as f:
        data = tomllib.load(f)
except FileNotFoundError as e:
    with open('clotho.toml', 'w') as f:
        f.write(placeholder + '\n')

    print(e)
    print("Fill out clotho.toml and launch again.")
