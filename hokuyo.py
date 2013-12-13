#!/usr/bin/env python

import serial

class HokuyoException(Exception):
	pass

class HokuyoURG:
	def __init__(self, port, initial_baud=19200, run_baud=115200, steps=768):

		self.steps=steps

		self.port = serial.Serial(port, initial_baud, timeout=1)
		self.port.write('SCIP2.0\n')
		# expect 'SCIP2.0\n0\n\n'
		self.port.write('RS\n')

		if (initial_baud != run_baud):
			msg = "SS{baud:06d}\n".format(baud=run_baud)
			self.port.flushInput()
			self.port.write(msg)

			for tries in range(10):
				c = self.port.readline()
				if c == msg:
					break
			else:
				print("Can't change baud rate")
				return

			s = self.port.readline()
			self.port.readline() # Empty

			if s != '00P\n':
				print("WARNING: Can't change baud: {} {}".format(c,s))
				return

		self.port.close()
		self.port = serial.Serial(port, run_baud, timeout=1)
		self.port.flushInput()

		#print(self.port)

	def close(self):
		self.port.close()

	@staticmethod
	def _encode_n(d, n):
		s = ''
		for i in range(n):
			s = chr((d & 0x3F)+0x30) + s
			d = d >> 6

		return s

	@staticmethod
	def _decode_n(s, n):
		d = 0
		for i in range(n):
			d = d << 6
			d = d + ord(s[i]) - 0x30

		return d

	def index_to_degrees(self, i):
		mid = self.steps / 2.0

		return (i - mid) * (240.0 / self.steps)

	def index_to_radians(self, i):
		import math
		return self.index_to_degrees(i) * math.pi / 180

	def _read_scan(self):
		dat = ''
		while True:
			try:
				l = self.port.readline()
			except (serial.SerialException, serial.SerialTimeoutException):
				raise HokyuoException("Serial error")


			if len(l) == 0:
				raise HokuyoException("Serial not ready")

			if len(l) == 1: # End of scan is a line with no data, only \n
				break

			l = l[:-2] # Trim off sum and \n TODO: check sum
			dat = dat + l

		scan = []

		if len(dat) % 3 != 0:
			#print("WARNING: unexpected data length")
			dat = dat[:-(len(dat)%3)]

		for i in range(0, len(dat), 3):
			scan.append(HokuyoURG._decode_n(dat[i:i+3],3))

		return scan


	def scan_once(self, start=0, end=None, cluster=0):
		if end is None:
			end=self.steps

		msg = "MD{start:04d}{end:04d}{cluster:02d}001\n".format(
			start=start, end=end, cluster=cluster)

		self.port.flushInput()
		self.port.write(msg)

		# Wait for echo (throw away anything at the head of the rx buffer)
		for i in range(10):
			l = self.port.readline()
			if l == msg:
				break
		else:
			print("WARNING: Hokuyo didn't respond to single scan start command")

		self.port.readline() # status
		self.port.readline() # Empty
		self.port.readline() # Confirmation, TODO
		self.port.readline() # 99b
		self.port.readline() # timestamp
		
		return self._read_scan()

	def start_scan(self, start=0, end=None, cluster=0, interval=0):
		if end is None:
			end=self.steps

		msg = "MD{start:04d}{end:04d}{cluster:02d}{interval:02d}0\n".format(
			start=start, end=end, cluster=cluster, interval=interval)

		self.port.flushInput()
		self.port.write(msg)

		# Wait for echo (throw away anything at the head of the rx buffer)
		for i in range(10):
			l = self.port.readline()
			if l == msg:
				break
		else:
			print("WARNING: Hokuyo not responding to scan start")

		self.port.readline() # status
		self.port.readline() # Empty

		if cluster == 0:
			cluster = 1

		self._expect_length = (end - start + 1) / cluster

	def read_scan(self):

		self.port.readline() # Confirmation, TODO
		self.port.readline() # 99b
		self.port.readline() # timestamp

		scan = self._read_scan()

		#print(len(scan), self._expect_length)
		return scan if len(scan) == self._expect_length else None

	def end_scan(self):
		self.port.write("QT\n")
		

if __name__ == '__main__':
	import sys
	h = HokuyoURG(sys.argv[1])
	print("Scan once: {}".format(len(h.scan_once())))

	h.start_scan()
	while True:
		print("Scan: {}".format(len(h.read_scan())))

	h.end_scan()
