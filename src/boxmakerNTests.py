import unittest
from boxmakerLib import BoxMaker, line, Path, Point, circleArc, Move
import inkex


class TestBoxMaker(unittest.TestCase):

    def test_path1(self):
      testPath = Path();
      
      testPath.append(line(Point(0,10)))
      testPath.append(line(Point(0,10)))
      testPath.append(line(Point(10,0)))
      
      self.assertEqual(3, len(testPath))
      
      self.assertEqual(2, len(testPath.simplify()))
      
    def test_roundedEdges(self):
      testPath = Path();
      
      testPath.append(Move(Point(0,10)))
      testPath.append(line(Point(0,10)))
      testPath.append(line(Point(0,10)))
      testPath.append(line(Point(10,0)))
      testPath.append(line(Point(0,10)))
      testPath.append(line(Point(-10, 0)))
     
      roundedPath = testPath.addRoundedEdgeAt(5.0, Point(10,30))
      self.assertEqual(7, len(roundedPath))
      roundedPath = roundedPath.addRoundedEdgeAt(5.0, Point(10,40))
      self.assertEqual(8, len(roundedPath))

    def test_roundedEdges2(self):
      testPath = Path();
      
      testPath.append(Move(Point(0,10)))
      testPath.append(line(Point(10,0)))
      testPath.append(line(Point(0,10)))
     
      roundedPath = testPath.addRoundedEdgeAt(5.0, Point(10,10))
      self.assertEqual(4, len(roundedPath))
      
      
  
    def test_paths(self):
      testBoxMaker = BoxMaker()

      testPath = Path();
      testPath.append(line(Point(0,10)))
 
      testPath.append(circleArc(5.0, Point(-(testBoxMaker.thickness/2), testBoxMaker.thickness/2 - testBoxMaker.thickness)))

      l = testPath.finalPosition()
     
      rawPath = testBoxMaker.boxFrames(testBoxMaker.boxHeight , Direction.up)
      
      for atom in rawPath : 
        inkex.debug("Element %.2f/%.2f" % (atom.p.x, atom.p.y))

      testPath.extend(rawPath)    
      
 
      testPath.simplify()

    def nontest_simplify(self):
        testBoxMaker = BoxMaker()
        testBoxMaker.boxWidth = 200.0
        testBoxMaker.boxDepth = 100.0
        testBoxMaker.boxHeight = 70.0
        testBoxMaker.thickness = 4.0  

        testBoxMaker.frameEdgesMin = 5.0
        testBoxMaker.frameLength = 10.0;
        testBoxMaker.hingeCircleFactor = 1.5;

        testBoxMaker.drawBox()


if __name__ == '__main__':
    unittest.main()
