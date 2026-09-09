"""Compatibility entry point; preferred: python -m unittest discover -s tests."""

import unittest

from tests import test_acceptance

if __name__ == "__main__":
    unittest.main(module=test_acceptance, verbosity=2)
