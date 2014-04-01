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
usage: exp2png.py [options] -i EXP-FILE -o PNG-FILE

renders an EXP embroidery file as a PNG image

options:
    -h, --help              print usage
    -i, --input=FILE        input EXP file
    -o, --output=FILE       output EXP file
    -z, --zoom=FACTOR       zoom in/out
    -e, --add-endstitches   add end stitches
    -t, --to-triples        convert to triple stitches
"""

infile = "";
outfile = "";
zoom = 1
add_endstitches = False
to_triple_stitches = False

def process_args():
	global infile, outfile, zoom
	global add_endstitches, to_triple_stitches
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hi:o:z:et",
			["help", "input=","output=","zoom=","add-endstitches","to-triples"])
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
		elif o in ("-e", "--add-endstitches"):
			add_endstitches = True	
		elif o in ("-t", "--to-triples"):
			to_triple_stitches = True
		else:
			assert False, "unhandled option"

	if len(infile) == 0:
		print "required."
		usage()
		sys.exit(2)	

if __name__ == '__main__':
	process_args()
	if not outfile:
		outfile = infile

	emb = stitchcode.Embroidery()
	emb.import_melco(infile)
	emb.scale(zoom)
	#emb.translate_to_origin()
	if add_endstitches:
		print "adding end stitches"
		emb.add_endstitches_to_jumps()
	if to_triple_stitches:
		print "convert to triple stitches"
		emb.to_triple_stitches()		
	emb.save_as_exp(outfile)

		
