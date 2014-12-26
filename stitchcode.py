#!/usr/bin/env python

# ------------------------------------------------------------------
# stitchcode - a simple Embroidery class for python
# ------------------------------------------------------------------
# Copyright (C) 2013 Michael Aschauer
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
from struct import unpack
from PIL import Image,ImageDraw
dbg = sys.stderr

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
		return "Pt(%s,%s,%s)" % (self.x,self.y,self.jump)

	def length(self):
		return math.sqrt(math.pow(self.x,2.0)+math.pow(self.y,2.0))

	def as_int(self):
		return Point(int(round(self.x)), int(round(self.y)))

	def as_tuple(self):
		return (self.x,self.y)

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
		
	def setMaxStitchLength(clamp=127):
		self.clamp = clamp

	def addStitch(self, coord):
		self.coords.append(coord)

	def translate_to_origin(self):
		(self.minx,self.maxx) = (9999999,0)
		(self.miny,self.maxy) = (9999999,0)
		if (len(self.coords)==0):
			return
		for p in self.coords:
			self.minx = min(self.minx,p.x)
			self.miny = min(self.miny,p.y)
			self.maxx = max(self.maxx,p.x)
			self.maxy = max(self.maxy,p.y)
		sx = self.maxx-self.minx
		sy = self.maxy-self.miny
		for p in self.coords:
			p.x -= self.minx
			p.y -= self.miny
		dbg.write("translated to origin. resulting field size: %0.2fmm x %0.2fmm\n" % (sx/10,sy/10))

	def scale(self, sc):
		dbg.write("scale to %d%%\n" % (sc * 100))
		for p in self.coords:
			p.x *= sc
			p.y *= sc

	def add_endstitches(self, length=10, max_stitch_length=127, dbg=sys.stderr):
		# adds endstitches before and after stitches that are too long
		
		dbg.write("add endstitches BEGIN - stitch count: %d\n" % len(self.coords))
		self.pos = self.coords[0]
		new_coords = []
		new_coords.append(self.coords[0])
		for stitch in self.coords[1:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int		
			dmax = max(abs(delta.x),abs(delta.y))

			if dmax <= max_stitch_length:
				new_coords.append(stitch)				
			else:
				x2 = length * delta.x / delta.length()
				y2 = length * delta.y / delta.length()
				new_coords.append(Point(old_int.x+x2,old_int.y+y2))
				new_coords.append(self.pos)
				new_coords.append(stitch)			
				new_coords.append(Point(new_int.x-x2,new_int.y-y2))
				new_coords.append(stitch)						
			self.pos = stitch
		self.coords = new_coords
		dbg.write("add endstitches END - stitch count: %d\n" % len(self.coords))
	
	
	def add_endstitches_to_jumps(self, length=10, dbg=sys.stderr):
		# adds endstitches before and after jump stitches.		
		
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

	def to_triple_stitches(self, length=2, dbg=sys.stderr):
		# convert to triple stitches	
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

	def to_red_work(self, length=3, dbg=sys.stderr):
		# convert to triple stitches	
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
		
	def flatten(self, max_length=127, dbg=sys.stderr):
		# flatten file - interpolate stitches that are too long
		
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
				dmax = max(abs(delta.x),abs(delta.y))
				dsteps = abs(dmax / max_length) + 1
				if dmax > max_length and not stitch.jump:
					for i in range(0, dsteps):					
						x =  last_stitch.x + (i+1) * delta.x/dsteps					
						y = last_stitch.y +  (i+1) * delta.y/dsteps
						new_coords.append(Point(x,y))			
				else:
					new_coords.append(stitch)
				self.pos = stitch
		self.coords = new_coords
		dbg.write("flatten END - stitch count: %d\n" % len(self.coords))

	############################################
	#### FILE IMPORT AND EXPORT
	############################################

	def save_as_exp(self, filename):
		# save as EXP File
		f = open(filename, "wb")
		f.write(self.export_melco())		
		f.close()
		dbg.write("saved to file: %s\n" % (filename))
		
	def export_melco(self, dbg=sys.stderr):
		# return stitches in EXP/Melco format
		self.str = ""
		self.pos = self.coords[0]
		dbg.write("Export - stitch count: %d\n" % len(self.coords))
		
		for stitch in self.coords[1:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int	
							
			def move(x,y):
				if (x<0): x = x + 256
				self.str+=chr(x)
				if (y<0): y = y + 256
				self.str+=chr(y)
				
			#do several interpolated steps if too long			
			dmax = max(abs(delta.x),abs(delta.y))
			dsteps = abs(dmax / 127) + 1
			for i in range(0,dsteps):
				if stitch.jump:
					self.str+=chr(0x80)
					self.str+=chr(0x04)
				move(delta.x/dsteps, delta.y/dsteps)	
			self.pos = stitch
			
		return self.str
		
	def import_melco(self, filename):
		# read in an EXP/Melco file
		(lastx, lasty) = (0,0)
		(self.maxx, self.maxy) = (0,0)
		(self.minx, self.miny) = (0,0)
		jump = False
		f = open(filename, "rb")
		byte =" "
		while byte:
			byte = f.read(1)
			if byte != "" and len(byte) > 0:
				if byte == chr(0x80):
					byte = f.read(1)
					if byte == chr(0x04) or byte == chr(0x02)  or byte == chr(0x00):					
						jump = True
					elif byte == chr(0x01) or byte == chr(0x02):
						dbg.write("ignoring color change")
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
					if dx != 0 and dy != 0:
						self.addStitch(Point(lastx, lasty, jump))
					jump = False
		f.close()
		dbg.write("loaded file: %s\n" % (filename))
		self.translate_to_origin()
	
	def import_pes(self, filename):
		# read in an PES Brother file
		
		def readInt32(file):
			data = unpack('<I', file.read(4))[0]
			return data

		def readInt16(file):
			data = int(unpack('H', file.read(2))[0])
			return data	
					
		def readInt8(file):
			data = int(unpack('B', file.read(1))[0])
			return data		
					
		(lastx, lasty) = (0,0)
		(self.maxx, self.maxy) = (0,0)
		(self.minx, self.miny) = (0,0)
		jump = False
		f = open(filename, "rb")

		# derived from stitchloader.py
		sig = f.read(4)
		if not sig == "#PES":
			dbg.write("not an exp file");
			exit()
		dbg.write("found PES header - version ")
		version = f.read(4)
		dbg.write(version)
		dbg.write("\n")
		
		pecstart = readInt32(f)
		
		f.seek(77)
		width =  readInt16(f)
		height =  readInt16(f)
		dbg.write("dimension %d x %d mm\n" %(width/10.0,height/10.0))
		
		#No. of colors in file
		f.seek(pecstart + 48)
		numColors = readInt8(f) + 1
		dbg.write("%d colors - but ignoring colors for now\n" % numColors)

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
				dbg.write("ignoring color change\n")
			else:
				if val1 & 128 == 128: # 0x80
					#this is a jump stitch
					jump = True
					x = ((val1 & 15) * 256) + val2
					if x & 2048 == 2048: # 0x0800
						x= x - 4096
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
			
	def save_as_png(self, filename, mark_stitch=False):	
		# Save as PNG image
		border=5
		stc = 2
		stitch_color = (0,0,255,0)
		line_color = (0,0,0,0)

		(self.maxx, self.maxy) = (0,0)
		(self.minx, self.miny) = (9999999,9999999)
		for p in self.coords:
			self.minx = min(self.minx,p.x)
			self.miny = min(self.miny,p.y)
			self.maxx = max(self.maxx,p.x)
			self.maxy = max(self.maxy,p.y)

		sx = int( self.maxx - self.minx + 2*border )
		sy = int( self.maxy - self.miny + 2*border )

		img = Image.new("RGB", (sx,sy), (255,255,255))
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
					 		
		for stitch in self.coords[1:]:
			
			if stitch.jump:
				line_color = (255,0,0,0)
				stitch_color = (0,0,255,0)
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
		dbg.write("saved image to file: %s\n" % (filename))
	
				
	def export_svg(self, dbg=sys.stderr):
		(self.maxx, self.maxy) = (0,0)
		(self.minx, self.miny) = (9999999,9999999)
		for p in self.coords:
			self.minx = min(self.minx,p.x)
			self.miny = min(self.miny,p.y)
			self.maxx = max(self.maxx,p.x)
			self.maxy = max(self.maxy,p.y)

		sx = int( self.maxx - self.minx)
		sy = int( self.maxy - self.miny)
		
		fact = 72.0 / 254
				
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
		for stitch in self.coords[1:]:			
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
				last_x = stitch.x
				last_y = stitch.y
		self.str += "\" />\n</svg>\n"
		return self.str		
		
	def save_as_svg(self, filename):
		fp = open(filename, "wb")
		fp.write(self.export_svg())
		fp.close()			

	def import_svg(self, filename):
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
	emb.import_svg("tree.svg")
	#emb.import_pes("test-files/Pinguin23.pes")
	#emb.translate_to_origin()
	emb.scale(1)
	emb.save_as_png("test.png")
