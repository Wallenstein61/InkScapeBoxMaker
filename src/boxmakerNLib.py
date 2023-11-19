#! /usr/bin/env python
"""
boxmaker.py
A module for creating a box with laser cut 

Copyright (C) 2018 Michael Breu; Michael.Breu@arctis.at

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the GNU General Public License
write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Updated for InkScape 1.0 by Leon Palnau 4/15/2021
Updated for InkScape 1.2 by Michael Breu 12/04/2022
"""

__version__ = "1.0"

from datetime import datetime
import sys, inkex, simplestyle, gettext
import math, abc
from lxml import etree

_ = gettext.gettext


def draw_line(parent, XYstring):  # Draw lines from a list
    name = 'part'
    style = {'stroke': '#000000', 'fill': 'none', 'stroke-width': self.svg.unittouu("0.1 mm")}
    drw = {'style': simplestyle.formatStyle(style), inkex.addNS('label', 'inkscape'): name, 'd': XYstring}
    etree.SubElement(parent, inkex.addNS('path', 'svg'), drw)
    return


class BoxType:

    def __init__(self, description, has_hinges):
        self.description = description
        self.withHinges = has_hinges

    def has_hinges(self):
        return self.withHinges


withHinge = BoxType('Box with Hinges', True)
openBox = BoxType('just an open Box', False)
mobileLoader = BoxType('box for mobile Loader', True)
shelvedBox = BoxType('Box with shelves', False)


class Direction:
    up = dict([('frameMove', [0.0, 1.0]), ('walkIn', [1.0, 0.0]), ('walkOut', [-1.0, 0.0])])
    down = dict([('frameMove', [0.0, -1.0]), ('walkIn', [-1.0, 0.0]), ('walkOut', [1.0, 0.0])])
    left = dict([('frameMove', [1.0, 0.0]), ('walkIn', [0.0, -1.0]), ('walkOut', [0.0, 1.0])])
    right = dict([('frameMove', [-1.0, 0.0]), ('walkIn', [0.0, 1.0]), ('walkOut', [0.0, -1.0])])


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            # TODO: equality on real is difficult
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def add(self, x, y):
        return Point(self.x + x, self.y + y)


class SVGPathAtom:
    @abc.abstractmethod
    def toSVGString():
        pass

    @abc.abstractmethod
    def newPos(start_pos):
        ''' returns a new position from Startpos'''
        pass


class Move(SVGPathAtom):
    def __init__(self, p):
        self.p = p

    def toSVGString(self):
        return 'M %f %f' % (self.p.x, self.p.y)

    def newPos(self, start_pos):
        return self.p


class move(SVGPathAtom):
    def __init__(self, p):
        self.p = p

    def toSVGString(self):
        return "m %f %f" % (self.p.x, self.p.y)

    def newPos(self, start_pos):
        return start_pos.add(self.p.x, self.p.y)


class line(SVGPathAtom):
    def __init__(self, p):
        self.p = p

    def toSVGString(self):
        return "l %f %f" % (self.p.x, self.p.y)

    def newPos(self, start_pos):
        return start_pos.add(self.p.x, self.p.y)


class circleArc(SVGPathAtom):

    def __init__(self, r, endPoint, largeArc='1', sweepFlag='1'):
        self.r = r
        self.endPoint = endPoint
        self.largeArc = largeArc
        self.sweepFlag = sweepFlag

    def toSVGString(self):
        return "a %f %f 0 %s %s %f %f" % (
            self.r, self.r, self.largeArc, self.sweepFlag, self.endPoint.x, self.endPoint.y)

    def newPos(self, start_pos):
        # inkex.debug("start %.2f %.2f"% (start_pos.x, start_pos.y))
        end_pos = start_pos.add(self.endPoint.x, self.endPoint.y)
        # inkex.debug("  end %.2f %.2f"% (end_pos.x, end_pos.y))
        return end_pos


class Path(list):
    def __init__(self, *args):
        list.__init__(self, *args)

    def MoveTo(self, point):
        self.append(Move(point))

    def lineBy(self, point):
        self.append(line(point))

    def lineByWithCorner(self, radius, point):
        pos = self.finalPosition()
        self.append(line(point))
        return self.addRoundedEdgeAt(radius, pos)

    def translateToSVGd(self):
        s = ''
        for atoms in self:
            s = s + atoms.toSVGString() + ' '
        return s

    def finalPosition(self):
        pos = Point(0.0, 0.0)
        for atoms in self:
            pos = atoms.newPos(pos)
        return pos

    def simplify(self):
        """combines elements in the path which are identical"""
        result = Path()
        cursorElement = None
        for atom in self:
            if isinstance(atom, Move) or isinstance(atom, move) or isinstance(atom, circleArc):
                # inkex.debug("nope %s"% atom)
                if not cursorElement is None:
                    result.append(cursorElement)
                    cursorElement = None
                result.append(atom)
            elif isinstance(atom, line):
                # inkex.debug("trying %.2f %.2f" % (atom.p.x, atom.p.y))
                if cursorElement is None:
                    cursorElement = line(Point(atom.p.x, atom.p.y))
                else:
                    if atom.p.x == 0.0 and atom.p.y == 0.0:  # empty line
                        pass
                    elif cursorElement.p.x == 0.0 and atom.p.x == 0.0:
                        cursorElement.p.y = cursorElement.p.y + atom.p.y
                        # debug("combining %.2f"% cursorElement.p.y)

                    elif cursorElement.p.y == 0.0 and atom.p.y == 0.0:
                        cursorElement.p.x = cursorElement.p.x + atom.p.x
                        # inkex.debug("combining %.2f"% cursorElement.p.x)

                    else:  # nicht kombinierbar
                        result.append(cursorElement)
                        # inkex.debug("pushing")
                        cursorElement = line(Point(atom.p.x, atom.p.y))
            else:
                inkex.debug("this is an error %s" % atom)
        if not cursorElement is None:
            result.append(cursorElement)
        return result

        cursorElement = self[0]

    def addRoundedEdgeAt(self, radius, point, debug=False):
        """add a roundes Edge at position point"""
        pos = Point(0.0, 0.0)
        result = Path()
        skip = False
        for i in range(0, len(self)):
            atom = self[i]
            pos = atom.newPos(pos)
            if skip:
                skip = False
                continue
            if debug: inkex.debug(
                "Test %s  (%.2f, %.2f) against (%.2f, %.2f)" % (repr(i), point.x, point.y, pos.x, pos.y))
            if pos == point and isinstance(atom, line):

                lx = atom.p.x
                ly = atom.p.y
                if ly == 0.0:
                    if lx < 0.0:
                        nextLine = self[i + 1]
                        if isinstance(nextLine, line) and nextLine.p.x == 0.0:
                            if debug: inkex.debug("Here 1.1 %s" % (repr(i)))
                            shortenedLine = line(Point(lx + radius, ly))
                            if nextLine.p.y < 0.0:
                                arc = circleArc(radius, Point(-radius, -radius), '0', '1')
                                newNextLine = line(Point(nextLine.p.x, nextLine.p.y + radius))
                            else:
                                arc = circleArc(radius, Point(-radius, radius), '0', '0')
                                newNextLine = line(Point(nextLine.p.x, nextLine.p.y - radius))
                            result.append(shortenedLine)
                            result.append(arc)
                            result.append(newNextLine)
                            pos = nextLine.newPos(pos)
                            skip = True
                        else:
                            result.append(atom)
                    else:
                        nextLine = self[i + 1]
                        if isinstance(nextLine, line) and nextLine.p.x == 0.0:
                            if debug: inkex.debug("Here 1.2 %s" % (repr(i)))
                            shortenedLine = line(Point(lx - radius, ly))
                            if nextLine.p.y < 0.0:
                                arc = circleArc(radius, Point(radius, -radius), '0', '0')
                                newNextLine = line(Point(nextLine.p.x, nextLine.p.y + radius))
                            else:
                                arc = circleArc(radius, Point(radius, radius), '0', '0')
                                newNextLine = line(Point(nextLine.p.x, nextLine.p.y - radius))
                            result.append(shortenedLine)
                            result.append(arc)
                            result.append(newNextLine)
                            pos = nextLine.newPos(pos)
                            skip = True
                        else:
                            result.append(atom)
                elif lx == 0.0:
                    if ly < 0.0:
                        nextLine = self[i + 1]
                        if isinstance(nextLine, line) and nextLine.p.y == 0.0:
                            if debug: inkex.debug("Here 2.1 %s" % (repr(i)))
                            shortenedLine = line(Point(lx, ly + radius))
                            if nextLine.p.x < 0.0:
                                arc = circleArc(radius, Point(-radius, -radius), '0', '0')
                                newNextLine = line(Point(nextLine.p.x + radius, nextLine.p.y))
                            else:
                                arc = circleArc(radius, Point(radius, -radius), '0', '1')
                                newNextLine = line(Point(nextLine.p.x - radius, nextLine.p.y))
                            result.append(shortenedLine)
                            result.append(arc)
                            result.append(newNextLine)
                            pos = nextLine.newPos(pos)
                            skip = True
                        else:
                            result.append(atom)
                    else:
                        if debug: inkex.debug("Here 2.2 %s" % (repr(i)))
                        nextLine = self[i + 1]
                        if isinstance(nextLine, line) and nextLine.p.y == 0.0:
                            shortenedLine = line(Point(lx, ly - radius))
                            if nextLine.p.x < 0.0:
                                arc = circleArc(radius, Point(-radius, radius), '0', '1')
                                newNextLine = line(Point(nextLine.p.x + radius, nextLine.p.y))
                            else:
                                arc = circleArc(radius, Point(radius, radius), '0', '0')
                                newNextLine = line(Point(nextLine.p.x - radius, nextLine.p.y))
                            result.append(shortenedLine)
                            result.append(arc)
                            result.append(newNextLine)
                            pos = nextLine.newPos(pos)
                            skip = True
                        else:
                            result.append(atom)
            else:
                result.append(atom)
        return result


class BoxMaker(inkex.Effect):
    def __init__(self):
        self.boxType = withHinge
        self.boxWidth = 200.0
        self.boxDepth = 100.0
        self.boxHeight = 70.0
        self.thickness = 4.0
        self.shelfCount = 1

        self.frameEdgesMin = 5.0
        self.frameLength = 10.0
        self.hingeCircleFactor = 1.5
        self.debug = False

        # Call the base class constructor.
        inkex.Effect.__init__(self)
        # Define options - Must match to the <param> elements in the .inx file
        # just dummies for the tabs
        self.arg_parser.add_argument('--tab', action='store', dest='tab', type=str, default='mm',
                                     help='just a dummy')
        self.arg_parser.add_argument('--HingeAndFrame', action='store', dest='tab', type=str, default='mm',
                                     help='just a dummy')
        self.arg_parser.add_argument('--Development', action='store', dest='tab', type=str, default='mm',
                                     help='just a dummy')

        self.arg_parser.add_argument('--boxType', action='store', dest='boxType', type=str, default='openBox',
                                     help='Type of Box')
        self.arg_parser.add_argument('--unit', action='store', dest='unit', type=str, default='mm',
                                     help='units of measurement')

        self.arg_parser.add_argument('--box_width', action='store', type=float, dest='boxWidth', default=200.0,
                                     help='width of the box.')
        self.arg_parser.add_argument('--box_depth', action='store', type=float, dest='boxDepth', default=120.0,
                                     help='depth of the box.')
        self.arg_parser.add_argument('--box_height', action='store', type=float, dest='boxHeight', default=70.0,
                                     help='height of the box.')
        self.arg_parser.add_argument('--thickness', action='store', type=float, dest='thickness', default=0,
                                     help='thickness of the material.')
        self.arg_parser.add_argument('--shelfCount', action='store', type=int, dest='shelfCount', default=1,
                                     help='number of shelves.')

        self.arg_parser.add_argument('--frameEdgesMin', action='store', type=float, dest='frameEdgesMin', default=0,
                                     help='Minimum distance of frame to edge.')
        self.arg_parser.add_argument('--frameLength', action='store', type=float, dest='frameLength', default=0,
                                     help='Length of a frame.')
        self.arg_parser.add_argument('--hingeCircleFactor', action='store', type=float, dest='hingeCircleFactor',
                                     default=1.5, help='Size of hinge circle.')

        self.arg_parser.add_argument('--debug', action='store', type=bool, dest='debug', default='False',
                                     help='debug Info')

    def effect(self):
        if self.options.boxType == 'withHinge':
            self.boxType = withHinge
        elif self.options.boxType == 'openBox':
            self.boxType = openBox
        elif self.options.boxType == 'mobileLoader':
            self.boxType = mobileLoader
        elif self.options.boxType == 'openBoxWithShelves':
            self.boxType = shelvedBox

        unit = self.options.unit
        self.unit = unit
        # starting cut length. Will be adjusted for get an integer number of cuts in the y-direction.
        self.boxWidth = self.svg.unittouu(str(self.options.boxWidth) + unit)
        self.boxDepth = self.svg.unittouu(str(self.options.boxDepth) + unit)
        self.boxHeight = self.svg.unittouu(str(self.options.boxHeight) + unit)
        self.thickness = self.svg.unittouu(str(self.options.thickness) + unit)
        self.shelfcount = self.options.shelfCount

        self.frameEdgesMin = self.svg.unittouu(str(self.options.frameEdgesMin) + unit)
        self.frameLength = self.svg.unittouu(str(self.options.frameLength) + unit)
        self.hingeCircleFactor = self.options.hingeCircleFactor

        self.debug = self.options.debug

        self.backRestHeight = 150.0
        self.backRestWidth = 90.0

        self.supportDistance = 20.0
        self.distanceBetweenSupports = 50.0
        self.shelfHeight = 15.0

        self.shelfLength = 20.0
        self.usbWidth = 10.2
        self.usbDepth = 6.0
        self.usbHeight = 25.0

        self.inclination = 75.0
        self.inclinationRad = self.inclination * math.pi / 180.0

        # inkex.debug("Info. %.2f %.2f %s %.2f" % (self.boxWidth, self.frameLength, repr(self.debug), self.hingeCircleFactor))

        self.parent = self.svg.get_current_layer()

        self.drawBox()
        #    inkex.debug("Dict up " + repr( Direction.up['walkIn'][0]))

        #    inkex.debug('date %s' % self.printDate(datetime.now()))
        #    self.markPoints(Point(5.0,5.0), 'green')
        #    inkex.debug('boxFrame %s'%self.boxFrames(Point(40.0,40.0), 100.0, Direction.down, False).translateToSVGd())
        #    self.insertPath(self.boxFrames(Point(40.0,40.0), 100.0, Direction.down, False))

        if self.boxType == mobileLoader:
            self.drawMobileLoader()

    def drawMobileLoader(self):
        start = Point(10, 10)
        backRestStart = start.add(
            self.boxWidth + self.boxHeight + 1 * self.hingeCircleFactor * self.thickness + self.boxWidth + self.thickness,
            0)

        dx = math.tan(math.pi / 2 - self.inclinationRad) * self.thickness
        frameWidth = self.thickness / math.sin(self.inclinationRad)
        dxPlusd = dx / math.sin(self.inclinationRad) + self.thickness

        supportHeight = self.supportDistance * math.tan(self.inclinationRad)
        supportExtra = self.thickness / math.cos(self.inclinationRad)

        shelfSupportHeight = (self.shelfHeight / math.cos(self.inclinationRad) - (
                self.supportDistance + self.thickness)) / math.tan(self.inclinationRad)

        l = self.supportDistance * (supportHeight - shelfSupportHeight - dxPlusd) / supportHeight
        shelfBackLength = l / math.sin(self.inclinationRad)

        infoText = "Mobile Stand  --- Inclination: %.2f deg, Width: %.2fmm, Height: %.2fmm (Support Distance %.2fmm)" % \
                   (self.inclination, self.backRestWidth, self.backRestHeight, self.supportDistance)
        # inkex.debug('boxFrame %s'%infoText)
        self.insertText(infoText, backRestStart.add(-2, -2), 'orange')

        backRest = Path()

        frameDepthWithOverhead = frameWidth + self.thickness
        backRest.MoveTo(backRestStart)

        backRest.lineBy(Point(0, self.backRestHeight + frameDepthWithOverhead))
        backRest.append(circleArc(self.thickness, Point(self.thickness, self.thickness), '0', '0'))
        backRest.lineBy(Point(self.backRestWidth - 2 * self.thickness, 0))
        backRest.append(circleArc(self.thickness, Point(self.thickness, -self.thickness), '0', '0'))
        backRest.lineBy(Point(0, -self.backRestHeight - frameDepthWithOverhead))
        backRest.extend(self.boxFrames(self.backRestWidth, Direction.right, True, frameDepthWithOverhead))

        self.insertPath(backRest.simplify(), 'orange')

        nrInOutFrames = int(
            math.floor((self.backRestWidth - (self.frameEdgesMin * 2) - self.frameLength) / self.frameLength))
        nrFrames = int(math.floor(nrInOutFrames / 2))
        remainder = (self.backRestWidth - ((nrFrames * 2) * self.frameLength)) / 2.0

        supportFrameWidth = self.thickness * (math.tan(self.inclinationRad) + math.cos(self.inclinationRad))
        boxStart = backRestStart.add(remainder + self.frameLength / 2,
                                     frameDepthWithOverhead + supportHeight / math.sin(self.inclinationRad))
        for i in range(nrFrames):
            self.insertRect(boxStart, self.frameLength, supportFrameWidth, 'orange')
            boxStart = boxStart.add(self.frameLength * 2, 0)

        shelfFrameWidth = self.shelfHeight - self.thickness * (
                math.cos(self.inclinationRad) / math.sin(self.inclinationRad))
        boxStart = backRestStart.add(self.backRestWidth / 4, frameDepthWithOverhead + shelfFrameWidth)
        self.insertRect(boxStart, self.backRestWidth / 2, self.thickness, 'orange')

        supportStart = backRestStart.add(
            self.backRestWidth + self.thickness, 0)
        support = Path()
        support.MoveTo(supportStart)

        support.lineBy(Point(0, supportHeight + self.thickness + supportExtra))
        # self.markPoints(support.finalPosition(), 'blue')
        support.extend(self.boxFrames(self.backRestWidth, Direction.left, True, supportExtra))
        support.lineBy(Point(0, -(supportHeight + self.thickness + supportExtra)))
        support.extend(self.boxFrames(self.backRestWidth, Direction.right, True, self.thickness))
        self.insertPath(support.simplify(), 'orange')

        boxStart = supportStart.add((self.backRestWidth - self.frameLength) / 2, shelfSupportHeight + self.thickness)
        self.insertRect(boxStart, self.frameLength, dxPlusd, 'orange')

        shelfStart = supportStart.add(self.backRestWidth + self.thickness, 0)
        halfWidth = self.backRestWidth / 2.0
        shelf = Path()

        smallradius = self.usbDepth / 2
        smallerradius = smallradius / 2
        plugoffset = smallerradius
        shelf.MoveTo(shelfStart.add(self.thickness, 0))
        shelf.lineBy(Point(halfWidth - self.thickness - 2 * smallradius, 0))
        shelf.append(circleArc(smallradius, Point(smallradius, smallradius), '0'))
        shelf.lineBy(Point(0, self.shelfLength - smallradius - self.usbDepth - plugoffset))
        self.markPoints(shelf.finalPosition(), 'blue')

        # shelf.append(circleArc(smallerradius, Point(-smallerradius, smallerradius), '0'))
        shelf = shelf.lineByWithCorner(smallerradius, Point(-(self.usbWidth / 2 - self.usbDepth / 2), 0))

        # shelf = shelf.addRoundedEdgeAt(smallerradius, edge)

        shelf.lineBy(Point(0, self.usbDepth))
        shelf = shelf.lineByWithCorner(smallerradius, Point(self.usbWidth, 0))
        shelf = shelf.lineByWithCorner(smallerradius, Point(0, -self.usbDepth))

        shelf.lineBy(Point(-(self.usbWidth / 2.0 - self.usbDepth / 2.0), 0))
        shelf = shelf.lineByWithCorner(smallerradius, Point(0, -(self.shelfLength - self.usbDepth) + plugoffset))
        self.markPoints(shelf.finalPosition(), 'blue')
        shelf = shelf.lineByWithCorner(smallradius, Point(halfWidth - self.thickness - smallradius, 0))
        shelf.append(circleArc(self.thickness, Point(self.thickness, self.thickness), '0'))
        shelf.lineBy(Point(0, self.shelfLength - self.thickness))

        shelf.lineBy(Point(-self.backRestWidth / 4, 0))

        shelf.lineBy(Point(0, shelfBackLength + self.thickness))
        l = (self.backRestWidth / 2.0 - self.frameLength) / 2.0
        shelf.lineBy(Point(-l, 0))
        shelf.lineBy(Point(0, dxPlusd))
        shelf.lineBy(Point(-self.frameLength, 0))
        shelf.lineBy(Point(0, -dxPlusd))
        shelf.lineBy(Point(-l, 0))
        shelf.lineBy(Point(0, -shelfBackLength - self.thickness))

        shelf.lineBy(Point(-self.backRestWidth / 4, 0))
        shelf.lineBy(Point(0, -self.shelfLength + self.thickness))
        shelf.append(circleArc(self.thickness, Point(self.thickness, -self.thickness), '0'))

        self.insertPath(shelf, 'orange')

        testBoxStart = shelfStart.add(0, self.shelfLength + 3 * self.thickness + l)

        lochLength = self.shelfLength - self.usbDepth;

        testBox = self.insertRect(testBoxStart, self.backRestWidth, 2 * self.supportDistance + lochLength, 'red')

        boxStart = testBoxStart.add(remainder + self.frameLength / 2, 2 * self.thickness + lochLength)
        for i in range(nrFrames):
            self.insertRect(boxStart, self.frameLength, dxPlusd, 'blue')
            boxStart = boxStart.add(self.frameLength * 2, 0)

        boxStart = testBoxStart.add(remainder + self.frameLength / 2,
                                    3 * self.thickness + self.supportDistance + lochLength)
        for i in range(nrFrames):
            self.insertRect(boxStart, self.frameLength, self.thickness, 'blue')
            boxStart = boxStart.add(self.frameLength * 2, 0)

        # usbLochStart
        boxStart = testBoxStart.add(self.backRestWidth / 2 - self.usbWidth / 2,
                                    2 * self.thickness + lochLength - self.usbDepth / 2)
        usbLoch = Path()
        usbLoch.append(Move(boxStart))
        usbLoch.lineBy(Point(self.usbWidth, 0))
        usbLoch.lineBy(Point(0, -self.usbDepth))
        extra = (self.usbWidth - self.usbDepth) / 2
        usbLoch.lineBy(Point(-extra, 0))
        usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(0, -lochLength + self.usbDepth))
        usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(-self.usbDepth, 0))
        usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(0, lochLength - self.usbDepth))
        usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(-extra, 0))
        usbLoch.lineBy(Point(0, self.usbDepth))

        self.insertPath(usbLoch, 'orange')

    def drawBox(self):
        outerRadius = self.thickness * self.hingeCircleFactor
        dx = math.sqrt(outerRadius ** 2 - (self.thickness / 2) ** 2)
        shelfHeight = (self.boxWidth - 2 * self.thickness - (self.shelfcount - 1) * self.thickness) / self.shelfcount

        start = Point(10, 10)
        infoStart = start.add(-2, -2);
        infoText = self.boxType.description + " (generated on %s)  --- Width: %.2fmm, Depth: %.2fmm, Height: %.2fmm (Thickness: %.2fmm, frame length: %.2fmm)[shelfheight: %.2fmm]" % \
                   (self.printDate(), self.boxWidth, self.boxDepth, self.boxHeight, self.thickness, self.frameLength,
                    shelfHeight)
        # inkex.debug('boxFrame %s'%infoText)
        self.insertText(infoText, infoStart, 'orange')

        bottomAndFrontBack = Path();

        # Move to start and draw a line from there
        bottomAndFrontBack.append(move(start))

        # front left first
        bottomAndFrontBack.extend(self.boxFrames(self.boxHeight, Direction.up))
        # self.markPoints(bottomAndFrontBack.finalPosition(), 'blue')
        bottomAndFrontBack.append(line(Point(0, -self.thickness)))
        # self.markPoints(bottomAndFrontBack.finalPosition(), 'blue')

        # bottom left next
        bottomAndFrontBack.extend(self.boxFrames(self.boxDepth, Direction.up))
        # self.markPoints(bottomAndFrontBack.finalPosition(), 'blue')

        bottomAndFrontBack.append(line(Point(0, -self.thickness)))
        # back left next
        bottomAndFrontBack.extend(self.boxFrames(self.boxHeight, Direction.up))

        if self.boxType.has_hinges():
            # back width next
            self.markPoints(bottomAndFrontBack.finalPosition(), 'yellow')
            # Zurueck wg. Deckel (+ Rotation)
            backForHinge = self.thickness / 2.0 + outerRadius
            bottomAndFrontBack.append(line(Point(0, -backForHinge)))

        bottomAndFrontBack.append(line(Point(self.thickness, 0)))

        if self.boxType.has_hinges():
            bottomAndFrontBack.append(line(Point(0, backForHinge - self.thickness * (1.0 + math.sqrt(2)) / 2.0)))

        bottomAndFrontBack.append(line(Point(self.boxWidth - 2 * self.thickness, 0)))

        if self.boxType.has_hinges():
            bottomAndFrontBack.append(line(Point(0, -(backForHinge - self.thickness * (1.0 + math.sqrt(2)) / 2.0))))
        bottomAndFrontBack.append(line(Point(self.thickness, 0)))
        if self.boxType.has_hinges():
            bottomAndFrontBack.append(line(Point(0, backForHinge)))

        self.markPoints(bottomAndFrontBack.finalPosition(), 'yellow')

        # back right next
        bottomAndFrontBack.extend(self.boxFrames(self.boxHeight, Direction.down))
        bottomAndFrontBack.append(line(Point(0, self.thickness)))

        # bottom right next
        bottomAndFrontBack.extend(self.boxFrames(self.boxDepth, Direction.down))

        # front right next
        bottomAndFrontBack.append(line(Point(0, self.thickness)))
        bottomAndFrontBack.extend(self.boxFrames(self.boxHeight, Direction.down))

        # front top next
        # Aussparung fuer Deckel
        bottomAndFrontBack.append(line(Point(-self.thickness, 0)))
        if self.boxType.has_hinges():
            bottomAndFrontBack.append(line(Point(0, self.thickness)))
        bottomAndFrontBack.append(line(Point(-self.boxWidth + 2 * self.thickness, 0)))
        if self.boxType.has_hinges():
            bottomAndFrontBack.append(line(Point(0, -self.thickness)))
        bottomAndFrontBack.append(line(Point(-self.thickness, 0)))

        self.markPoints(bottomAndFrontBack.finalPosition(), 'green')
        bottomAndFrontBack = bottomAndFrontBack.simplify()
        self.markPoints(bottomAndFrontBack.finalPosition(), 'red')
        self.insertPath(bottomAndFrontBack)

        # separators
        separator1 = Path();
        separator1.MoveTo(start.add(self.boxWidth, self.boxHeight - self.thickness))
        separator1.extend(self.boxFrames(self.boxWidth, Direction.right))
        self.insertPath(separator1, 'green')

        separator2 = Path();
        separator2.MoveTo(start.add(0, self.boxHeight - self.thickness + self.boxDepth))
        separator2.extend(self.boxFrames(self.boxWidth, Direction.left))
        self.insertPath(separator2, 'green')

        # Shelf frames
        if (self.boxType == shelvedBox):
            # Shelf frames  front and back

            nrInOutFrames = int(
                math.floor((self.boxHeight - (self.frameEdgesMin * 2) - self.frameLength) / self.frameLength))
            nrFrames = int(math.floor(nrInOutFrames / 2))
            remainder = (self.boxHeight - nrFrames * self.frameLength * 2) / 2

            for side in range(2):  # 0 is front,  1 is back
                for i in range(self.shelfcount - 1):
                    shelfFramesStart = start.add((i + 1) * (shelfHeight + self.thickness),
                                                 (side * (self.boxDepth + self.boxHeight - 2 * self.thickness)))
                    # self.markPoints(shelfFramesStart, 'blue')
                    frameStart = shelfFramesStart.add(0, remainder + self.frameLength / 2)
                    for i in range(nrFrames):
                        self.insertRect(frameStart, self.thickness, self.frameLength, 'blue')
                        frameStart = frameStart.add(0, self.frameLength * 2)

            nrInOutFrames = int(
                math.floor((self.boxDepth - (self.frameEdgesMin * 2) - self.frameLength) / self.frameLength))
            nrFrames = int(math.floor(nrInOutFrames / 2))
            remainder = (self.boxDepth - nrFrames * self.frameLength * 2) / 2
            for i in range(self.shelfcount - 1):
                shelfFramesStart = start.add((i + 1) * (shelfHeight + self.thickness),
                                             (self.boxHeight - self.thickness))
                # self.markPoints(shelfFramesStart, 'blue')
                # inkex.debug('width %.2f remainder %.2f : fl %.2f'%(self.boxDepth, remainder, self.frameLength/2 ))
                frameStart = shelfFramesStart.add(0, remainder + self.frameLength / 2)
                for i in range(nrFrames):
                    self.insertRect(frameStart, self.thickness, self.frameLength, 'blue')
                    frameStart = frameStart.add(0, self.frameLength * 2)

        # Left and right part
        # left part

        leftPart = Path();

        leftBoxStart = start.add(self.boxWidth + 2, self.thickness)
        #    leftBoxStart = start.add(self.boxWidth + 2, self.boxHeight)

        leftHingecenter = leftBoxStart.add(self.boxHeight - self.thickness / 2,
                                           self.boxDepth - self.thickness - self.thickness / 2);
        if self.boxType.has_hinges():
            self.insertCircle(self.thickness * math.sqrt(2) / 2, leftHingecenter, 'green')

        leftPart.MoveTo(leftBoxStart)
        # self.markPoints(leftBoxStart, 'yellow')
        # leftPart.append(line(Point(0, self.thickness)))
        leftPart.extend(self.boxFrames(self.boxHeight, Direction.left))
        leftPart.append(line(Point(0, self.boxDepth - 2 * self.thickness)))
        if self.boxType.has_hinges():
            leftPart.append(line(Point(0, +0.5 * self.thickness - dx)))
            leftPart.append(
                circleArc(outerRadius, Point(-(dx + self.thickness / 2), dx + self.thickness / 2 - self.thickness)))
            leftPart.append(line(Point(dx + self.thickness / 2, 0)))
        # self.markPoints(leftPart.finalPosition(), 'orange')
        leftPart.extend(self.boxFrames(self.boxHeight, Direction.right))
        leftPart.append(line(Point(self.thickness, 0)))
        leftPart.append(line(Point(0, self.thickness)))
        leftPart.extend(self.boxFrames(self.boxDepth, Direction.down))

        self.insertPath(leftPart.simplify())

        # left part

        rightPart = Path();

        rightBoxStart = start.add(self.boxWidth + 2, self.boxDepth + self.thickness + 2 * outerRadius)

        if self.boxType.has_hinges():
            rightHingecenter = rightBoxStart.add(self.boxHeight - self.thickness / 2, - self.thickness / 2);
            self.insertCircle(self.thickness * math.sqrt(2) / 2, rightHingecenter, 'green')

        rightPart.MoveTo(rightBoxStart)

        rightPart.extend(self.boxFrames(self.boxHeight, Direction.left))
        if self.boxType.has_hinges():
            rightPart.append(line(Point(-dx - self.thickness / 2, 0)))
            rightPart.append(
                circleArc(outerRadius, Point((dx + self.thickness / 2), dx + self.thickness / 2 - self.thickness)))
            rightPart.append(line(Point(0, 0.5 * self.thickness - dx)))

        rightPart.append(line(Point(0, self.boxDepth - 2 * self.thickness)))
        # self.markPoints(rightPart.finalPosition(), 'orange')
        rightPart.extend(self.boxFrames(self.boxHeight, Direction.right))
        rightPart.append(line(Point(self.thickness, 0)))
        rightPart.append(line(Point(0, self.thickness)))
        rightPart.extend(self.boxFrames(self.boxDepth, Direction.down))

        self.insertPath(rightPart.simplify())

        if (self.boxType == shelvedBox):
            self.draw_linehelves(start)
        # TOP Part (only for hinged boxes)
        if self.boxType.has_hinges():

            topStart = start.add(self.boxWidth + self.boxHeight + 1 * self.hingeCircleFactor * self.thickness, 0)
            topPart = Path()

            topPart.MoveTo(topStart)
            topPart.append(line(Point(self.boxWidth, 0)))
            topPart.append(line(Point(0, self.thickness)))
            topPart.append(line(Point(-self.thickness, 0)))
            topPart.append(line(Point(0, self.boxDepth - self.thickness)))
            topPart.append(line(Point(-(self.boxWidth - 2 * self.thickness), 0)))
            topPart.append(line(Point(0, -self.boxDepth + self.thickness)))
            topPart.append(line(Point(-self.thickness, 0)))
            topPart.append(line(Point(0, -self.thickness)))

            self.insertPath(topPart.simplify())

            # make boxes for the mobile stand
            if self.boxType == mobileLoader:
                numberOfSupports = int(math.floor(self.boxWidth - self.thickness) / self.distanceBetweenSupports)
                remainder = (self.boxWidth - self.thickness) - self.distanceBetweenSupports * numberOfSupports

                dx = math.tan(math.pi / 2 - self.inclinationRad) * self.thickness
                # frameWidth = self.thickness/math.sin(self.inclinationRad)
                dxPlusd = dx / math.sin(self.inclinationRad) + self.thickness
                nrInOutFrames = int(
                    math.floor((self.backRestWidth - (self.frameEdgesMin * 2) - self.frameLength) / self.frameLength))
                nrFrames = int(math.floor(nrInOutFrames / 2))
                remainderFrames = (self.backRestWidth - ((nrFrames * 2) * self.frameLength)) / 2.0

                lochLength = self.shelfLength - self.usbDepth;
                smallerradius = self.usbDepth * 0.3
                for supp in range(0, numberOfSupports):
                    boxStart = topStart.add(self.thickness + remainder / 2.0 + self.distanceBetweenSupports * supp,
                                            (self.boxDepth - self.backRestWidth) / 2.0)

                    testBox = self.insertRect(boxStart, self.distanceBetweenSupports, self.backRestWidth, 'red')

                    # =============================================================================
                    standBoxStart = boxStart.add(self.thickness + lochLength, remainderFrames + 0.5 * self.frameLength)
                    for i in range(nrFrames):
                        self.insertRect(standBoxStart, dxPlusd, self.frameLength, 'blue')
                        standBoxStart = standBoxStart.add(0, self.frameLength * 2)
                    #
                    supportBoxStart = boxStart.add(self.thickness + lochLength + dxPlusd + self.supportDistance,
                                                   remainderFrames + 0.5 * self.frameLength)
                    for i in range(nrFrames):
                        self.insertRect(supportBoxStart, self.thickness, self.frameLength, 'blue')
                        supportBoxStart = supportBoxStart.add(0, self.frameLength * 2)

                        # usbLochStart
                    lochBoxStart = boxStart.add(0.5 * self.thickness + lochLength,
                                                self.backRestWidth / 2 - self.usbWidth / 2)
                    self.markPoints(lochBoxStart, 'blue')
                    usbLoch = Path()
                    usbLoch.append(Move(lochBoxStart))
                    usbLoch.lineBy(Point(0, self.usbWidth))
                    usbLoch.lineBy(Point(-self.usbDepth, 0))
                    extra = (self.usbWidth - self.usbDepth) / 2
                    usbLoch.lineBy(Point(0, -extra))
                    usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(-lochLength + self.usbDepth, 0))
                    usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(0, -self.usbDepth))
                    usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(lochLength - self.usbDepth, 0))
                    usbLoch = usbLoch.lineByWithCorner(smallerradius, Point(0, -extra))
                    usbLoch.lineBy(Point(self.usbDepth, 0))

                    self.insertPath(usbLoch, 'orange')

    #
    # =============================================================================
    def draw_linehelves(self, start):
        for ii in range(self.shelfcount - 1):
            shelfStart = start.add(self.boxWidth + self.boxHeight + self.thickness,
                                   self.thickness + ii * (self.boxDepth + self.thickness))
            self.draw_linehelf(shelfStart)

    def draw_linehelf(self, shelfStart):

        leftPart = Path();

        leftPart.MoveTo(shelfStart)

        leftPart.extend(self.boxFrames(self.boxHeight, Direction.left))
        leftPart.append(line(Point(0, self.boxDepth - 2 * self.thickness)))

        leftPart.extend(self.boxFrames(self.boxHeight, Direction.right))
        leftPart.append(line(Point(self.thickness, 0)))
        leftPart.append(line(Point(0, self.thickness)))
        leftPart.extend(self.boxFrames(self.boxDepth, Direction.down))

        self.insertPath(leftPart.simplify())

    def insertRect(self, start_pos, dx, dy, color='black'):
        box = Path()
        box.MoveTo(start_pos)
        box.lineBy(Point(dx, 0))
        box.lineBy(Point(0, dy))
        box.lineBy(Point(-dx, 0))
        box.lineBy(Point(0, -dy))
        self.insertPath(box, color)

    def insertText(self, text, position, color='black'):
        style = {'stroke': color, 'stroke-width': self.svg.unittouu("0.1 mm"), 'font-size': '3px'}
        drw = {'style': str(inkex.Style(style)), 'x': '%f' % position.x, 'y': '%f' % position.y}
        text_node = etree.SubElement(self.parent, inkex.addNS('text', 'svg'), drw)
        text_node.text = text

    def insertPath(self, path, color='black'):
        style = {'stroke': color, 'fill': 'none', 'stroke-width': self.svg.unittouu("0.1 mm")}
        actions = path.translateToSVGd()
        #    inkex.debug(' actions %s'%actions)
        drw = {'style': str(inkex.Style(style)), 'd': actions}
        edge = etree.SubElement(self.parent, inkex.addNS('path', 'svg'), drw)

    def insertCircle(self, r, center, color='black'):
        style = {'stroke': color, 'fill': 'none', 'stroke-width': self.svg.unittouu("0.1 mm")}
        drw = {'style': str(inkex.Style(style)), 'cx': '%f' % center.x, 'cy': '%f' % center.y, 'r': '%f' % r}
        edge = etree.SubElement(self.parent, inkex.addNS('circle', 'svg'), drw)

    def toSVGString(self):
        return "a %f %f 0 1 1 %f %f" % (self.r, self.r, self.endPoint.x, self.endPoint.y)

    def newPos(self, start_pos):
        return start_pos.add(self.endPoint.x, self.endPoint.y)

    def printDate(self, date=datetime.now()):
        return date.strftime('%d.%m.%y %H:%M')

    markerCount = 0

    def markPoints(self, center, color='red'):
        """
    Just a helper method to mark certain points
    """

        if self.debug:
            self.markerCount += 1
            style = {'stroke': color, 'fill': 'none', 'stroke-width': self.svg.unittouu("2 mm")}
            drw = {'style': str(inkex.Style(style)), 'cx': '%f' % center.x, 'cy': '%f' % center.y, 'r': '4'}
            etree.SubElement(self.parent, inkex.addNS('circle', 'svg'), drw)

            style = {'stroke': 'black', 'stroke-width': self.svg.unittouu("0.1 mm"), 'font-size': '3px'}
            drw = {'style': str(inkex.Style(style)), 'x': '%f' % (center.x + 5.0), 'y': '%f' % (center.y + 5),
                   'r': '4'}
            #      inkex.debug("Text: %s" % drw)
            text_node = etree.SubElement(self.parent, inkex.addNS('text', 'svg'), drw)
            text_node.text = '%s: (%.2f,%.2f)' % (self.markerCount, center.x, center.y)

    def boxFrames(self, length, direction, inverse=False, depth=None):
        """
    returns a subPath with tabs starting at pointLoc
    pointLoc: the start point    
    length: the length in current unit
    direction: an enum with the direction
    inverse: if true, indentation is on the other side
    """
        if depth is None:
            depth = self.thickness
        nrInOutFrames = int(math.floor((length - (self.frameEdgesMin * 2) - self.frameLength) / self.frameLength))
        nrFrames = int(math.floor(nrInOutFrames / 2))
        remainder = (length - ((nrFrames * 2) * self.frameLength)) / 2.0

        frameMoveHalf = Point(direction['frameMove'][0] * self.frameLength / 2.0,
                              direction['frameMove'][1] * self.frameLength / 2.0)
        walkIn = Point(direction['walkIn'][0] * depth, direction['walkIn'][1] * depth)
        walkOut = Point(direction['walkOut'][0] * depth, direction['walkOut'][1] * depth)
        startEnd = Point(direction['frameMove'][0] * remainder, direction['frameMove'][1] * remainder)

        path = Path()

        if (inverse):
            path.append(line(walkIn))
        path.append(line(startEnd))

        for i in range(nrFrames):
            path.append(line(frameMoveHalf))
            if inverse:
                path.append(line(walkOut))
            else:
                path.append(line(walkIn))
            path.append(line(frameMoveHalf))
            path.append(line(frameMoveHalf))
            if (inverse):
                path.append(line(walkIn))
            else:
                path.append(line(walkOut))
            path.append(line(frameMoveHalf))
        path.append(line(startEnd))
        if (inverse): path.append(line(walkOut))
        return path
