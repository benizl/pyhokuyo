#!/usr/bin/env python

import pylab
import hokuyo

from math import sin, cos

h = hokuyo.HokuyoURG('/dev/ttyACM0')

fig=pylab.figure()
pylab.ion()
pylab.show()
pylab.hold(False)

while True:
	try:
		d = h.scan_once()
		b = [h.index_to_radians(i) for i in range(len(d))]

		x = [ r * sin(bear) for r, bear in zip(d,b)]
		y = [ r * cos(bear) for r, bear in zip(d,b)]

		pylab.scatter(x,y)
		pylab.axis([-5000,5000,-1000,5000])
		pylab.draw()

	except KeyboardInterrupt:
		break

