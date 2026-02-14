import os
import functools
from pathlib import Path


class InvalidHelpTopic(KeyError):
    pass


class retrieve:
    base = Path(r'./helpfiles/documentation')
    if not os.path.exists(base):
        base = Path(r'./documentation')
    topics = {name.split('.')[0]: name for name in os.listdir(base)}

    @functools.cache
    def __new__(cls, topic) -> tuple[str, Path]:
        try:
            name = cls.topics[topic.lower()]
        except KeyError as e:
            raise InvalidHelpTopic(topic)
        with open(p := (cls.base / name), 'r') as f:
            text = f.read()
        return text, p


if __name__ == '__main__':
    print(retrieve('clotho'))