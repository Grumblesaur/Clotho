from pathlib import Path

documentation = Path('helpfiles/documentation')
components = [documentation / 'clotho.md', documentation / 'quickstart.md']
readme = []
for component in components:
    with open(component, 'r') as f:
        readme.append(f.read())

with open('README.md', 'w') as f:
    f.write("<!-- THIS FILE HAS BEEN GENERATED FROM OTHER SOURCES. IT SHOULD NOT BE EDITED DIRECTLY. -->\n")
    f.write('\n----\n'.join(readme))


