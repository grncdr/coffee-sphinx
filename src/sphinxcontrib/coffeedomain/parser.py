# Parser and AST traversers
import json
from os import path
from subprocess import Popen, PIPE

class CoffeeParser(object):
    """
    A simple wrapper that finds and parses .coffee files in a source directory.
    The parsed files are scanned for doc-comments and the result is cached.
    """

    parser_script = path.join(path.abspath(path.dirname(__file__)), 'nodes_to_json.coffee')
    files = {}
    src_dir = '/Users/stephen/dev/griddle/src'

    def __init__(self, src_dir):
        self.src_dir = src_dir
 
    def get_nodes(self, filename):
        if filename not in self.files:
            parser = Popen(['coffee', self.parser_script,
                            path.join(self.src_dir, filename)],
                           stdout=PIPE)
            self.files[filename] = CoffeeNodeList(json.load(parser.stdout))
        return self.files[filename]

from UserDict import DictMixin
class CoffeeNode(DictMixin, object):
    def __init__(self, data, parent=None, name=None, siblings=None):
        self.tag = data.keys()[0]
        self.data = data[self.tag]
        self.parent = parent
        self.siblings = siblings

    def keys(self): return self.data.keys()
    def __getitem__(self, key):
        i = self.data[key]
        if type(i) == dict:
            return CoffeeNode(i, parent=self, name=key)
        elif type(i) == list:
            return CoffeeNodeList(i, parent=self, name=key)
        else:
            return i

    def children(self):
        is_node = lambda n: type(n) in (CoffeeNode, CoffeeNodeList)
        return ((name, node) for name, node in self.items() if is_node(node))

    def __repr__(self):
        return "<%s:%s %s>" % (type(self), self.tag, self.data.keys())

    def find_nodes(self, test):
        results = []
        for name, node in self.children():
            if test(node):
                results.append(node)
            sub_results = node.find_nodes(test)
            if sub_results:
                results.extend(sub_results)
        return results

    @property
    def next_sibling(self):
        if not self.siblings:
            return None
        idx = self.siblings.index(self) + 1
        if idx >= len(self.siblings):
            return None
        return self.siblings[idx]

    @property
    def prev_sibling(self):
        if not self.siblings:
            return None
        idx = self.siblings.index(self) - 1
        if idx < 0:
            return None
        return self.siblings[idx]

    def find_parent(self, tag):
        maybe_it = self.parent
        while maybe_it:
            if maybe_it.tag == tag: break
            maybe_it = maybe_it.parent
        return maybe_it

    def __eq__(self, other):
        return self is other

class CoffeeNodeList(list):
    def __init__(self, nodes, name="TOP", parent=None):
        self.tag = None
        self.name = name
        self.parent = parent
        self.extend(CoffeeNode(node, self.parent, siblings=self) for node in nodes)

    def find_nodes(self, test):
        results = []
        for node in self:
            if test(node):
                results.append(node)
            results.extend(node.find_nodes(test))
        return results

    def children(self):
        return self
