import os
import unittest

from src import stats_utils as su

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample_scores.csv")


class TestStatsUtils(unittest.TestCase):

    def test_mean(self):
        self.assertAlmostEqual(su.mean([1, 2, 3, 4]), 2.5)

    def test_median_odd_and_even(self):
        self.assertEqual(su.median([3, 1, 2]), 2)
        self.assertEqual(su.median([4, 1, 3, 2]), 2.5)

    def test_variance_and_std(self):
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        self.assertAlmostEqual(su.variance(values), 4.0)
        self.assertAlmostEqual(su.std_dev(values), 2.0)

    def test_min_max_normalize(self):
        self.assertEqual(su.min_max_normalize([0, 5, 10]), [0.0, 0.5, 1.0])
        self.assertEqual(su.min_max_normalize([3, 3]), [0.0, 0.0])

    def test_z_score(self):
        z = su.z_score([1, 2, 3, 4, 5])
        self.assertAlmostEqual(su.mean(z), 0.0)
        self.assertAlmostEqual(su.std_dev(z), 1.0)

    def test_describe_keys(self):
        d = su.describe([1, 2, 3])
        self.assertEqual(set(d), {"count", "mean", "median", "std", "min", "max"})

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            su.mean([])

    def test_non_numeric_raises(self):
        with self.assertRaises(TypeError):
            su.mean([1, "two", 3])

    def test_load_column(self):
        hours = su.load_column(DATA_PATH, "hours_studied")
        self.assertEqual(len(hours), 6)
        self.assertEqual(hours[0], 2.0)


if __name__ == "__main__":
    unittest.main()
