from dicelang import dicecore


class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


class DND:
    ability_scores = {'strength': 'STR', 'dexterity': 'DEX', 'constitution': 'CON',
                      'intelligence': 'INT', 'wisdom': 'WIS', 'charisma': 'CHA'}

    @ClassProperty
    @classmethod
    def stats(cls):
        return [dicecore.keep_highest(4, 6, 3) for _ in range(6)]

    @ClassProperty
    @classmethod
    def stats_named(cls):
        return dict(zip(cls.ability_scores.keys(), cls.stats))

    @ClassProperty
    @classmethod
    def adv(cls):
        return dicecore.keep_highest(2, 20, 1)

    @ClassProperty
    @classmethod
    def dis(cls):
        return dicecore.keep_lowest(2, 20, 1)

    @staticmethod
    def mod(n):
        return (n - 10) // 2

    @staticmethod
    def modifiers(named_stats: dict[str, int]) -> dict[str, int]:
        return {ability[:3].upper(): (score - 10) // 2 for ability, score in named_stats.items()}
