from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.directives import ObjectDescription, Directive
from sphinx.roles import XRefRole
from sphinx.domains import Domain, ObjType
from sphinx.domains.python import _pseudo_parse_arglist
from sphinx.locale import l_, _
from sphinx.util.nodes import make_refnode

class CoffeeObj(ObjectDescription):
    def handle_signature(self, sig, signode):
        if self.display_prefix:
            signode += addnodes.desc_annotation(self.display_prefix, self.display_prefix)

        fullname, _, args = sig.partition('(')
        modname, name = fullname.split('::')
        args = args[:-1]
        signode += addnodes.desc_name(name, name)
        if isinstance(self, CoffeeFunction):
            _pseudo_parse_arglist(signode, args)
        return fullname

    def add_target_and_index(self, fqn, sig, signode):
        doc = self.state.document
        if fqn not in self.state.document.ids:
            signode['names'].append(fqn)
            signode['ids'].append(fqn)
            self.state.document.note_explicit_target(signode)
        objects = self.env.domaindata['coffee']['objects']
        objects[fqn] = (self.env.docname, self.objtype)

        indextext = "%s (%s)" % (fqn.replace('::','/'), self.display_prefix.strip())
        self.indexnode['entries'].append(('single', _(indextext), fqn, ''))

# CoffeeModule inherits from Directive to allow it to output titles etc.
class CoffeeModule(Directive):
    required_arguments = 1
    has_content = False

    def run(self):
        env = self.state.document.settings.env
        modname = self.arguments[0].strip()
        env.temp_data['coffee:module'] = modname
        targetnode = nodes.target('', '', ids=['module-' + modname], ismod=True)
        self.state.document.note_explicit_target(targetnode)
        indextext = _('%s (module)') % modname
        inode = addnodes.index(entries=[('single', indextext,
                                         'module-' + modname, '')])
        #section = nodes.section()
        return [nodes.title('', modname), targetnode, inode]


class CoffeeClass(CoffeeObj):
    option_spec = {
        'module': directives.unchanged,
        'export_name': directives.unchanged,
    }
    display_prefix = 'class '

class CoffeeFunction(CoffeeObj):
    option_spec = {
        'module': directives.unchanged,
        'export_name': directives.unchanged,
    }
    display_prefix = 'function '

class CoffeeMethod(CoffeeFunction):
    option_spec = {
        'module': directives.unchanged,
        'class': directives.unchanged,
    }
    display_prefix = 'method '


class CoffeeXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        """ Called after CoffeeDomain.resolve_xref """
        if not has_explicit_title:
            title = title.split('::').pop()
        return title, target

class CoffeeDomain(Domain):
    label = 'CoffeeScript'
    name = 'coffee'
    object_types = {
        'module':      ObjType(l_('module'), 'module'),
        'function':  ObjType(l_('function'),  'func'),
        'class':     ObjType(l_('class'),     'class'),
        'method':    ObjType(l_('method'), 'method')
    }
    directives = {
        'module': CoffeeModule,
        'function': CoffeeFunction,
        'class': CoffeeClass,
        'method': CoffeeMethod,
    }

    roles = {
       'meth': CoffeeXRefRole(),
       'class': CoffeeXRefRole(),
       'func': CoffeeXRefRole(),
    }
    initial_data = {"node_cache": {}, "objects": {}}

    def get_objects(self):
        for fqn, node in self.data['node_cache'].items():
            (docname, objtype) = self.data['objects'][fqn]
            disp_name = fqn.split('::').pop()
            yield (fqn, disp_name, objtype, docname, fqn, 1)
            
    def resolve_xref(self, env, fromdocname, builder, type, target, node, contnode):
        if target[0] == '~':
            target = target[1:]
        doc, _ = self.data['objects'].get(target, (None, None))
        if doc:
            return make_refnode(builder, fromdocname, doc, target, contnode,
                                target)
