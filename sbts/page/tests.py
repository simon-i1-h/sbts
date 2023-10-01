from django.test import TestCase

from .templatetags.pretty_filters import pretty_nbytes


class PrettyNbytesTest(TestCase):
    def test_pretty_nbytes_0(self):
        self.assertEqual(pretty_nbytes(0), '0 B')

    def test_pretty_nbytes_1(self):
        self.assertEqual(pretty_nbytes(1), '1 B')

    def test_pretty_nbytes_2(self):
        self.assertEqual(pretty_nbytes(2), '2 B')

    def test_pretty_nbytes_1023(self):
        '''
        1023までは単位が大きくならない。
        '''
        self.assertEqual(pretty_nbytes(1023), '1,023 B')

    def test_pretty_nbytes_1kib(self):
        '''
        1024の位ごとに単位が大きくなる。
        '''
        self.assertEqual(pretty_nbytes(1024), '1 kiB')

    def test_pretty_nbytes_fraction(self):
        '''
        端数は小数第1位まで有効。
        '''
        self.assertEqual(pretty_nbytes(1134), '1.1 kiB')

    def test_pretty_nbytes_fraction_rounddown(self):
        '''
        端数が出て、かつ小数第1位が0になる場合は省略。
        '''
        self.assertEqual(pretty_nbytes(1034), '1 kiB')

    def test_pretty_nbytes_kib_complex(self):
        '''
        複合: 桁上がり、2以上、端数
        '''
        self.assertEqual(pretty_nbytes(2600), '2.5 kiB')

    def test_pretty_nbytes_1023kib(self):
        '''
        1023までは単位が大きくならない。
        '''
        self.assertEqual(pretty_nbytes(1023 * 1024), '1,023 kiB')

    def test_pretty_nbytes_1mib(self):
        '''
        単位: k->M
        '''
        self.assertEqual(pretty_nbytes(1024 ** 2), '1 MiB')

    def test_pretty_nbytes_1023mib(self):
        '''
        1023までは単位が大きくならない。
        '''
        self.assertEqual(pretty_nbytes(1023 * (1024 ** 2)), '1,023 MiB')

    def test_pretty_nbytes_1gib(self):
        '''
        単位: M->G
        '''
        self.assertEqual(pretty_nbytes(1024 ** 3), '1 GiB')

    def test_pretty_nbytes_1023gib(self):
        '''
        1023までは単位が大きくならない。
        '''
        self.assertEqual(pretty_nbytes(1023 * (1024 ** 3)), '1,023 GiB')

    def test_pretty_nbytes_1tib(self):
        '''
        単位: G->T
        '''
        self.assertEqual(pretty_nbytes(1024 ** 4), '1 TiB')

    def test_pretty_nbytes_1023tib(self):
        '''
        1023までは単位が大きくならない。
        '''
        self.assertEqual(pretty_nbytes(1023 * (1024 ** 4)), '1,023 TiB')

    def test_pretty_nbytes_1pib(self):
        '''
        単位: T->P
        '''
        self.assertEqual(pretty_nbytes(1024 ** 5), '1 PiB')

    def test_pretty_nbytes_1023pib(self):
        '''
        1023までは単位が大きくならない。
        '''
        self.assertEqual(pretty_nbytes(1023 * (1024 ** 5)), '1,023 PiB')

    def test_pretty_nbytes_1024pib(self):
        '''
        単位はPで最大なので、それ以上は単に数が大きくなる。
        '''
        self.assertEqual(pretty_nbytes(1024 ** 6), '1,024 PiB')

    def test_pretty_nbytes_large_pib_complex(self):
        '''
        複合: 1024以上のPiB、端数
        '''
        self.assertEqual(pretty_nbytes(42 * (1024 ** 6) + 900 * (1024 ** 4)), '43,008.9 PiB')
