import unittest
from dicelang.interpreter import DicelangInterpreter
from dicelang.parser import parser
from dicelang import exceptions

Dicelang = DicelangInterpreter()


def execute(command):
    syntax_tree = parser.parse(command)
    return Dicelang.execute_test(syntax_tree)


class Addition(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(3, execute("1 + 2"))
        self.assertEqual((1-2j), execute("1 + -2j"))

    def test_collection(self):
        self.assertEqual({'a': 1, 'b': 2}, execute("{'a': 1} + {'b': 2}"))
        self.assertEqual(['a', 'b', 'c'], execute("['a', 'b'] + ['c']"))
        self.assertEqual((1, 2, 3), execute("() + (1, 2, 3,)"))
        self.assertEqual({1, 2, 3}, execute("{1, 2} + {3}"))

    def test_string(self):
        self.assertEqual('beefheart', execute("'beef' + 'heart'"))


class Subtraction(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(3, execute("8 - 5"))
        self.assertEqual((1-2j), execute("1 - 2j"))

    def test_collection(self):
        self.assertEqual({'a': 1}, execute("{'a': 1, 'b': 2} - 'b'"))
        self.assertEqual(['a', 'b', 'c'], execute("['a', 'a', 'b', 'c'] - 'a'"))
        self.assertEqual((1, 2), execute('(1, 2, 3) - 3'))
        self.assertEqual({1, 2}, execute('{1, 2, 3} - 3'))

    def test_string(self):
        self.assertEqual('helo world', execute("'hello world' - 'l'"))


class Multiplication(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(42, execute('6 * 7'))
        self.assertEqual((3+3j), execute('(1+1j) * 3'))

    def test_collection(self):
        self.assertEqual([3, 2, 1], execute('[1, 2, 3] * -1'))
        self.assertEqual((1, 1, 1), execute('(1,) * 3'))

    def test_string(self):
        self.assertEqual("olleh", execute('-1 * "hello"'))


class Division(unittest.TestCase):
    def test_numeric(self):
        self.assertEqual(2.5, execute('5 / 2'))
        self.assertEqual(2, execute('5 // 2'))
        self.assertEqual(1, execute('5 % 2'))

    def test_collection(self):
        self.assertEqual({1, 2}, execute("{1, 2, 3} / 3"))
        self.assertEqual([1, 3], execute("[1, 2, 2, 2, 3] / 2"))
        self.assertEqual({'a': 1}, execute("{'a': 1, 'b': 2} / 'b'"))

    def test_string(self):
        self.assertEqual("spn", execute("'spoon' / 'o'"))


class Dice(unittest.TestCase):
    def test_scalar(self):
        self.assertIn(execute("1d6"), set(range(7)))
        self.assertIn(execute("3d6"), set(range(3, 19)))

    def test_vector(self):
        self.assertEqual(3, execute("len(3r6)"))


class Function(unittest.TestCase):
    def test_nullary(self):
        self.assertEqual(4, execute("(() -> 4)()"))

    def test_unary(self):
        self.assertEqual(4, execute("((x) -> x)(4)"))

    def test_binary(self):
        self.assertEqual(4, execute("((x, y) -> x + y)(2, 2)"))

    def test_variadic(self):
        self.assertEqual(4, execute("((*a) -> sum(a))(1, 1, 1, 1)"))


class Scope(unittest.TestCase):
    def test_block(self):
        code = """begin
            x = 1;
            z = begin
                y = 2;
                x = 3;
                begin
                    x + y
                end
            end;
            x + z
        end"""
        self.assertEqual(8, execute(code))


class Assignment(unittest.TestCase):
    def test_single(self):
        self.assertEqual(5, execute('x = 5'))

    def test_unpack(self):
        self.assertEqual((1, 2, 3), execute('x, y, z = (1, 2, 3)'))

    def test_unpack_right(self):
        self.assertEqual((1, 2, (3, 4, 5)), execute('x, y, *z = (1, 2, 3, 4, 5)'))

    def test_unpack_middle(self):
        self.assertEqual((1, (2, 3, 4), 5), execute('x, *y, z = (1, 2, 3, 4, 5)'))

    def test_unpack_left(self):
        self.assertEqual(((1, 2, 3), 4, 5), execute('*x, y, z = (1, 2, 3, 4, 5)'))

    def test_unpacking(self):
        self.assertEqual(((1,2), 3, 4, 5), execute("*w, x, y, z = (1, 2, 3, 4, 5)"))
        self.assertEqual((1, 2, (3,), 4, 5), execute("v, w, *x, y, z = (1, 2, 3, 4, 5)"))
        self.assertEqual((1, 2, 3, (4, 5)), execute("w, x, y, *z = (1, 2, 3, 4, 5)"))


class Deletion(unittest.TestCase):
    def test_delete(self):
        code = """
        x = 1;
        y = 2;
        z = 3;
        delete x, y, z;
        """
        self.assertEqual((1, 2, 3), execute(code))


if __name__ == '__main__':
    unittest.main()
