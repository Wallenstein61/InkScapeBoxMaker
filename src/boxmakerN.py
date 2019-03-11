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
"""


__version__ = "0.1" 

from boxmakerNLib import BoxMaker
# Create effect instance and apply it.
effect = BoxMaker()
effect.affect()

