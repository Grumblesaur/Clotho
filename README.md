# Clotho
Clotho is a tool for playing tabletop RPG games over Discord. It features a simple
expression-based programming language for automating common RPG actions, and for the most
essential features, no prior programming experience is required. Familiarity with basic
arithmetic and [dice notation](https://en.wikipedia.org/wiki/Dice_notation) is sufficient.

While most Discord bots are run by their developers for any server to add them, a major
design goal of Clotho is to make it easy to run one's own instance of the bot for a private
server or group of servers. Furthermore, bot operators with some knowledge of Python will be
able to write their own Python plugins for the bot, for instances where Dicelang is too
limiting.

## Questions

If you're confused about how something words, need to report a bug, or have an idea for a new
feature, you can open an issue on Clotho's [GitHub repository](https://github.com/Grumblesaur/Clotho).

----
## Quickstart

This is a quick guide for some Dicelang operations when using Clotho. If you want Clotho to
see your message, make sure to start it with `+roll`. If this would trigger another bot as
well, you can use `+roll` instead.

The person who manages your server's Clotho instance may have changed the `+` prefix to some
other character (e.g. `$` for `$roll` instead), but all documentation will assume `+` for
consistency. The correct prefix will always be indicated in Clotho's Discord status.

### Roll dice (Examples)
```
  +roll 1d20    ? a twenty-sided die
  +roll 4d6     ? four six-sided dice
  
  +roll 7d8kh4   ? seven eight-sided dice, keep the highest four
  +roll 10d3kl5  ? ten three-sided dice, keep the lowest five
  
  +roll 3d6xh1   ? three six-sided dice, scratch the highest one
  +roll 8d8xl4   ? eight eight-sided dice, scratch the lowest four
```
Any number of dice or sides 1 or greater will work. The number you keep (`kh`, `kl`)
must be greater than or equal to 1 and less than or equal to the number of dice rolled.
If you scratch (drop) dice instead (`xh`, `xl`), the number you scratch must be greater
or equal to 1 and strictly less than the number of dice rolled. The results of the dice
can be given as a list instead of a sum by switching the `d` to `r` (e.g. `1r20`). They
will be ordered least to greatest, not in the order they were generated.

For the rest of the examples, we'll exclude the `+roll` command handle.

### Multiply and divide (Examples)
```
  5 / 10       ? gives 0.5
  8.8 / -2     ? gives -4.4
  -3.0 * -3.0  ? gives 9.0
  5 // 2       ? gives 2  (`//` always gives an integer result)
```

### Add and subtract (Examples)
```
  6 + 4   ? gives 10
  5 - 6   ? gives -1
```

You'll notice that these examples have trailing remarks beginning with a `?`. These are
comments. Everything from the `?` to the end of the line is ignored by the Dicelang
interpreter. This allows you to annotate your intent for other people reading Clotho's
replies.

```
+roll [1d20 + 7,  ? This is my attack roll.
       2d6 + 3,   ? This is the damage it does if the game master deems it a success.
      ]           ? Also, yes, trailing commas are OK in lists, and you can break commands
                  ? up across multiple lines.
```

There is no multiline comment syntax.


### Repetition

Sometimes you'll want to perform the same action multiple times. Atropos Dicelang had a
repeat operator (`^`), but Clotho Dicelang reserves this for a different operation now.
Instead, you can use the `for` loop syntax. Say you're making a D&D character, and you need
to generate your ability scores. This process has to be repeated six times for six ability
scores. You could, of course, just enter `+roll 4d6kh3` or `+roll 4d6xl1` six different times,
but grouping them together states your intent more clearly to your fellow players, and reduces
clutter in your chat. Here's how you can do it instead:

```
  for ability_score in [1 through 6] do 4d6xl1
```

The variable `ability_score` does not actually have to be named here; we could leave it
blank  by calling it `_` instead. `[1 through 6]` creates the list `[1, 2, 3, 4, 5, 6]`.
This is helpful, since we need ability scores. So, for each item in this list, we'll
`do` `4d6xl1`, which is the expression that generates an ability score. The output of the
entire `for` expression is a list containing the ability scores, which a player can assign
as desired. For more information on this kind of loop, invoke `help("for")`.

This is actually unnecessary. Since D&D is a common choice of tabletop game, Clotho has a
module named `dnd` containing a few functions for tasks like this. Instead, you could invoke:

```
  dnd.stats   ? There's some trickery here under the hood so that no `()` are required.
```

Or, if you want them auto-assigned to the ability scores by name,

```
  dnd.stats_named
```

These are all examples of expressions, which can be combined to your heart's content. For
example, you can roll two different dice and add their totals together,

```
  1d6 + 1d10
```

or modify a roll.

```
  1d100 - 10
  10 * 5d4
  10 / 1d20
```

### Exponents (Examples)
```
  3 ** 2      ? gives 9
  10 ** (-1)  ? gives 0.1
```

Just like with regular math, Atropos' dice engine adheres to an order of  operations (also
known as operator precedence). For the operations defined above, the order of precedence
is:
  * parentheses
  * dice
  * exponents
  * negative sign
  * multiplication and division
  * addition and subtraction

There are many more operations left out of the quickstart guide, but these are all most
games require. Other help topics will explain other features, and elaborate on the ones
listed.