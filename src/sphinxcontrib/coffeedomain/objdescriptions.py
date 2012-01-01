from sphinx.directives import ObjectDescription

class CoffeeFile(ObjectDescription):
    required_arguments = 1

    def run(self):
        return super(CoffeeFile, self).run()

class CoffeeClass(ObjectDescription):
    required_arguments = 1

    def run(self):
        return super(CoffeeFile, self).run()

class CoffeeFunction(ObjectDescription):
    required_arguments = 1

    def run(self):
        return super(CoffeeClass, self).run()
