from rc import VON_BASE_PATH
import model, view

parser = view.Parser(prog='search', \
		description='Searches for problems by tags or text.')
parser.add_argument('s_terms', nargs='*', metavar='term', \
		help="Terms you want to search for.")
parser.add_argument('-t', '--tag', nargs='+', metavar='tag', \
		dest='s_tags', default = [], help="Tags you want to search for.")
parser.add_argument('-k', '--source', nargs='+', metavar='source', \
		dest='s_sources', default =[],  help="Sources you want to search for.")
parser.add_argument('-r', '--refine', action = "store_const", \
		default = False, const = True, \
		help = "Prune through the Cache rather than the whole database.")

def main(self, argv):
	opts = parser.process(argv)
	if len(opts.s_terms + opts.s_tags + opts.s_sources) == 0:
		view.warn("Must supply at least one search keyword!")
		return

	search_path = model.getcwd()
	if search_path != VON_BASE_PATH:
		view.out("Search restricted to " + view.APPLY_COLOR("BOLD_GREEN", search_path))
	result = model.runSearch(
			terms = opts.s_terms, tags = opts.s_tags, sources = opts.s_sources,
			refine = opts.refine, path = search_path)

	for i, entry in enumerate(result):
		view.printEntry(entry)
	if len(result) == 0:
		view.warn("No matches found.")
