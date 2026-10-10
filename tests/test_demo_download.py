import struct,unittest
from tools.download_bloodrun_corpus import framed
class DemoFramingTests(unittest.TestCase):
 def test_valid(self):self.assertTrue(framed(struct.pack('<ii',1,3)+b'abc'+struct.pack('<ii',-1,-1)))
 def test_truncated(self):self.assertFalse(framed(struct.pack('<ii',1,4)+b'abc'))
 def test_html(self):self.assertFalse(framed(b'<html>login page</html>'))
 def test_oversized_frame(self):self.assertFalse(framed(struct.pack('<ii',1,200000)))
 def test_empty(self):self.assertFalse(framed(b''))
 def test_trailing_garbage(self):self.assertFalse(framed(struct.pack('<ii',1,1)+b'x'+struct.pack('<ii',-1,-1)+b'garbage'))
if __name__=='__main__':unittest.main()
