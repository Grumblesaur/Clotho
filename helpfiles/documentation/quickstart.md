## Quickstart

This is a quick guide for some Dicelang operations when using Clotho. If you want Clotho to
see your message, make sure to start it with `+roll`.

The person who manages your server's Clotho instance may have changed the `+` prefix to some
other character (e.g. `$` for `$roll` instead), but all documentation will assume `+` for
consistency. The correct prefix will always be indicated in Clotho's Discord status.

### Roll dice (Examples)
```
  +roll 1d20    # a twenty-sided die
  +roll 4d6     # four six-sided dice
  
  +roll 7d8kh4   # seven eight-sided dice, keep the highest four
  +roll 10d3kl5  # ten three-sided dice, keep the lowest five
  
  +roll 3d6xh1   # three six-sided dice, scratch the highest one
  +roll 8d8xl4   # eight eight-sided dice, scratch the lowest four
```
Any number of dice *k* or sides 1 or greater will work. For a number *n* of dice you keep
(`kh`, `kl`) or scratch (`xh`, `xl`), 1 <= n < k. The results of the dice can be given as
a list instead of a sum by switching the `d` to `r` (e.g. `1r20`). They will be ordered least
to greatest, not in the order they were generated.

For the rest of the examples, we'll exclude the `+roll` command handle.

### Multiply and divide (Examples)
```
  5 / 10       # gives 0.5
  8.8 / -2     # gives -4.4
  -3.0 * -3.0  # gives 9.0
  5 // 2       # gives 2  (`//` always gives an integer result)
```

### Add and subtract (Examples)
```
  6 + 4   # gives 10
  5 - 6   # gives -1
```

You'll notice that these examples have trailing remarks beginning with a `#`. These are
comments. Everything from the `#` to the end of the line is ignored. This allows you to
annotate your intent for other people reading Clotho's replies.

```
+roll [1d20 + 7,  # This is my attack roll.
       2d6 + 3,   # This is the damage it does if the game master deems it a success.
      ]           # Also, yes, trailing commas are OK in lists, and you can break commands
                  # up across multiple lines.
```

There is no multiline comment syntax.


### Repetition

Sometimes you'll want to perform one action many times. Atropos Dicelang had a repeat
operator (`^`), but Clotho Dicelang reserves this for something else. Instead, you can use
the `repeat` syntax. Say you're making a D&D 5e character, and you need to generate your
ability scores. This process has to be repeated six times for six ability scores. You could,
of course, just enter `+roll 4d6kh3` or `+roll 4d6xl1` six different times, but grouping them
together communicates your intent to your fellow players. Here's how you can do it instead:

```
  4d6lx1 repeat 6  # Roll 4d6 scratch 1 six different times.
```

More complex types of repetition can be performed using `for` loops, which you can
read about by invoking `+roll help("for")`.

This is actually unnecessary. Since D&D is a common choice of tabletop game, Clotho has a
module named `dnd` containing a few functions for tasks like this. Instead, you could invoke:

```
  dnd.stats   # There's some trickery here under the hood so that no `()` are required.
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
  3 ** 2      # gives 9
  10 ** (-1)  # gives 0.1
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