import model, view
from rc import EDITOR, SEPERATOR, NSEPERATOR, TAG_HINT_TEXT

import clipboard
import datetime
import tempfile
import subprocess
import yaml
import string
import os
import traceback

def user_file_input(initial = "", extension = ".tmp"):
	"""Opens in $EDITOR a file with content 'initial'
	and 'extension', and returns edited file."""

	with tempfile.NamedTemporaryFile(suffix=extension) as tf:
		tf.write(initial)
		tf.flush()
		subprocess.call([EDITOR, tf.name])

		# do the parsing with `tf` using regular File operations.
		# for instance:
		tf.seek(0)
		edited_message = ''.join(tf.readlines())
	return edited_message

def alert_error_tryagain(message = ''):
	"""Prints an error message and waits for user to confirm."""
	return raw_input(message + ' ')

PS_INSTRUCT = """% Input your problem and solution below.
% Three dashes on a newline indicate the breaking points.
% vim: tw=72"""

def get_bodies(raw_text, opts):
	initial = PS_INSTRUCT + NSEPERATOR + raw_text
	while True:
		# TODO maybe give user instructions
		raw_ps = user_file_input(initial = initial, extension = ".tex")
		if raw_ps.count(SEPERATOR) >= 1:
			bodies = [_.strip() for _ in raw_ps.split(SEPERATOR)[1:]]
			if bodies[0] == '': return None
			return bodies
		elif raw_ps.strip() == "":
			return None
		else:
			alert_error_tryagain("Bad format: can't find separator. Try again.")
			initial = raw_ps
	return bodies

DEFAULT_PATH = model.getcwd()
YAML_DATA_FILE = """# Input your problem metadata here

source: {source}     # e.g. USAMO 2000/6. This must be unique
desc:   <++>     # e.g. Fiendish inequality
path:   {path}<++>
tags:   [{now.year}-{now.month:02d}, <++>] # don't forget difficulty and shape!

{hint}"""

def file_escape(s):
	s = s.replace("/", "-")
	s = s.replace(" ", "")
	s = ''.join([_ for _ in s if _ in string.letters+string.digits+'-'])
	if s == '':
		s += 'emptyname'
	return s

def get_yaml_info(opts):
	initial = YAML_DATA_FILE.format(\
			path = model.completePath(DEFAULT_PATH),
			now = datetime.datetime.now(),\
			source = "<++>" if opts.source is None else opts.source,
			hint = TAG_HINT_TEXT)
	while True:
		raw_yaml = user_file_input(initial = initial, extension = ".yaml")
		try:
			d = yaml.load(raw_yaml)
			if d is None:
				return (None, None)
			assert 'path' in d, "Path is mandatory"
			assert 'source' in d, "Source is mandatory"
			if d['path'][-1] != '/':
				d['path'] += '/'
			assert os.path.isdir(d['path']), d['path'] + " directory non-existent"
			target = d['path'] + file_escape(d['source']) + '.tex'
			assert not os.path.isfile(target), target + " already taken"
		except AssertionError:
			# TODO test this
			traceback.print_exc()
			alert_error_tryagain("Okie dokie?")
			initial = raw_yaml
		else:
			del d['path']
			return (target, yaml.dump(d).strip())

def do_add_problem(raw_text, opts):
	"""Core procedure. Opens two instances of editors to solicit user input
	on problem and produce a problem instance."""

	# Get problem and solution
	bodies = get_bodies(raw_text, opts)
	if bodies is None:
		view.warn("Aborting due to empty input...")
		return
	target, out_yaml = get_yaml_info(opts)
	if out_yaml is None:
		view.warn("Aborting due to empty input...")
		return
	out_text = NSEPERATOR.join([out_yaml]+bodies)
	p = model.addProblemByFileContents(target, out_text)
	view.printEntry(p.entry)

parser = view.Parser(prog='add', description='Adds a problem to VON.')
parser.add_argument('source', default = None, nargs = '?',
		help="If specified, sets the source for the new problem.")
parser.add_argument('-f', '--file', dest = 'filename', default = None,
		help="If specified, uses contents of file as body")

def main(self, argv):
	opts = parser.process(argv)
	opts.verbose = True
	if opts.filename is not None:
		if not os.path.isfile(opts.filename):
			view.error("The file " + opts.filename +  " doesn't exist")
			return
		with open(opts.filename) as f:
			initial_text = ''.join(f.readlines())
	else:
		initial_text = clipboard.paste()
		if initial_text.strip() == '':
			initial_text = '<++>'
	do_add_problem(initial_text, opts)
