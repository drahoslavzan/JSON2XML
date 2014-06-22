#!/usr/bin/python2


# json2xml.py - JSON to XML converter
#
# Copyright (C) 2010, Drahoslav Zan.
# 
# The json2xml.py is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.  
#
# The json2xml.py is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the json2xml.py. If not, see
# <http://www.gnu.org/licenses/>.


import sys
import re
import simplejson as json
import xml.dom.minidom as dom


###############
### General ###
###############

# Print error
def die(msg):
	sys.stderr.write('ERROR: ' + msg + '\n')
	exit(1)


#####################
### Parse options ###
#####################

# Options
optHelp = 0
optInput = ''
optOutput = ''
optN = 0
optR = ''
optS = 0
optI = 0
optL = 0
optE = 0

# Args
args = []

# Parse option with arg
def parseOption(option, i):
	arg = re.match('^' + option + '(=(.*))', sys.argv[i])
	if arg:
		if not arg.group(2):
			die('Missing argument: ' + option)
		return arg.group(2)
	else:
		i += 1
		if i >= len(sys.argv):
			die('Missing argument: ' + option)
		return sys.argv[i]

seq = range(1, len(sys.argv))
for i in seq:
	# --help
	if re.match('^--help$', sys.argv[i]):
		optHelp = 1
	# --input
	elif re.match('^--input', sys.argv[i]):
		optInput = parseOption('--input', i)
		if not re.match('^--input=', sys.argv[i]):
			seq.pop(1)
	# --output
	elif re.match('^--output', sys.argv[i]):
		optOutput = parseOption('--output', i)
		if not re.match('^--output=', sys.argv[i]):
			seq.pop(1)
	# -n
	elif re.match('^-n$', sys.argv[i]):
		optN = 1
	# -r
	elif re.match('^-r', sys.argv[i]):
		optR = parseOption('-r', i)
		if not re.match('^-r=', sys.argv[i]):
			seq.pop(1)
	# -s
	elif re.match('^-s$', sys.argv[i]):
		optS = 1
	# -i
	elif re.match('^-i$', sys.argv[i]):
		optI = 1
	# -l
	elif re.match('^-l$', sys.argv[i]):
		optL = 1
	# -e
	elif re.match('^-e$', sys.argv[i]):
		optE = 1
	# Invalid option
	elif re.match('^-+', sys.argv[i]):
			die('Invalid option: ' + sys.argv[i])
	# Arguments
	else:
		args.append(sys.argv[i])


############
### HELP ###
############

def showHelp(e):
	print 'Usage: ' + sys.argv[0] + ' OPTIONS\n'
	print 'OPTIONS:'
	print '    --help                    Show this help and exit.'
	print '    --input   FILE            Read JSON or XML formatted file from FILE'
	print '                              instead of stdin.'
	print '    --output  FILE            Output written to FILE instead of stdout'
	print '    -n                        Do not generate XML header.'
	print '    [-e] -r   root-element    Set root element for result, with -e'
	print '                              option specified, missing starting block'
	print '                              in JSON formatted input will not'
	print '                              be considered as error.'
	print '    -s                        Transform string types to text elements.'
	print '    -i                        Transform number types to text elements.'
	print '    -l                        Transform literals (true, false, null)'
	print '                              to elements.'
	exit(e)


###########################
### Option dependencies ###
###########################

if len(args) > 0:
	die('No arguments allowed')

depSum = (optInput != '') + (optOutput != '') + (optR != '') + optN \
				 + optS + optI + optL + optE

if (optHelp and depSum):
	die('Combination of parameters not allowed')
if (optE and not optR):
	die('Dependecy for option not satisfied: -e')

if optHelp:
	showHelp(0)

if optInput:
	try:
		INPUT = open(optInput, 'r')
	except Exception, e:
		die(str(e))
else:
	INPUT = sys.stdin

if optOutput:
	try:
		OUTPUT = open(optOutput, 'w')
	except Exception, e:
		die(str(e))
else:
	OUTPUT = sys.stdout


############
### Main ###
############

invalidElementCharactersPattern     = '[<>"\'&]'
invalidElementCharactersReplacement = '-'

# Set element of XML according to options
def xmlElement(elem, item):
	if type(item) is type(None):
		if optL:
			it = xml.createElement(unicode('null'))
			elem.appendChild(it)
		else:
			elem.setAttribute('value', unicode('null'))
	elif type(item) is bool:
		if item:
			itext = 'true'
		else:
			itext = 'false'
		if optL:
			it = xml.createElement(unicode(itext))
			elem.appendChild(it)
		else:
			elem.setAttribute('value', unicode(itext))
	elif (((type(item) is str) or (type(item) is unicode)) and optS) or ((type(item) is int) and optI):
		text = xml.createTextNode(unicode(item))
		elem.appendChild(text)
	else:
		elem.setAttribute('value', unicode(item))

# Conver JSON format to XML, recursive processing
def json2xml(items, doc):
	if type(items) is not dict:
		return
	for i in items.keys():
		elemName = re.sub(invalidElementCharactersPattern,
				invalidElementCharactersReplacement, unicode(i))
		elem = xml.createElement(unicode(elemName))
		doc.appendChild(elem)
		if type(items[i]) is dict:
			json2xml(items[i], elem)
		elif type(items[i]) is type([]):
			array = xml.createElement('array')
			elem.appendChild(array)
			for u in items[i]:
				it = xml.createElement('item')
				array.appendChild(it)
				if type(u) is dict:
					json2xml(u, it)
				else:
					xmlElement(it, u)
		else:
			xmlElement(elem, items[i])

file = INPUT.read()

list = file.splitlines(1)

for l in list:
	if re.match('^[ \t]*\r?\n', l): 				# skip empty lines
		continue
	l = re.sub('^[ \t]*', '', l)
	if re.match('^\[', l): 									# JSON start with array, semi-invalid
		if not optE:
			die('JSON: Block required (use -e to suppress error)')
		file = '{ "' + optR + '" : ' + file + ' }'
		optR = ''
		break
	if optE: 																# not used - turn off
		optE = 0
	break 																	# valid or completely invalid JSON file

# Load JSON file
try:
	items = json.loads(file)
except Exception, e:
	die('JSON: ' + str(e))

# Create XML document
try:
	xml = dom.Document()
except Exception, e:
	die('XML: ' + str(e))

try:
	elem = xml.createElement('dummy') 			# dummy element ensure XML validity
	xml.appendChild(elem)
	json2xml(items, elem)
except Exception, e:
	die('json2xml: ' + str(e))

file = xml.toprettyxml(indent='\t', encoding='UTF-8')

list = file.splitlines(1)

xmlHeader = list[0]

list = list[2:(len(list) - 1)] 						# remove header and dummy elements

file = ''

# Apply options
if optR:
	indent = '\t'
	if not optN:
		file = xmlHeader
		indent = ''
	if not len(list):
		file += '<' + optR + '/>\n'
	else:
		file += '<' + optR + '>\n'
		for l in list:
			file += indent + l
		file += '</' + optR + '>\n'
else:
	if not optN:
		file = xmlHeader
	file += ''.join(list)

# Write XML file
OUTPUT.write(file)


#############
### Clean ###
#############

INPUT.close()
OUTPUT.close()

