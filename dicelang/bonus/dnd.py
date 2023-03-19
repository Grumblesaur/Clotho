from dicelang import dicecore


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

class dnd:
    ability_scores = ['strength',     'dexterity', 'constitution',
                      'intelligence', 'wisdom',    'charisma']

    @classproperty
    @classmethod
    def stats(cls):
        return [dicecore.keep_highest(4, 6, 3) for _ in range(6)]

    @classproperty
    @classmethod
    def stats_named(cls):
        return dict(zip(cls.ability_scores, cls.stats))

    @classproperty
    @classmethod
    def adv(cls):
        return dicecore.keep_highest(2, 20, 1)

    @classproperty
    @classmethod
    def dis(cls):
        return dicecore.keep_lowest(2, 20, 1)
