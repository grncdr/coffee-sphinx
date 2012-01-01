# HISTORY: this used to parse the ouput of coffee --nodes, but now it directly uses
#     CS to get more detailed info on nodes
# 
# USAGE: coffee nodes_to_json.coffee hello_world.coffee

CoffeeScript = require "coffee-script" unless window?
  
wrap = (expressions) ->
  expressions = expressions.map (expression) ->
    wrap_obj(expression)
    
wrap_obj = (expression) ->
  expression.children = undefined
  keys = [
    'array',
    'attempt',
    'base',
    'body',
    'condition',
    'elseBody',
    'error',
    'ensure',
    'expression',
    'first',
    'from',
    'index',
    'name',
    'object',
    'otherwise',
    'parent',
    'range',
    'recovery',
    'second',
    'source',
    'subject',
    'to',
    'value',
    'variable',
    ]
  for key in keys
    if expression[key]
      expression[key] = wrap_obj expression[key]
  list_keys = [
    'args',
    'expressions',
    'objects',
    'params',
    'properties',
  ]
  for list_key in list_keys
    if expression[list_key]
      expression[list_key] = wrap expression[list_key]
  if expression.cases
    my_cases = []
    for when_statement in expression.cases
      my_cases.push
        cond: wrap_obj when_statement[0]
        block: wrap_obj when_statement[1]
    expression.cases = my_cases
  name = expression.constructor.name
  if name == 'Obj'
    expression.objects = undefined
  if name && name != 'Array' && name != "String" && name != "Object"
    obj = {}
    obj[name] = expression
    obj
  else
    expression

handle_data = (data) ->
  expressions = CoffeeScript.nodes(data).expressions
  console.log JSON.stringify wrap(expressions), null, "  "

if window?
  # turns coffeescript code into json
  window.CoffeeCoffee.nodes_to_json = (code) ->
    expressions = window.CoffeeScript.nodes(code).expressions
    wrap(expressions)

  # turns the ast CoffeeScript.nodes output to json
  window.CoffeeCoffee.ast_to_json = (ast) ->
    if ast.expressions?
      wrap(ast.expressions)
    else
      [wrap_obj(ast)]

else
  fs = require 'fs'
  fn = process.argv[2]
  if fn
    data = fs.readFileSync(fn).toString()
    handle_data(data)
  else
    data = ''
    stdin = process.openStdin()
    stdin.on 'data', (buffer) ->
      data += buffer.toString() if buffer
    stdin.on 'end', ->
      handle_data(data)

