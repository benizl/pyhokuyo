#!/usr/bin/env python

import pylab
import hokuyo

h = hokuyo.HokuyoURG('/dev/ttyACM0')

while True:
	try:
		d = h.scan_once()

		pylab.plot(d)
		pylab.show()

	except KeyboardInterrupt:
		break

