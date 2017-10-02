#!/usr/bin/env python

# ------------------------------------------------------------------
# stitchcode - a simple Embroidery class for python
# ------------------------------------------------------------------
# Copyright (C) 2013-2015 Michael Aschauer
# ------------------------------------------------------------------
# originaly derived and forked from PyEmb.py
# see: http://www.achatina.de/sewing/main/TECHNICL.HTM
# ------------------------------------------------------------------
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import math
import sys
from struct import unpack,pack
from PIL import Image, ImageDraw
dbg = sys.stderr

pixels_per_millimeter = 5

def abs(x):	
	if (x<0): return -x
	return x


############################################
#### POINT CLASS
############################################

class Point:
	def __init__(self, x, y, jump=False, color=0):
		self.x = x
		self.y = y
		self.color = 0
		self.jump = jump
		
	def __add__(self, other):
		return Point(self.x+other.x, self.y+other.y)

	def __sub__(self, other):
		return Point(self.x-other.x, self.y-other.y)

	def mul(self, scalar):
		return Point(self.x*scalar, self.y*scalar)
	
	def __repr__(self):
		return "Pt(%s,%s,%s)" % (self.x, self.y, self.jump)

	def length(self):
		return math.sqrt(math.pow(self.x, 2.0) + math.pow(self.y, 2.0))

	def as_int(self):
		return Point(int(round(self.x)), int(round(self.y)))

	def as_tuple(self):
		return (self.x, self.y)

	def __cmp__(self, other):
		return cmp(self.as_tuple(), other.as_tuple())


############################################
#### MAIN EMBROIDERY CLASS
############################################

class Embroidery:
	def __init__(self):
		self.coords = []
		self.clamp = 127
		self.minx = 0
		self.maxx = 0
		self.miny = 0
		self.maxy = 0
		
	def setMaxStitchLength(self, clamp=127):
		self.clamp = clamp

	def addStitch(self, coord):
		self.coords.append(coord)
		
	def getSize(self):
		(self.maxx, self.maxy) = (self.coords[0].x, self.coords[0].y)
		(self.minx, self.miny) = (self.coords[0].x, self.coords[0].y)
		for p in self.coords:
			self.minx = min(self.minx, p.x)
			self.miny = min(self.miny, p.y)
			self.maxx = max(self.maxx, p.x)
			self.maxy = max(self.maxy, p.y)

		sx = int( self.maxx - self.minx )
		sy = int( self.maxy - self.miny )
		return (sx,sy)
		
	def getMetricWidth(self):
		sx,sy = self.getSize()
		return sx / 10.0
		
	def getMetricHeight(self):
		sx,sy = self.getSize()
		return sy / 10.0
		
	def translate_to_origin(self):
		"""translates embroidery to origin

		Args: none
		"""
		(self.minx, self.maxx) = (self.coords[0].x, self.coords[0].x)
		(self.miny, self.maxy) = (self.coords[0].y, self.coords[0].y)
		if (len(self.coords)==0):
			return
		for p in self.coords:
			self.minx = min(self.minx, p.x)
			self.miny = min(self.miny, p.y)
			self.maxx = max(self.maxx, p.x)
			self.maxy = max(self.maxy, p.y)
		sx = self.maxx - self.minx
		sy = self.maxy - self.miny
		for p in self.coords:
			p.x -= self.minx
			p.y -= self.miny
		dbg.write("translated to origin. resulting field size: %0.2fmm x %0.2fmm\n" % (sx/10, sy/10))

	def scale(self, factor):
		"""scales embroidery design

		Args:
			factor: multiplication factor (1 means no scaling)
		"""		
		dbg.write("scale to %d%%\n" % (factor * 100))
		for p in self.coords:
			p.x *= factor
			p.y *= factor

	def add_endstitches(self, length=10, max_stitch_length=127):
		"""adds endstitches before and after stitches that are too long

		Args:
			length: length of end stitches (default = 10)
			max_stitch_length: max. length for stitches (default = 127)
		"""				
		dbg.write("add endstitches BEGIN - stitch count: %d\n" % len(self.coords))
		self.pos = self.coords[0]
		new_coords = []
		new_coords.append(self.coords[0])
		for stitch in self.coords[1:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int		
			dmax = max(abs(delta.x), abs(delta.y))

			if dmax <= max_stitch_length:
				new_coords.append(stitch)				
			else:
				x2 = length * delta.x / delta.length()
				y2 = length * delta.y / delta.length()
				new_coords.append(Point(old_int.x+x2, old_int.y+y2))
				new_coords.append(self.pos)
				new_coords.append(stitch)			
				new_coords.append(Point(new_int.x-x2, new_int.y-y2))
				new_coords.append(stitch)						
			self.pos = stitch
		self.coords = new_coords
		dbg.write("add endstitches END - stitch count: %d\n" % len(self.coords))
	
	
	def add_endstitches_to_jumps(self, length=10):		
		"""adds endstitches before and after jumps.	

		Args:
			length: length of end stitches (default = 10)
		"""				
		dbg.write("add endstitches BEGIN - stitch count: %d\n" % len(self.coords))
		self.pos = self.coords[0]
		new_coords = []
		new_coords.append(self.pos)

		for j in range(1, len(self.coords)):
			stitch = self.coords[j]		
			if stitch.jump == True:
				if j > 2:
					l1_int = self.coords[j-1].as_int()
					l2_int = self.coords[j-2].as_int()
					delta = l1_int - l2_int
					if delta.length() != 0:				
						dx = length * delta.x / delta.length()
						dy = length * delta.y / delta.length()					
						new_coords.append(Point(l1_int.x - dx, l1_int.y - dy))
						new_coords.append(self.coords[j-1])			
				new_coords.append(stitch)				
				#and after jump	
				if j+1 < len(self.coords):
					l3_int = self.coords[j].as_int()
					l4_int = self.coords[j+1].as_int()
					delta = l4_int - l3_int
					if delta.length() != 0:				
						dx = length * delta.x / delta.length()
						dy = length * delta.y / delta.length()
						new_coords.append(Point(l3_int.x + dx, l3_int.y + dy))
						new_coords.append(Point(l3_int.x, l3_int.y))
			else:
				new_coords.append(stitch)
								
			self.pos = stitch
		self.coords = new_coords
		dbg.write("add endstitches END - stitch count: %d\n" % len(self.coords))		

	def to_triple_stitches(self, length=2):
		"""convert desgin to triple stitches

		Args:
			length: length/offset of triple (default = 2)
		"""			
		dbg.write("to_triple_stitches BEGIN - stitch count: %d\n" % len(self.coords))
		self.pos = self.coords[0]
		new_coords = []
		new_coords.append(self.coords[0])
		for stitch in self.coords[1:]:		
			if not stitch.jump:
				new_stitch = stitch.as_int()
				last_stitch = self.pos.as_int()
				delta = new_stitch - last_stitch	
				if delta.length != 0:						
					nx = length * -delta.y / delta.length()
					ny = length * delta.x / delta.length()			
					new_coords.append(Point(new_stitch.x - nx, new_stitch.y - ny))
					new_coords.append(Point(last_stitch.x - nx, last_stitch.y - ny))
					new_coords.append(stitch)
			new_coords.append(stitch)				
			self.pos = stitch
		self.coords = new_coords
		dbg.write("to_triple_stitches END - stitch count: %d\n" % len(self.coords))

	def to_red_work(self, length=3):
		"""convert desgin to red work stitches

		Args:
			length: length/offset of triple (default = 3)
		"""					
		dbg.write("to_triple_stitches BEGIN - stitch count: %d\n" % len(self.coords))
		self.pos = self.coords[0]
		new_coords = []
		new_coords.append(self.coords[0])
		for stitch in self.coords[1:]:		
			if not stitch.jump:
				new_stitch = stitch.as_int()
				last_stitch = self.pos.as_int()
				delta = new_stitch - last_stitch
				if delta.length != 0:				
					nx = length * -delta.y / delta.length()
					ny = length * delta.x / delta.length()			
					new_coords.append(Point(new_stitch.x - nx, new_stitch.y - ny))
					new_coords.append(Point(last_stitch.x - nx, last_stitch.y - ny))
					new_coords.append(Point(new_stitch.x + nx, new_stitch.y + ny))
					new_coords.append(Point(last_stitch.x + nx, last_stitch.y + ny))
					new_coords.append(stitch)
			new_coords.append(stitch)				
			self.pos = stitch
		self.coords = new_coords
		dbg.write("to_triple_stitches END - stitch count: %d\n" % len(self.coords))
		
	def flatten(self, max_length=127):
		"""flatten file - interpolate stitches that are too long

		Args:
			max_length: maximum stitch length (default = 127)
		"""					
		dbg.write("flatten BEGIN - stitch count: %d\n" % len(self.coords))
		self.pos = self.coords[0]
		new_coords = []
		new_coords.append(self.coords[0])
		for stitch in self.coords[1:]:		
			new_stitch = stitch.as_int()
			last_stitch = self.pos.as_int()
			delta = new_stitch - last_stitch
			if delta.length:	
				#do several interpolated steps if too long			
				dmax = max(abs(delta.x), abs(delta.y))
				dsteps = abs(dmax / max_length) + 1
				if dmax > max_length and not stitch.jump:
					for i in range(0, dsteps):					
						x =  last_stitch.x + (i+1) * delta.x/dsteps					
						y = last_stitch.y +  (i+1) * delta.y/dsteps
						new_coords.append(Point(x, y))			
				else:
					new_coords.append(stitch)
				self.pos = stitch
		self.coords = new_coords
		dbg.write("flatten END - stitch count: %d\n" % len(self.coords))

	############################################
	#### FILE IMPORT AND EXPORT
	############################################

	def save(self, filename):
		"""save design as file - a wrapper that figures out which format
			funtion to use by filename extension
		Args:
			filename
		"""					
		ext = (filename[-3:]).lower()
		if ext == "exp":
			self.save_as_exp(filename)
		elif ext == "png":
			self.save_as_png(filename)
		elif ext == "pes":
			self.save_as_pes(filename)
		elif ext == "svg":
			self.save_as_svg(filename)
		elif ext == "ksm":
			self.save_as_ksm(filename)
		elif ext == "dst":
			self.save_as_dst(filename)
		else:
			dbg.write("error saving file: unknown file extension: %s\n" % (filename))
			
			
	def load(self, filename):
		"""import design from file - a wrapper that figures out which format
			funtion to use by filename extension
		Args:
			filename
		"""					
		ext = (filename[-3:]).lower()
		if ext == "exp":
			self.import_melco(filename)
		if ext == "dst":
			self.import_tajima(filename)
		elif ext == "pes":
			self.import_pes(filename)
		elif ext == "svg":
			self.import_svg(filename)
		else:
			dbg.write("error loading file: unknown input file extension: %s\n" % (filename))
			

	############################################
	#### PFAFF / KSM
	############################################

	def save_as_ksm(self, filename):
		"""save design as  KSM/Pfaff format formated file

		Args:
			filename
		"""			
		f = open(filename, "wb")
		f.write(self.export_ksm())		
		f.close()
		dbg.write("saved to file: %s\n" % (filename))


	def export_ksm(self):
		"""converts design to KSM/Pfaff format -  CURRENTLY UNTESTED
		
		Returns:
			string (KSM/Pfaff)
		"""			
		
		self.string = ""
		self.mode_byte = 0x80
		
		#write empty header
		for i in range(0, 512):
			self.string += chr(0x00)		
		
		def move(x,y):
			self.string+=chr(abs(y))
			self.string+=chr(abs(x))
			if (y<0):
				self.mode_byte |= 0x20
			if (x<0):
				self.mode_byte |= 0x40
			self.string+=chr(self.mode_byte)
	
								
		
		self.pos = Point(0,0)
		lastColor = None
		for stitch in self.coords:
			if (lastColor!=None and stitch.color!=lastColor):
				self.mode_byte = 0x99
				#dbg.write("Color change!\n")
			else:
				self.mode_byte = 0x80
				#dbg.write("color still %s\n" % stitch.color)
			lastColor = stitch.color
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int
			
			sum_x = 0
			sum_y = 0
			dmax = max(abs(delta.x), abs(delta.y))
			dsteps = abs(dmax / 127) + 1
			if dsteps == 1:
				move(delta.x, delta.y)
			else:
				for i in range(0,dsteps):
					if i < dsteps -1:
						move(delta.x/dsteps, delta.y/dsteps)
						sum_x += delta.x/dsteps
						sum_y += delta.y/dsteps
					else:
						move(delta.x - sum_x, delta.y - sum_y)			
						

			self.pos = stitch
		return self.string

						
	############################################
	#### MELCO / EXP
	############################################
	

	def save_as_exp(self, filename):
		"""save design as EXP/Melco formated file

		Args:
			filename
		"""			
		f = open(filename, "wb")
		f.write(self.export_melco())		
		f.close()
		dbg.write("saved to file: %s\n" % (filename))		
				
		
	def export_melco(self):
		"""converts design to EXP/Melco format

		Returns:
			string (EXP/Melco)
		"""				
		self.string = ""
		self.pos = self.coords[0]
		dbg.write("export - stitch count: %d\n" % len(self.coords))
		
		for stitch in self.coords[0:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int	
							
			def move(x, y):
				if (x<0): x = x + 256
				self.string += chr(x)
				if (y<0): y = y + 256
				self.string += chr(y)
				
			#do several interpolated steps if too long	
			#dbg.write("delta: %d, %d\n" % (delta.x,delta.y))
			sum_x = 0
			sum_y = 0
			dmax = max(abs(delta.x), abs(delta.y))
			dsteps = abs(dmax / 127) + 1
			if dsteps == 1:
				if stitch.jump:
					self.string += chr(0x80)
					self.string += chr(0x04)
				#dbg.write("move: %d, %d\n" % (delta.x, delta.y))				
				move(delta.x, delta.y)
			else:
				for i in range(0,dsteps):
					if stitch.jump:
						self.string += chr(0x80)
						self.string += chr(0x04)
					if i < dsteps -1:
						#dbg.write("move: %d, %d\n" % (delta.x/dsteps, delta.y/dsteps))
						move(delta.x/dsteps, delta.y/dsteps)
						sum_x += delta.x/dsteps
						sum_y += delta.y/dsteps
					else:
						#dbg.write("move: %d, %d\n" % (delta.x - sum_x, delta.y - sum_y))
						move(delta.x - sum_x, delta.y - sum_y)
						
			self.pos = stitch
			#dbg.write("sum: %d, %d\n" % (sum_x,sum_y))
			
		return self.string
	
			
	def import_melco(self, filename):
		"""read an EXP/Melco file

		Args:
			filename
		"""				
		# read in an EXP/Melco file
		(lastx, lasty) = (0, 0)
		(self.maxx, self.maxy) = (0, 0)
		(self.minx, self.miny) = (0, 0)
		
		# add Stitch at origin or not?
		self.addStitch(Point(lastx, lasty, False))
		
		jump = False
		f = open(filename, "rb")
		byte = " "
		while byte:			
			byte = f.read(1)
			if byte != "" and len(byte) > 0:
				if byte == chr(0x80):
					byte = f.read(1)
					if byte == chr(0x04) or byte == chr(0x02)  or byte == chr(0x00):					
						jump = True
					elif byte == chr(0x01) or byte == chr(0x02):
						dbg.write("reading EXP: ignore color change")
					byte = f.read(1)
				dx = ord(byte)
				if dx > 127:
					dx = dx - 256
				byte = f.read(1)
				if byte != "":
					dy = ord(byte)					
					if dy > 127:
						dy = dy - 256
					lastx = lastx + dx
					lasty = lasty + dy	
					if dx != 0 or dy != 0:
						self.addStitch(Point(lastx, lasty, jump))
					jump = False				
		f.close()
		dbg.write("reading EXP: loaded from file: %s\n" % (filename))
		dbg.write("reading EXP: number of stitches: %d\n" % len(self.coords))
		self.translate_to_origin()



						
	############################################
	#### TAJIMA / DST
	############################################
	

	def save_as_dst(self, filename):
		"""save design as DST/Tajima formated file

		Args:
			filename
		"""			
		f = open(filename, "wb")
		f.write(self.export_tajima())		
		f.close()
		dbg.write("saved to file: %s\n" % (filename))		

	def DecodeTajimaStitch(self, b1, b2, b3):       
		
		x = 0
		y = 0
		        
		if b1 & 0x01:
				x += 1
				
		if b1 & 0x02:
				x -= 1
				
		if b1 & 0x04:
				x += 9
				
		if b1 & 0x08:
				x -= 9
				
		if b1 & 0x80:
				y += 1
				
		if b1 & 0x40:
				y -= 1
				
		if b1 & 0x20:
				y += 9
				
		if b1 & 0x10:
				y -= 9
				
		if b2 & 0x01:
				x += 3
				
		if b2 & 0x02:
				x -= 3
				
		if b2 & 0x04:
				x += 27
				
		if b2 & 0x08:
				x -= 27
				
		if b2 & 0x80:
				y += 3

		if b2 & 0x40:
				y -= 3
				
		if b2 & 0x20:
				y += 27
				
		if b2 & 0x10:
				y -= 27
				
		if b3 & 0x04:
				x += 81
				
		if b3 & 0x08:
				x -= 81
				
		if b3 & 0x20:
				y += 81
				
		if b3 & 0x10:
				y -= 81

		# Color change
		#if b3 & 0x80 and b3 & 0x40:
		#		self.ColorsRead += 1
		#		if self.ColorsRead > len(self.Colors):
		#				self.Colors.append( self.RandomColor() )
		#		
		#		self.ColorChanges.append( self.CurrentStitch ) 
		#		return [self.ColorsRead - 1, 0, self.COLOR]


		# Jump stitch
		if b3 & 0x80:
			return (x, y, True)
		else:
			return (x, y, False)

				
	def EncodeTajimaStitch(self, dx, dy, jump=False):
		b1 = 0
		b2 = 0
		b3 = 0

		if dx > 40:
				b3 |= 0x04
				dx -= 81

		if dx < -40:
				b3 |= 0x08
				dx += 81
				
		if dy > 40:
				b3 |= 0x20
				dy -= 81

		if dy < -40:
				b3 |= 0x10
				dy += 81

		if dx > 13:
				b2 |= 0x04
				dx -= 27

		if dx < -13:
				b2 |= 0x08
				dx += 27
				
		if dy > 13:
				b2 |= 0x20
				dy -= 27

		if dy < -13:
				b2 |= 0x10
				dy += 27

		if dx > 4:
				b1 |= 0x04
				dx -= 9

		if dx < -4:
				b1 |= 0x08
				dx += 9
				
		if dy > 4:
				b1 |= 0x20
				dy -= 9

		if dy < -4:
				b1 |= 0x10
				dy += 9
				
		if dx > 1:
				b2 |= 0x01
				dx -= 3

		if dx < -1:
				b2 |= 0x02
				dx += 3
				
		if dy > 1:
				b2 |= 0x80
				dy -= 3

		if dy < -1:
				b2 |= 0x40
				dy += 3

		if dx > 0:
				b1 |= 0x01
				dx -= 1

		if dx < 0:
				b1 |= 0x02
				dx += 1
				
		if dy > 0:
				b1 |= 0x80 
				dy -= 1

		if dy < 0:
				b1 |= 0x40
				dy += 1

		s = chr(b1)
		s += chr(b2)
		if jump:
			s += chr(b3 | 0x83)
		else:
			s += chr(b3 | 0x03)
		
		return s

		
	def export_tajima(self):
		"""converts design to DST/Tajima  format

		Returns:
			string (DST/Tajima )
		"""				
		self.string = ""
		self.pos = self.coords[0]
		dbg.write("export - stitch count: %d\n" % len(self.coords))


		def writeHeader(str, length, padWithSpace=False):
			for i in range (0,length-2):
				if i < len(str):
					self.string += str[i];
				else:
					if padWithSpace:
						self.string += chr(0x20)
					else:
						self.string += chr(0x00);				
			self.string += chr(0x0A);
			self.string += chr(0x1A);		

		writeHeader("LA:turtlestitch", 20, True)
		writeHeader("ST:%s" % (len(self.coords)), 11)
		writeHeader("CO:1", 7)
		writeHeader("+X:%s" % (self.getMetricWidth()), 9)
		writeHeader("-X:0", 9)
		writeHeader("+Y:%s" % (self.getMetricHeight()), 9)
		writeHeader("-Y:0", 9)
		writeHeader("AX:0", 10)
		writeHeader("AY:0", 10)
		writeHeader("MX:0", 10)
		writeHeader("MY:0", 10)
		writeHeader("PD:0", 10)

		self.string += chr(0x1a);
		self.string += chr(0x00);
		self.string += chr(0x00);
		self.string += chr(0x00);
			
		#write empty header
		for i in range(0, 384):
			self.string += chr(0x00)
		
		for stitch in self.coords[0:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int	
							
			#do several interpolated steps if too long	
			sum_x = 0
			sum_y = 0
			dmax = max(abs(delta.x), abs(delta.y))
			dsteps = abs(dmax / 121) + 1
			if dsteps == 1:
				self.string += self.EncodeTajimaStitch(delta.x, delta.y, stitch.jump)				
			else:
				for i in range(0,dsteps):
					if i < dsteps -1:
						self.string += self.EncodeTajimaStitch(delta.x/dsteps, delta.y/dsteps, stitch.jump, )
						sum_x += delta.x/dsteps
						sum_y += delta.y/dsteps
					else:
						self.string += self.EncodeTajimaStitch(delta.x - sum_x, delta.y - sum_y, stitch.jump)					
			self.pos = stitch		

		self.string += chr(0x00)
		self.string += chr(0x00)
		self.string += chr(0xF3)
			
		return self.string
	
			
	def import_tajima(self, filename):
		"""read an EXP/Melco file

		Args:
			filename
		"""			
		
		# TODO!!!
		
		# read in an EXP/Melco file
		(lastx, lasty) = (0, 0)
		(self.maxx, self.maxy) = (0, 0)
		(self.minx, self.miny) = (0, 0)
		
		# add Stitch at origin or not?
		self.addStitch(Point(lastx, lasty, False))
		
		jump = False
		f = open(filename, "rb")
		header = f.read(512)

		while True:
			rec = f.read(3)

			# Bad record or end of file
			if len(rec) < 3:
					break

			b1 = ord(rec[0])
			b2 = ord(rec[1])
			b3 = ord(rec[2])

			# End of file
			if b3 == 0xF3:
					break

			(dx, dy, jump) = self.DecodeTajimaStitch(b1, b2, b3)
			lastx = lastx + dx
			lasty = lasty + dy			
			self.addStitch(Point(lastx, lasty, jump))
			
		f.close()
		dbg.write("reading EXP: loaded from file: %s\n" % (filename))
		dbg.write("reading EXP: number of stitches: %d\n" % len(self.coords))
		self.translate_to_origin()



	############################################
	#### Brother / PES
	############################################
	
			
	def save_as_pes(self, filename):
		"""converts stitches to EXP/Melco format

		Returns:
			string (EXP/Melco)
		"""		
	
		dbg.write("Warning: PES export is still experimental!")	
		# PES has maximum value of 64 for stitch lengt p direction
		
		self.flatten(max_length=63)
		
		(self.minx, self.maxx) = (self.coords[0].x, self.coords[0].x)
		(self.miny, self.maxy) = (self.coords[0].y, self.coords[0].y)
		if (len(self.coords)==0):
			return
		for p in self.coords:
			self.minx = min(self.minx, p.x)
			self.miny = min(self.miny, p.y)
			self.maxx = max(self.maxx, p.x)
			self.maxy = max(self.maxy, p.y)
		sx = self.maxx - self.minx
		sy = self.maxy - self.miny

		# helper functions
		def writeInt32(f,i):
			f.write(pack('<I', i))

		def writeInt16(f,i):
			f.write(pack('H', i))
					
		def writeInt8(f,i):
			f.write(pack('B', i))	
							
		
		self.pos = self.coords[0]
		dbg.write("export - stitch count: %d\n" % len(self.coords))
		
		f = open(filename,"w")
		
		# PES Block v1		
		f.write("#PES0001")		
		
		writeInt32(f,0) # pecblock pointer	
			
		writeInt16(f,0) #  a value of 1 here seems to indicate design data is over 100KB long, or 0 for less than 100KB
		writeInt16(f,1)
		writeInt16(f,1)
		writeInt16(f,0xFFFF)
		writeInt16(f,0)
		
		# CEmbOne Block v1
		writeInt16(f,7)
		f.write("CEmbOne")
		
		writeInt16(f,0) # min x?
		writeInt16(f,0) # min y?
		writeInt16(f,0) # max x?
		writeInt16(f,0) # max y?	
		
		writeInt16(f,0) # min x?
		writeInt16(f,0) # min y?
		writeInt16(f,0) # max x?
		writeInt16(f,0) # max y?	
		
		writeInt32(f,0)
		writeInt32(f,0)
		writeInt32(f,0)
		writeInt32(f,0)	
		writeInt32(f,0)	
		writeInt32(f,0)	
		
		writeInt16(f,1)		
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)	
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)
		writeInt16(f,0)

		# CEmbOne Block v1
		writeInt16(f,7)
		f.write("CSewSeq")
		
		#CSewSeg Stitch Data
		writeInt32(f,0)
	
		
		#PEC Code Block Stitch Data
		pecstart = f.tell() 			
		for i in range(0,550):
			writeInt8(f,0)

		f.seek(8)
		writeInt32(f,pecstart)
		f.seek(77)
		writeInt16(f,sx) # width
		writeInt16(f,sy) # height
		f.seek(pecstart+49)
		writeInt8(f,0) # num colors
		f.seek(pecstart+532)
		
		for stitch in self.coords[0:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int	
							
			if stitch.jump:
				dbg.write("export to PES: ignore jump stitches!!!!!\n")

				x = abs(delta.x) & 0x7FF
				if x < 0:
					x =  (x + 0x1000 & 0x7FF) | 0x800
				
				x = ((x >> 8) & 0x0F) | 0x80
				writeInt8(f,x)
				writeInt8(f,(x & 0xFF))	
				
				y= abs(delta.y) & 0x7FF
				if y < 0:
					y =  (y + 0x1000 & 0x7FF) | 0x800
				
				y= ((y >> 8) & 0x0F) | 0x80
				writeInt8(f,y)		
				writeInt8(f,(y & 0xFF))		

			else:
				if delta.x >= 0:
					writeInt8(f,delta.x)
				else:
					writeInt8(f,delta.x + 128)
				
				delta.y *= -1	
				if delta.y >= 0:
					writeInt8(f,delta.y)
				else:
					writeInt8(f,delta.y+128)
												
			self.pos = stitch		
		
		writeInt8(f,0xFF)
		writeInt8(f,0x00)
		
		f.close()

	
	def import_pes(self, filename):
		"""read a PES Brother file

		Args:
			filename
		"""			
		
		# helper functions
		def readInt32(f):
			data = unpack('<I', f.read(4))[0]
			return data

		def readInt16(f):
			data = int(unpack('H', f.read(2))[0])
			return data	
					
		def readInt8(f):
			data = int(unpack('B', f.read(1))[0])
			return data		
					
		(lastx, lasty) = (0, 0)
		(self.maxx, self.maxy) = (0, 0)
		(self.minx, self.miny) = (0, 0)
		jump = False
		f = open(filename, "rb")

		# read PES header signature
		sig = f.read(4)
		if not sig == "#PES":
			dbg.write("error reading PES: not a PES file!");
			exit()
		dbg.write("reading PES file: header found - version ")
		version = f.read(4)
		dbg.write(version)
		dbg.write("\n")
		
		pecstart = readInt32(f)	
		f.seek(77)
		width =  readInt16(f)
		height =  readInt16(f)
		dbg.write("reading PES: dimension is %d x %d mm\n" % (width/10.0, height/10.0))
		
		# No. of colors in file
		f.seek(pecstart + 48)
		numColors = readInt8(f) + 1
		dbg.write("reading PES:  %d colors - but ignoring colors for now\n" % numColors)

		# derived from stitchloader.py
		# Beginning of stitch data
		f.seek(pecstart + 532)
		while 1:
			val1 = readInt8(f)
			val2 = readInt8(f)
			
			if val1 is None or val2 is None:
				break
			elif val1 == 255 and val2 == 0:
				break
			elif val1 == 254 and val2 == 176:
				nn = readInt8(f)
				dbg.write("reading PES: ignoring color change\n")
			else:
				if val1 & 128 == 128: # 0x80
					#this is a jump stitch
					jump = True
					x = ((val1 & 15) * 256) + val2
					if x & 2048 == 2048: # 0x0800
						x = x - 4096
					#read next byte for Y value
					val2 = readInt8(f)
				else:
					#normal stitch
					jump = False
					x = val1
					if x > 63:
						x = x - 128
				
				if val2 & 128 == 128: # 0x80
					#this is a jump stitch
					jump = True
					val3 = readInt8(f)
					y = ((val2 & 15) * 256) + val3
					if y & 2048 == 2048: # 0x0800
						y = y - 4096
				else:
					#normal stitch
					jump = False
					y = val2
					if y > 63:
						y = y - 128
				#flip vertical coordinate 
				x, y = x, -y

				lastx = lastx + x
				lasty = lasty + y	
				self.addStitch(Point(lastx, lasty, jump))
			

	############################################
	#### PNG
	############################################
	
	
	def save_as_png(self, filename, mark_stitch=False):	
		"""save design as PNG image
		
		Args:
			filename
			mark_stitches: boolean (mark stitches with "X")
		"""			
		border = 5
		stc = 2
		stitch_color = (0, 0, 255, 0)
		line_color = (0, 0, 0, 0)
		
		self.scale(pixels_per_millimeter/10.0)

		(self.maxx, self.maxy) = (self.coords[0].x, self.coords[0].y)
		(self.minx, self.miny) = (self.coords[0].x, self.coords[0].y)
		for p in self.coords:
			self.minx = min(self.minx, p.x)
			self.miny = min(self.miny, p.y)
			self.maxx = max(self.maxx, p.x)
			self.maxy = max(self.maxy, p.y)

		sx = int( self.maxx - self.minx + 2*border )
		sy = int( self.maxy - self.miny + 2*border )

		dbg.write("creating PNG image with size %d x %d\n" % (sx,sy))
		img = Image.new("RGB", (sx, sy), (255, 255, 255))
		draw  =  ImageDraw.Draw(img)	
		last = self.coords[0]
				
		def mark_point(point):
			draw.line(
				(point.x + border - stc, self.maxy - point.y + border - stc, 
				 point.x + border + stc, self.maxy - point.y + border + stc), 
				 fill=stitch_color)
			draw.line(
				(point.x + border + stc, self.maxy - point.y + border - stc, 
				 point.x + border - stc, self.maxy - point.y + border + stc), 
				 fill=stitch_color)			
		
		if(mark_stitch and not last.jump):
			mark_point(last)
					 		
		for stitch in self.coords[0:]:
			
			if stitch.jump:
				line_color = (255, 0, 0, 0)
				stitch_color = (0, 0, 255, 0)
			else:
				line_color = (0,0,0,0)
				stitch_color = (0,0,255,0)
				
			p = stitch.as_int()
			draw.line(
				(last.x + border, self.maxy - last.y + border, 
				 p.x + border , self.maxy - p.y + border), 
				fill=line_color)
			
			if(mark_stitch and not stitch.jump):
				mark_point(p)
					 
			if(mark_stitch and not stitch.jump and last.jump):
				mark_point(last)
								
			last = p		
		img.save(filename, "PNG")	
		dbg.write("saving image to file: %s\n" % (filename))


	############################################
	#### SVG
	############################################
		
				
	def export_svg(self):
		"""converts design to SVG paths 
		
		Return:
			string with SVG-data
		"""					
		(self.maxx, self.maxy) = (self.coords[0].x, self.coords[0].y)
		(self.minx, self.miny) = (self.coords[0].x, self.coords[0].y)
		for p in self.coords:
			self.minx = min(self.minx, p.x)
			self.miny = min(self.miny, p.y)
			self.maxx = max(self.maxx, p.x)
			self.maxy = max(self.maxy, p.y)

		sx = int( self.maxx - self.minx)
		sy = int( self.maxy - self.miny)
		
		# TODO convert to pixel
		# conversion factor: 
		# fact = 72.0 / 254
				
		self.str = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="%d" height="%d" viewBox="0 -%d %d 0"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <title>Embroidery export</title>
  <path fill=\"none\" stroke=\"black\" d=\"""" % (sx, sy, sx, sy)
		self.pos = self.coords[0]
		last_jump = False
		self.str += "M %d %d" % (self.pos.x, sy - self.pos.y )
		for stitch in self.coords[0:]:			
			if stitch.jump:
				if not last_jump:
					self.str += "\" />\n"
				last_jump = True
			else:
				if last_jump:
					#self.str += "  <path fill=\"none\" stroke=\"red\" d=\"M %d %d L %d %d\" />\n" % (last_x, sy-last_y, stitch.x,  sy-stitch.y)
					self.str += "  <path fill=\"none\" stroke=\"black\" d=\"M %d %d" % (stitch.x,  sy - stitch.y)
					last_jump = False
				self.str += " L %d %d" % (stitch.x,  sy - stitch.y)
		self.str += "\" />\n</svg>\n"
		return self.str		
		
	def save_as_svg(self, filename):
		"""save design as SVG vector image
		
		Args:
			filename
		"""					
		f = open(filename, "wb")
		f.write(self.export_svg())
		f.close()
		dbg.write("saving SVG to file: %s\n" % (filename))		

	def import_svg(self, filename):
		"""read a SVG file (for now just what we have written ourselves)
		
		Args:
			filename
		"""			
		dbg.write("loading SVG: %s\n" % (filename))	
		dbg.write("Warning: SVG import is experimental!")	
					
		first = True
		jump = False
		from xml.dom import minidom
		xmldoc = minidom.parse(filename)
		itemlist = xmldoc.getElementsByTagName('path') 
		for s in itemlist :
			if not first:
				jump = True
			t = s.attributes['d'].value.strip().split("M")
			points = t[1].split("L")
			for p in points:
				p = p.strip()
				x = int(p.split(' ')[0])
				y = int(p.split(' ')[1])
				self.addStitch(Point(x, -y, jump))
				jump = False
				first = False



############################################
#### Turtle and Test classes
############################################		

class Test:
	def __init__(self):
		emb = Embroidery()
		for x in range(0,301,30):
			emb.addStitch(Point(x, 0));
			emb.addStitch(Point(x, 15));
			emb.addStitch(Point(x, 0));

		for x in range(300,-1,-30):
			emb.addStitch(Point(x, -12));
			emb.addStitch(Point(x, -27));
			emb.addStitch(Point(x, -12));

		fp = open("test.exp", "wb")
		fp.write(emb.export_melco())
		fp.close()

class Turtle:
	def __init__(self):
		self.emb = Embroidery()
		self.pos = Point(0.0,0.0)
		self.dir = Point(1.0,0.0)
		self.emb.addStitch(self.pos)

	def forward(self, dist):
		self.pos = self.pos+self.dir.mul(dist)
		self.emb.addStitch(self.pos)

	def turn(self, degreesccw):
		radcw =  -degreesccw/180.0*3.141592653589
		self.dir = Point(
			math.cos(radcw)*self.dir.x-math.sin(radcw)*self.dir.y,
			math.sin(radcw)*self.dir.x+math.cos(radcw)*self.dir.y)

	def right(self, degreesccw):
		self.turn(degreesccw)

	def left(self, degreesccw):
		self.turn(-degreesccw)
	
class Koch(Turtle):
	def __init__(self, depth):
		Turtle.__init__(self)

		edgelen = 750.0
		for i in range(3):
			self.edge(depth, edgelen)
			self.turn(120.0)

		fp = open("koch%d.exp" % depth, "wb")
		fp.write(self.emb.export_melco())
		fp.close()
	
	def edge(self, depth, dist):
		if (depth==0):
			self.forward(dist)
		else:
			self.edge(depth-1, dist/3.0)
			self.turn(-60.0)
			self.edge(depth-1, dist/3.0)
			self.turn(120.0)
			self.edge(depth-1, dist/3.0)
			self.turn(-60.0)
			self.edge(depth-1, dist/3.0)

class Hilbert(Turtle):
	def __init__(self, level):
		Turtle.__init__(self)

		self.size = 10.0
		self.hilbert(level, 90.0)

		fp = open("hilbert%d.exp" % level, "wb")
		fp.write(self.emb.export_melco())
		fp.close()

	# http://en.wikipedia.org/wiki/Hilbert_curve#Python
	def hilbert(self, level, angle):
		if (level==0):
			return
		self.right(angle)
		self.hilbert(level-1, -angle)
		self.forward(self.size)
		self.left(angle)
		self.hilbert(level-1, angle)
		self.forward(self.size)
		self.hilbert(level-1, angle)
		self.left(angle)
		self.forward(self.size)
		self.hilbert(level-1, -angle)
		self.right(angle)

if (__name__=='__main__'):
	#Test()
	#Koch(4)
	#Hilbert(4)
	print("test")
	emb = Embroidery()
	emb.import_melco("test-files/MerAut.exp")
	#emb.import_svg("tree.svg")
	#emb.import_pes("test-files/ptest.pes")
	#emb.translate_to_origin()
	emb.scale(1)
	emb.save_as_pes("test-files/MerAut.pes")
