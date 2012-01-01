from .parser import CoffeeParser, CoffeeNode
from sphinx.util.docstrings import prepare_docstring
from sphinx.ext.autodoc import Documenter, members_option, bool_option
from pdb import set_trace

def get_docstring(node):
    """
    Extract the doc-comment preceding the node if it exists
    """
    # Special case for file comments
    if node.siblings and node.siblings.index(node) == 1 and not node.parent:
        return None
    prev = node.prev_sibling
    if prev and prev.tag == 'Comment':
        return prev['comment']
        
def variable_name(node):
    if node.tag == 'Assign':
        if node['value'].tag == 'Class':
            return variable_name(node['value'])
        return expand_variable_name(node['variable'])
    elif node.tag == 'Class':
        return node['variable']['base']['value']

def full_name(node):
    if node.tag == 'Assign':
        name = expand_variable_name(node['variable'])
        maybe_class = node.find_parent('Class')
        if maybe_class:
            name = "%s.%s" % (maybe_class['variable']['base']['value'], name)
        return name
    else:
        return None

def expand_variable_name(var):
    parts = []
    for p in var['properties']:
        # Handle indexed properties, they will come out as quoted strings
        if p.tag == 'Index':
            p = p['index']
        if 'name' not in p:
            break
        else:
            parts.append(p['name']['value'])
    if 'value' in var['base']:
        parts.insert(0, var['base']['value'])
    return '.'.join(parts)

class CoffeeASTDocumenter(Documenter):
    priority = 11 # Need to outrank AttributeDocumenter
    option_spec = {
       'members': members_option
    }

    @property
    def filename(self):
        return self.modname + '.coffee'

    @classmethod
    def can_document_member(cls, ast_node, ast_node_name, isattr, p_documenter):
        if not isinstance(ast_node, CoffeeNode):
            return False
        # Always walk down through assignments to find the actual thing
        while ast_node.tag == 'Assign':
            ast_node = ast_node['value']
        return ast_node.tag == cls.documents_ast_node_tag

    def get_object_members(self, want_all=False):
        members = []
        for node in self.get_child_nodes():
            if node.tag == 'Comment': continue
            node.__doc__ = get_docstring(node)
            members.append((variable_name(node), node))
        return False, members

    def import_object(self):
        obj = self.ast_node
        while obj.tag == 'Assign':
            obj = obj['value']
        self.object = obj
        self.object.__doc__ = self.ast_node.__doc__
        return True

    def filter_members(self, members, want_all):
        for (name, node) in members:
            if not node.__doc__:
                continue
            # XXX - Cache the node with a fully-qualified name
            # This is pretty gross, but this name is the only thing passed
            # to the constructor of the Documenter, and trying to look up
            # the node again via the parser is worse.
            #
            # https://bitbucket.org/birkenfeld/sphinx/src/65e4c29a24e4/sphinx/ext/autodoc.py#cl-636
            fqn = '::'.join([self.modname, '.'.join(self.objpath + [name])])
            self.env.domaindata['coffee']['node_cache'][fqn] = node

            yield (name, node, False)

    @property
    def ast_node(self):
        return self.env.domaindata['coffee']['node_cache'][self.name]

    def parse_name(self):
        parts = self.name.split('::')
        self.modname = parts[0]
        self.fullname = self.name
        self.objpath = len(parts) == 2 and parts[1].split('.') or []
        self.args = None
        self.retann = None
        return True

    def format_name(self):
        return self.name

class ModuleDocumenter(CoffeeASTDocumenter):
    objtype = 'module'
    domain = 'coffee'
    content_indent = u'   '
    documents_ast_node_tag = "-----" # Never match nodes
    titles_allowed = True

    @property
    def ast_node(self):
        return self.parser.get_nodes(self.filename)

    @property
    def parser(self):
        domain_data = self.env.domaindata['coffee']
        if 'parser' not in domain_data:
            domain_data['node_cache'] = {}
            domain_data['parser'] = CoffeeParser(self.env.config.coffee_src_dir)
        return domain_data['parser']

    def get_child_nodes(self):
        return self.ast_node

    def generate(self, **kwargs):
        self.parse_name()
        self.real_modname = self.modname
        self.add_directive_header(u'')

        first_node = self.ast_node[0]
        if first_node.tag == 'Comment':
            for line in prepare_docstring(first_node['comment']):
                self.add_line(line, self.name)
        self.document_members(True)

class ClassDocumenter(CoffeeASTDocumenter):
    content_indent = u'   '
    domain = 'coffee'
    objtype = 'class'
    documents_ast_node_tag = 'Class'

    def import_object(self):
        """
        Over-ride import object to add an 'exported as' note to
        module.exports assignments
        """
        super(ClassDocumenter, self).import_object()
        if self.ast_node.tag == 'Assign':
            var_name = expand_variable_name(self.ast_node['variable'])
            if var_name.find('exports') > -1:
                export_name = var_name.partition('exports')[2]
                if export_name:
                    export_name = export_name.strip('.')
                else:
                    export_name = self.modname
                self.object.__doc__ += '\n\nExported as "%s"' % export_name
        return True

    def get_child_nodes(self):
        exprs = self.object['body']['expressions']
        children = []
        for expr in exprs:
            if expr.tag == 'Value' and expr['base'].tag == 'Obj':
                children += expr['base']['properties']
        # TODO - Add support for documenting non properties?
        return children

class FunctionDocumenter(CoffeeASTDocumenter):
    content_indent = u'   '
    domain = 'coffee'
    objtype = 'function'
    documents_ast_node_tag = 'Code'

    def get_child_nodes(self):
        return []

    def format_signature(self):
        param_names = (p['name']['value'] for p in self.object['params'])
        return '(%s)' % ', '.join(param_names)

class MethodDocumenter(FunctionDocumenter):
    objtype = 'method'
    priority = FunctionDocumenter.priority + 1
    
    @classmethod
    def can_document_member(cls, ast_node, ast_node_name, isattr, p_documenter):
        if not isinstance(p_documenter, ClassDocumenter):
            return False
        return FunctionDocumenter.can_document_member(ast_node, ast_node_name,
                                                      isattr, p_documenter)
