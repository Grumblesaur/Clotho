# Operators

Much of Dicelang's functionality comes from mathematical operators. You are likely already familiar with addition,
subtraction, multiplication, division, and exponentiation. As Dicelang is a programming language, particularly one that
centers around [dice notation](https://en.wikipedia.org/wiki/Dice_notation), it includes many others, and they have a
precedential order just like ordinary math class PEMDAS. The closer to the top of the list an operation is, the sooner
it is processed.

## Precedence Table

(You may wish to open this in a Markdown viewer, such as the
[Markdown Viewer Webtext](https://addons.mozilla.org/en-US/firefox/addon/markdown-viewer-webext/) for Mozilla Firefox.)

|    Precedence Level    | Operators                                                        | Names                                                                        |
|:----------------------:|------------------------------------------------------------------|------------------------------------------------------------------------------|
|        Priority        | `()`                                                             | Parentheses                                                                  |
|          Atom          | `f()`, `[]`, `.`                                                 | Function calls, subscripts, attributes                                       |
|          Dice          | `d`, `r` with `kh`, `xh`, `kl`, `xl`                             | Dice rolls, with keep/scratch highest/lowest                                 |
|        Special         | (unary) `&`, `!`, `@`, (unary) `@`, `@!`                         | Sum, coinflip, random selection, random selection without replacement        |
|         Power          | `**`                                                             | Exponentiation                                                               |
|         Factor         | (unary) `+`, (unary) `-`, (unary) `~`                            | Unary plus, unary minus, bitwise not                                         |
|          Term          | `*`, `/`, `//`, `%`, `<<`, `>>`                                  | Multiplication, division, floor division, remainder, left shift, right shift |
|       Arithmetic       | `+`, `-`, `$`                                                    | Addition, subtraction, numeric catenation                                    |
|      Bitwise AND       | `&`                                                              | Bitwise AND                                                                  |
|      Bitwise XOR       | `^`                                                              | Bitwise XOR                                                                  |
|       Bitwise OR       | `\|`                                                             | Bitwise OR                                                                   |
|       Comparison       | `in`, `not in`, `is`, `is not`, `>`, `<`, `>=`, `<=`, `==`, `!=` | Member of, identity, numeric comparisons, equality                           |
|    Logical Negation    | `not`                                                            | Boolean NOT                                                                  |
|  Logical Conjunction   | `and`                                                            | Boolean AND                                                                  |
| Logical Nonequivalence | `xor`                                                            | Boolean XOR                                                                  |
|  Logical Disjunction   | `or`                                                             | Boolean OR                                                                   |
|       Repetition       | `repeat`                                                         | Repeat                                                                       |
|   Inline Conditional   | `value_when_true if condition else value_when_false`             | Inline IF                                                                    |
|      Assignment        | `=`                                                              | Assignment                                                                   |

## Examples

**Parentheses**

```
(3 + 6) * 2
>>> 18
```

----

**Function calls**

```
sum([1, 5, 9])
>>> 15
```

**Subscripts**

```
('A', 'B', 'C')[0]
>>> 'A'
```

----

**Dice**

See `+docs quickstart` for a list of dice roll examples.

----

**Sum or Join**

```
&[1, 2, 3]
>>> 6

&['a', 'b', 'c']
>>> 'abc'
```

**Coinflip**

This operator yields one of its operands at random.

```
'Heads' ! 'Tails'
[e.g.] >>> 'Heads'
```

**Random Selection**

This operator selects random element from an iterable object. It replaces elements when performing multiple
selections, so the same element may be selected multiple times.

```
@[1, 2, 3]
[e.g.] >>> 3

3 @ [1, 2, 3]
[e.g.] >>> [3, 1, 1]
```

**Random Selection (without replacement)**

This operator selects random elements from an iterable object. It does not replace elements when performing
multiple selections, so the same element may never appear more than once unless there are duplicates in the
original iterable. The unary version of `@!` is functionally identical to unary `@`.

```
3 @! [1, 2, 3]
[e.g.] >>> [1, 3, 2]
[e.g.] >>> [3, 2, 1]
```

----

**Exponentiation**

```
3 ** 2
>>> 9

-3 ** 2
>>> -9

(-3) ** 2
>>> 9
```

----

**Unary Plus**

This is a no-op, in accordance with the specification of most programming languages.

```
+4
>>> 4

+"fizz"
>>> "fizz"
```

**Unary Minus**

```
-4
>>> -4

-"fizz"
>>> "zzif"

-[6, 5, 4]
>>> [4, 5, 6]
```

**Bitwise Not**

This also calculates the conjugate of a complex number.

```
~4
>>> -5

~(5+1j)
>>>(5-1j)
```

----

**Multiplication**

```
6 * 8
>>> 48

2 * "fizz"
>>> "fizzfizz"
```

**Division**

```
7 / 2
>>> 3.5

7 // 2
>>> 3
```

**Remainder**

```
7 % 2
>>> 1
```

**Shift**

In addition to the bitwise shift behavior on integers, this acts as a way to append or prepend an element to
a list, although you receive a modified copy of the list, rather than the original.

```
7 << 1
>>> 14

7 >> 1
>>> 3

[1, 2, 3] >> 4
>>> [4, 1, 2, 3]

[1, 2, 3] << 4
>>> [1, 2, 3, 4]
```

----

**Addition**

```
1 + 1
>>> 2

"abc" + "def"
>>> "abcdef"

[1, 2, 3] + [4, 5, 6]
>>> [1, 2, 3, 4, 5, 6]
```

**Subtraction**

```
3 - 2
>>> 1

[1, 1, 2, 3, 1, 4, 5] - 1
>>> [1, 2, 3, 1, 4, 5]

"poofoof" - "oo"
>>> "pfoof"
```

**Catenation**

```
1 $ 5
>>> 15
```

----

**Bitwise AND**

```
12 & 5
>>> 4
```

**Bitwise XOR**

```
12 ^ 5
>>> 9
```

**Bitwise OR**

```
12 | 5
>>> 13
```

----

TODO: Comparison & onward