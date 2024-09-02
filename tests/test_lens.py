from unittest import TestCase

from exprlens import arg
from exprlens import args
from exprlens import kwargs


class TestExamples(TestCase):

    def test_lens_basic(self):
        # Basic usage

        # Lens for getting the first item in the first argument from a call:
        first = arg[0]

        # Getter can be accessed using the `get` method or by calling (`__call__`):
        self.assertEqual(first.get([0, 1, 2, 3]), 0)
        self.assertEqual(first([0, 1, 2, 3]), 0)

        # Setter can be accessed using the `set` method.
        self.assertEqual(first.set([0, 1, 2, 3], val=42), [42, 1, 2, 3])

    def test_lens_expressions(self):
        # Expressions.

        # Lens that first grabs the first two items in the first argument and adds them:
        plusfirsts = arg[0] + arg[1]

        self.assertEqual(plusfirsts([1, 2, 3, 4]), 3)

        # Note that once expression lenses are constructed, `set` can no longer be used on them.
        with self.assertRaises(ValueError):
            plusfirsts.set([1, 2, 3, 4], val=42)  # Raises an exception.

        # Literals/constants: Expression lenses can involve literals/constants.
        plusone = arg + 1
        self.assertEqual(list(map(plusone, [1, 2, 3])),  [2, 3, 4])

    def test_lens_validation(self):
        # Validation

        # Lenses can be validate on construction:
        args[0]  # ok
        with self.assertRaises(ValueError):
            args["something"]  # error

        kwargs["something"]  # ok
        with self.assertRaises(ValueError):
            kwargs[0]  # error

        # Lenses can be validated on use:

        # Lens that gets a key from the first argument, thus the first argument must be a mapping:
        firstkey = arg["something"]
        firstkey.get({"something": 42})  # ok

        # Will fail if the first argument is not a mapping:
        with self.assertRaises(ValueError):
            firstkey.get([1, 2, 3])  # error
