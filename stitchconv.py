#!/usr/bin/env python
#######################################
#
# manipulate and process EXP files
#
# author:(c) Michael Aschauer <m AT ash.to>
# www: http:/m.ash.to
# licenced under: GPL v3
# see: http://www.gnu.org/licenses/gpl.html
#
#######################################

import stitchcode
import getopt
import sys

def usage():
	print """
usage: stitchconv.py [options] -i INPUT-FILE -o OUTPUT-FILE

Embroidery file conversion and manipulation.
input supported: Melco/EXP, Brother/PES, SVG (partly)
output supported: Melco/EXP, PNG, SVG, Brother/PES (partly)

options:
    -h, --help              print usage
    -i, --input=FILE        input file
    -o, --output=FILE       output file
    -z, --zoom=FACTOR       zoom in/out
    -t, --to-triples        convert to triple stitches
    -r, --to-red-work       convert to red work stitches 
    -s, --show-stitches     show stitches (PNG only)      
    -d, --distance=VALUES   distance of triple/redwork stitches in mm
"""

infile = "";
outfile = "";
zoom = 1
distance = 0.3
to_triple_stitches = False
to_red_work = False
show_stitches = False
flatten = False
show_info = False

def process_args():
	global infile, outfile, zoom
	global to_triple_stitches
	global to_red_work
	global distance, show_stitches
	global flatten, show_info
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:o:z:trd:sfx",
			["help", "input=","output=","zoom=","to-triples","to-red-work","show-stitches",
			"distance", "flatten", "show-info", ])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)

	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-o", "--output"):
			outfile = a
		elif o in ("-i", "--input"):
			infile = a
		elif o in ("-z", "--zoom"):
			zoom = float(a)
		elif o in ("-t", "--to-triples"):
			to_triple_stitches = True
		elif o in ("-r", "--to-red_work"):
			to_red_work = True
		elif o in ("-d", "--distance"):
			distance = float(a)	
		elif o in ("-s", "--show-stitch"):
			show_stitches = True						
		elif o in ("-f", "--flatten"):
			flatten = True		
		elif o in ("-x", "--show-info"):
			show_info = True	
		else:
			usage();
			sys.exit()

	if len(infile) == 0:
		print "options required."
		usage()
		sys.exit(2)	

if __name__ == '__main__':
	process_args()
	if not outfile:
		outfile = infile

	emb = stitchcode.Embroidery()
	emb.load(infile)
	emb.scale(zoom)
	emb.translate_to_origin()
	
	if show_info:
		print emb.info()
		exit()

	if to_triple_stitches:
		print "convert to triple stitches"
		emb.to_triple_stitches(distance*10)	
		
	if to_red_work:
		print "convert to red work stitches"
		emb.to_red_work(distance*10)
	
	if flatten:
		emb.flatten()
		
	if show_stitches and (outfile[-3:]).lower() == "png":
		emb.save_as_png(outfile, show_stitches)
	else:
		emb.save(outfile)

		
