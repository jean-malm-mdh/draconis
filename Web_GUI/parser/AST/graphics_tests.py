import unittest

from Web_GUI import Point, Rectangle


class GraphicalTests(unittest.TestCase):
    def test_can_create_rectangle(self):
        rect = Rectangle(Point(25, 35), Point(30, 45))
        self.assertEqual(rect.getPosition(), (25, 35))
        self.assertEqual(rect.getSize(), Point(5, 10))

    def test_can_check_rectangle_overlap(self):
        rect1 = Rectangle(Point(25, 35), Point(30, 45))
        rect2 = Rectangle(Point(28, 30), Point(38, 50))
        expected = Rectangle(Point(28, 35), Point(30, 45))
        self.assertEqual(expected, Rectangle.check_overlap(rect1, rect2))
        rect3 = Rectangle(Point(10, 10), Point(20, 20))
        self.assertIsNone(Rectangle.check_overlap(rect1, rect3))


if __name__ == "__main__":
    unittest.main()
