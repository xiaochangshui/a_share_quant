import unittest


class PackageImportTest(unittest.TestCase):
    def test_exposes_package_version(self):
        import a_share_quant

        self.assertEqual(a_share_quant.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
