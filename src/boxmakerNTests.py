import unittest
from boxmakerNLib import BoxMaker, line, Path, Point, circleArc, Move
import inkex


class TestBoxMaker(unittest.TestCase):

    def test_path1(self):
        test_path = Path();

        test_path.append(line(Point(0, 10)))
        test_path.append(line(Point(0, 10)))
        test_path.append(line(Point(10, 0)))

        self.assertEqual(3, len(test_path))

        self.assertEqual(2, len(test_path.simplify()))

    def test_roundedEdges(self):
        test_path = Path();

        test_path.append(Move(Point(0, 10)))
        test_path.append(line(Point(0, 10)))
        test_path.append(line(Point(0, 10)))
        test_path.append(line(Point(10, 0)))
        test_path.append(line(Point(0, 10)))
        test_path.append(line(Point(-10, 0)))

        roundedPath = test_path.addRoundedEdgeAt(5.0, Point(10, 30))
        self.assertEqual(7, len(roundedPath))
        roundedPath = roundedPath.addRoundedEdgeAt(5.0, Point(10, 40))
        self.assertEqual(8, len(roundedPath))

    def test_roundedEdges2(self):
        test_path = Path();

        test_path.append(Move(Point(0, 10)))
        test_path.append(line(Point(10, 0)))
        test_path.append(line(Point(0, 10)))

        roundedPath = test_path.addRoundedEdgeAt(5.0, Point(10, 10))
        self.assertEqual(4, len(roundedPath))

    def test_paths(self):
        test_box_maker = BoxMaker()

        test_path = Path();
        test_path.append(line(Point(0, 10)))

        test_path.append(
            circleArc(5.0, Point(-(test_box_maker.thickness / 2), test_box_maker.thickness / 2 - test_box_maker.thickness)))

        l = test_path.finalPosition()

        rawPath = test_box_maker.boxFrames(test_box_maker.boxHeight, Direction.up)

        for atom in rawPath:
            inkex.debug("Element %.2f/%.2f" % (atom.p.x, atom.p.y))

        test_path.extend(rawPath)

        test_path.simplify()

    def nontest_simplify(self):
        test_box_maker = BoxMaker()
        test_box_maker.boxWidth = 200.0
        test_box_maker.boxDepth = 100.0
        test_box_maker.boxHeight = 70.0
        test_box_maker.thickness = 4.0

        test_box_maker.frameEdgesMin = 5.0
        test_box_maker.frameLength = 10.0;
        test_box_maker.hingeCircleFactor = 1.5;

        test_box_maker.drawBox()


if __name__ == '__main__':
    unittest.main()
