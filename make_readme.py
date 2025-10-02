from pathlib import Path

documentation = Path('helpfiles/documentation')
components = [documentation / 'clotho.md', documentation / 'quickstart.md']
readme = []
for component in components:
    with open(component, 'r') as f:
        readme.append(f.read())

with open('README.md', 'w') as f:
    f.write('\n----\n'.join(readme))


