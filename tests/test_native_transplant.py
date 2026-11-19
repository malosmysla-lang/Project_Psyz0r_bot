from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prepare_v2_native_candidate import transplant


class NativeTransplantTests(unittest.TestCase):
    def test_unrelated_deployed_changes_survive(self):
        result,ops=transplant('begin\nold\nend\n','begin\nfixed\nend\n','custom\nbegin\nold\nend\nlegacy\n')
        self.assertEqual(result,'custom\nbegin\nfixed\nend\nlegacy\n')
        self.assertEqual(len(ops),1)

    def test_insert_does_not_remove_inherited_block(self):
        result,_=transplant('begin\nend\n','begin\nnew\nend\n','begin\ninherited\nend\n')
        self.assertEqual(result,'begin\nnew\ninherited\nend\n')

    def test_ambiguous_edit_refuses_to_guess(self):
        with self.assertRaises(RuntimeError):transplant('old\n','fixed\n','old\nold\n')


if __name__=='__main__':unittest.main()
