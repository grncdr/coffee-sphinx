def setup(app):
    app.add_config_value('coffee_src_dir', None, 'env')
    from .domain import CoffeeDomain
    app.add_domain(CoffeeDomain)
    from .documenters import *
    app.add_autodocumenter(ModuleDocumenter)
    app.add_autodocumenter(ClassDocumenter)
    app.add_autodocumenter(FunctionDocumenter)
    app.add_autodocumenter(MethodDocumenter)
