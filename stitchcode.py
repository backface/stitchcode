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
from PIL import Image,ImageDraw
dbg = sys.stderr

def abs(x):
	if (x<0): return -x
	return x

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
		return "Pt(%s,%s)" % (self.x,self.y)

	def length(self):
		return math.sqrt(math.pow(self.x,2.0)+math.pow(self.y,2.0))

	def as_int(self):
		return Point(int(round(self.x)), int(round(self.y)))

	def as_tuple(self):
		return (self.x,self.y)

	def __cmp__(self, other):
		return cmp(self.as_tuple(), other.as_tuple())

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
		(self.minx,self.maxx) = (0,0)
		(self.miny,self.maxy) = (0,0)
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
		for p in self.coords:
			p.x *= sc
			p.y *= sc
			
	def export_ksm(self, dbg):
		str = ""
		self.pos = Point(0,0)
		lastColor = None
		for stitch in self.coords:
			if (lastColor!=None and stitch.color!=lastColor):
				mode_byte = 0x99
				#dbg.write("Color change!\n")
			else:
				mode_byte = 0x80
				#dbg.write("color still %s\n" % stitch.color)
			lastColor = stitch.color
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int
			assert(abs(delta.x)<=127)
			assert(abs(delta.y)<=127)
			str+=chr(abs(delta.y))
			str+=chr(abs(delta.x))
			if (delta.y<0):
				mode_byte |= 0x20
			if (delta.x<0):
				mode_byte |= 0x40
			str+=chr(mode_byte)
			self.pos = stitch
		return str

	def export_melco(self, dbg=sys.stderr):
		self.str = ""
		self.pos = self.coords[0]
		dbg.write("stitch count: %d\n" % len(self.coords))
		#lastColor = None
		#numColors = 0x0
		for stitch in self.coords[1:]:
			# ignore colors for the time being
			#if (lastColor!=None and stitch.color!=lastColor):
			#	numColors += 1
			#	# color change
			#	self.str += chr(0x80)
			#	self.str += chr(0x01)
			#	self.str += chr(numColors)
			#	self.str += chr(((numColors+0x80)>>8)&0xff)
			#	self.str += chr(((numColors+0x80)>>0)&0xff)
			#lastColor = stitch.color
			
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int

							
			def move(x,y):
				if (x<0): x = x + 256
				self.str+=chr(x)
				if (y<0): y = y + 256
				self.str+=chr(y)

			if stitch.jump:
				self.str+=chr(0x80)
				self.str+=chr(0x00)
			
			#do several interpolated steps if too long			
			dmax = max(abs(delta.x),abs(delta.y))
			dsteps = abs(dmax / 127) + 1
			#print dmax, dsteps, "(", delta.x,delta.y, ")"
			for i in range(0,dsteps):
				#print " ", i, ":", delta.x/dsteps, delta.y/dsteps
				move(delta.x/dsteps, delta.y/dsteps)	
			
#			clamp values to max							
#			while (delta.x!=0 or delta.y!=0):		

#				def clamp(v):
#					if (v>127):
#						v = 127
#					if (v<-127):
#						v = -127
#					return v	
#				dx = clamp(delta.x)
#				dy = clamp(delta.y)	
#				move(dx,dy)
#				delta.x -= dx
#				delta.y -= dy
				
			#dbg.write("Stitch: %s delta %s\n" % (stitch, delta))
			self.pos = stitch
		return self.str

	def add_endstitches(self, length=20, maxstitch=127, dbg=sys.stderr):
		self.str = ""
		self.pos = self.coords[0]
		new_coords = []
		dbg.write("stitch count: %d\n" % len(self.coords))
		new_coords.append(self.coords[0])
		for stitch in self.coords[1:]:		
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int		
			dmax = max(abs(delta.x),abs(delta.y))
			dmin = min(abs(delta.x),abs(delta.y))
			if dmax <= 127:
				new_coords.append(stitch)
			else:
				d = math.sqrt(pow(delta.x,2)+pow(delta.y,2))
				x2 = length * delta.x / d
				y2 = length * delta.y / d
				print  delta.x,  delta.y, d, "-", x2,y2
				
				new_coords.append(Point(old_int.x+x2,old_int.y+y2))
				new_coords.append(self.pos)
				
				new_coords.append(stitch)
				
				new_coords.append(Point(new_int.x-x2,new_int.y-y2))
				new_coords.append(stitch)
				
			self.pos = stitch
		self.coords = new_coords
				
	def write_exp(self, filename):
		f = open(filename, "wb")
		f.write(self.export_melco())		
		f.close()
		dbg.write("saved to file: %s\n" % (filename))
		
	def import_melco(self, filename):
		(lastx, lasty) = (0,0)
		(self.maxx, self.maxy) = (0,0)
		(self.minx, self.miny) = (0,0)
		self.addStitch(Point(0, 0))
		f = open(filename, "rb")
		byte =" "
		while byte:
			byte = f.read(1)
			if byte != "":
				if byte == chr(0x80):
					dbg.write("ignore jump stich or color change")
					f.read(3)
				else:
					dx = ord(byte)
					if dx > 127:
						dx = dx - 256
					byte = f.read(1)
					dy = ord(byte)
					if dy > 127:
						dy = dy - 256
					lastx = lastx + dx
					lasty = lasty + dy						
					self.addStitch(Point(lastx, lasty))
		f.close()
		dbg.write("loaded file: %s\n" % (filename))
		self.translate_to_origin()


		
	def save_as_png(self, filename, mark_stitch=False):	
		border=5
		stc = 2
		sx = int( self.maxx - self.minx + 2*border )
		sy = int( self.maxy - self.miny + 2*border )
		img = Image.new("RGB", (sx,sy), (255,255,255))
		draw  =  ImageDraw.Draw(img)	
		last = self.coords[0]
		
		for stitch in self.coords[1:]:
			p = stitch.as_int()
			draw.line(
				(last.x + border, self.maxy - last.y + border, 
				 p.x + border , self.maxy - p.y + border), 
				fill=(0,0,0,0))
			if(mark_stitch):
				draw.line(
					(p.x + border - stc, self.maxy - p.y + border - stc, 
					 p.x + border + stc, self.maxy - p.y + border + stc), 
					 fill=(0,0,0,0))
				draw.line(
					(p.x + border + stc, self.maxy - p.y + border - stc, 
					 p.x + border - stc, self.maxy - p.y + border + stc), 
					 fill=(0,0,0,0))
			last = p		
		img.save(filename, "PNG")	
		dbg.write("saved image to file: %s\n" % (filename))
		
		
		
	def export_svg_rel_melco(self, dbg=sys.stderr):
		self.str = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="4cm" height="4cm" viewBox="0 0 400 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <title>Embroidery export</title>
  <rect x="1" y="1" width="398" height="398"
        fill="none" stroke="blue" />
  <path d=\""""
		self.pos = self.coords[0]
		self.str += "M %d %d" % (self.coords[0].x, - self.coords[0].y)
		dbg.write("stitch count: %d\n" % len(self.coords))
		for stitch in self.coords[1:]:
			new_int = stitch.as_int()
			old_int = self.pos.as_int()
			delta = new_int - old_int
				
			while (delta.x!=0 or delta.y!=0):
				def clamp(v):
					if (v>127):
						v = 127
					if (v<-127):
						v = -127
					return v
				dx = clamp(delta.x)
				dy = clamp(delta.y)
				self.str += " l %d %d" % (dx, -dy)
				delta.x -= dx
				delta.y -= dy
				
			self.pos = stitch
		
		self.str += "\" fill=\"none\" stroke=\"black\" stroke-width=\"2\"/></svg>"
		return self.str		
		
	def export_svg(self, dbg=sys.stderr):
		self.str = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="4cm" height="4cm" viewBox="0 -400 400 0"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <title>Embroidery export</title>
  <rect x="1" y="1" width="398" height="398"
        fill="none" stroke="blue" />
  <path d=\""""

		self.pos = self.coords[0]
		#self.str += "M 0 0"
		self.str += "M %d %d" % (self.coords[0].x, - self.coords[0].y)
		for stitch in self.coords[1:]:
			self.str += " L %d %d" % (stitch.x, - stitch.y)

		self.str += "\" fill=\"none\" stroke=\"black\" stroke-width=\"2\"/></svg>"
		return self.str		
		
	def write_svg(self, filename):
		fp = open(filename, "wb")
		fp.write(self.export_svg())
		fp.close()			

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

if (__name__=='__main__'):
	Test()
