import unittest
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser
from dicelang.script import Flattener
from dicelang.exceptions import ImpossibleDice

di = DicelangInterpreter()
fl = Flattener()

def execute(s: str):
    ast = parser.parse(s)
    ast_flat = fl.transform(ast)
    return di.execute(ast_flat)


class TestLiterals(unittest.TestCase):
    def test_integer(self):
        r = execute("1")
        self.assertTrue(r.unwrap_eq(1))

    def test_float(self):
        r = execute("0.2")
        self.assertTrue(r.unwrap_eq(0.2))

    def test_string(self):
        r = execute("''")
        self.assertTrue(r.unwrap_eq(''))
        r = execute("'foobar'")
        self.assertTrue(r.unwrap_eq('foobar'))

    def test_list(self):
        r = execute("[]")
        self.assertTrue(r.unwrap_eq([]))
        r = execute("[1, 2, 3]")
        self.assertTrue(r.unwrap_eq([1, 2, 3]))
        r = execute("[1 to 9]")
        self.assertTrue(r.unwrap_eq(list(range(1, 9))))
        r = execute("[1 through 9]")
        self.assertTrue(r.unwrap_eq(list(range(1, 10))))

    def test_dict(self):
        r = execute("{}")
        self.assertTrue(r.unwrap_eq({}))
        r = execute("{1:2}")
        self.assertTrue(r.unwrap_eq({1: 2}))

    def test_set(self):
        r = execute("set()")
        self.assertTrue(r.unwrap_eq(set()))
        r = execute("{1, 2}")
        self.assertTrue(r.unwrap_eq({1, 2}))

    def test_tuple(self):
        r = execute("()")
        self.assertTrue(r.unwrap_eq(()))
        r = execute("(1,)")
        self.assertTrue(r.unwrap_eq((1,)))
        r = execute("(1,2,3)")
        self.assertTrue(r.unwrap_eq((1,2,3)))

    def test_boolean(self):
        r = execute("True")
        self.assertTrue(r.unwrap())
        r = execute("False")
        self.assertFalse(r.unwrap())

    def test_complex(self):
        r = execute("1j")
        self.assertTrue(r.unwrap_eq(1j))
        r = execute("2+1j")
        self.assertTrue(r.unwrap_eq(2+1j))

    def test_undefined(self):
        r = execute('Undefined')
        self.assertTrue(repr(r.unwrap()) == 'Undefined')


class TestMathematics(unittest.TestCase):
    def test_negative(self):
        r = execute('-5')
        self.assertTrue(r.unwrap_eq(-5))
        r = execute('-"abc"')
        self.assertTrue(r.unwrap_eq('cba'))
        r = execute('-(1, 2, 3)')
        self.assertTrue(r.unwrap_eq((3, 2, 1)))

    def test_add(self):
        r = execute("1 + 2")
        self.assertTrue(r.unwrap_eq(3))
        r = execute("[1] + [2]")
        self.assertTrue(r.unwrap_eq([1, 2]))
        r = execute("'1' + '2'")
        self.assertTrue(r.unwrap_eq('12'))

    def test_subtract(self):
        r = execute("1 - 2")
        self.assertTrue(r.unwrap_eq(-1))
        r = execute("[1, 2, 3] - 1")
        self.assertTrue(r.unwrap_eq([2, 3]))
        r = execute("'abc' - 'b'")
        self.assertTrue(r.unwrap_eq('ac'))
        r = execute("2.5 - 1.2")
        self.assertTrue(r.unwrap_eq(1.3))
        r = execute("{1, 2, 3} - 3")
        self.assertTrue(r.unwrap_eq({1, 2}))

    def test_catenate(self):
        r = execute("15 $ 15")
        self.assertTrue(r.unwrap_eq(1515))
        r = execute("15 $ 0")
        self.assertTrue(r.unwrap_eq(150))
        r = execute("15.0 $ 14.1")
        self.assertTrue(r.unwrap_eq(1514))
        r = execute("15.0 $ -14.1")
        self.assertFalse(r)

    def test_divide(self):
        r = execute("15 / 2")
        self.assertTrue(r.unwrap_eq(15 / 2))
        r = execute('15 / 3')
        self.assertTrue(r.unwrap_eq(15 / 3))
        r = execute('{1: 2} / 1')
        self.assertTrue(r.unwrap_eq({}))

    def test_intdivide(self):
        r = execute('15 // 2')
        self.assertTrue(r.unwrap_eq(15 // 2))

    def test_remainder(self):
        r = execute('5 % 3')
        self.assertTrue(r.unwrap_eq(5 % 3))
        r = execute('"%s" % 5')
        self.assertTrue(r.unwrap_eq("5"))

    def test_multiply(self):
        r = execute('5 * 3')
        self.assertTrue(r.unwrap_eq(15))
        r = execute('5 * "abc"')
        self.assertTrue(r.unwrap_eq(5 * 'abc'))
        r = execute('"abc" * -2')
        self.assertTrue(r.unwrap_eq('cbacba'))
        r = execute('(1, 2, 3) * 2')
        self.assertTrue(r.unwrap_eq((1, 2, 3) * 2))
        r = execute("-2 * (1, 2, 3)")
        self.assertTrue(r.unwrap_eq((3, 2, 1, 3, 2, 1)))

    def test_bitwise_not(self):
        r = execute('~1')
        self.assertTrue(r.unwrap_eq(~1))
        r = execute("~(2-1j)")
        self.assertTrue(r.unwrap_eq((2-1j).conjugate()))

    def test_shifts(self):
        r = execute('1 << 1')
        self.assertTrue(r.unwrap_eq(1 << 1))
        r = execute('4 >> 1')
        self.assertTrue(r.unwrap_eq(4 >> 1))
        r = execute('[1, 2, 3] << 4')
        self.assertTrue(r.unwrap_eq([1, 2, 3, 4]))
        r = execute('[1, 2, 3] >> 0')
        self.assertTrue(r.unwrap_eq([0, 1, 2, 3]))

    def test_exponents(self):
        r = execute("2 ** 4")
        self.assertTrue(r.unwrap_eq(2 ** 4))
        r = execute('2 ** 3 ** 1')
        self.assertTrue(r.unwrap_eq(2 ** 3 ** 1))
        r = execute('-5 ** 2')
        self.assertTrue(r.unwrap_eq(-5 ** 2))


class TestSpecials(unittest.TestCase):
    def test_sum_or_join(self):
        r = execute('&[0 through 4]')
        self.assertTrue(r.unwrap_eq(10))
        r = execute('&["a", "b", "c"]')
        self.assertTrue(r.unwrap_eq('abc'))

    def test_coinflip(self):
        # NOTE: This has a 1 in 2**100 chance to fail.
        unwrapped_results = []
        for _ in range(100):
            unwrapped_results.append(execute('1 ! 2').unwrap())
        self.assertEqual(set(unwrapped_results), {1, 2})

    def test_random_selection(self):
        result_pool = {1, 2, 3, 4, 5}

        r = execute("@[1, 2, 3, 4, 5]")
        self.assertTrue(r.unwrap() in result_pool)
        r = execute("@![1, 2, 3, 4, 5]")
        self.assertTrue(r.unwrap() in result_pool)

        r = execute('5 @ [1, 2, 3, 4, 5]')
        self.assertTrue(set(r.unwrap()) <= result_pool)
        r = execute('5 @! [1, 2, 3, 4, 5]')
        self.assertTrue(set(r.unwrap()) == result_pool)

class TestDice(unittest.TestCase):
    def test_die_binary(self):
        r = execute('3d6')
        self.assertTrue(3 <= r.unwrap() <= 18)
        self.assertRaises(ImpossibleDice, lambda: execute('0d6').reraise())

    def test_roll_binary(self):
        r = execute('3r6')
        self.assertTrue(len(dice := r.unwrap()) == 3)
        for d in dice:
            self.assertTrue(1 <= d <= 6)
        self.assertRaises(ImpossibleDice, lambda: execute('0r6').reraise())

    def test_roll_ternary(self):
        r = execute('3r6kh2')
        self.assertEqual(len(r.unwrap()), 2)
        r = execute('3r6xl2')
        self.assertEqual(len(r.unwrap()), 1)
        r = execute('3r6xh2')
        self.assertEqual(len(r.unwrap()), 1)
        r = execute('3r6kl2')
        self.assertEqual(len(r.unwrap()), 2)

    def test_die_ternary(self):
        r = execute('3d6kh2')
        self.assertTrue(2 <= r.unwrap() <= 12)
        r = execute('3d6xl2')
        self.assertTrue(1 <= r.unwrap() <= 6)
        r = execute('3d6xh2')
        self.assertTrue(1 <= r.unwrap() <= 6)
        r = execute('3d6kl2')
        self.assertTrue(2 <= r.unwrap() <= 12)


if __name__ == '__main__':
    unittest.main()
