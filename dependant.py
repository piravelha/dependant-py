from lark import Lark, Transformer
from typing import Any
from typecheck import *

with open("grammar.lark") as f:
    grammar = f.read()

parser = Lark(grammar)

class GetDataDecls(Transformer):
  def __init__(self, context: Context):
    self.context = context
  def start(self, _):
    return self.context
  def data_decl(self, args):
    name, params, ret, constructors = args
    cons = self.context.mapping
    to_term = ToTerm()
    for con in constructors.children:
      con_name, con_type = con.children
      cons[con_name.value] = to_term.transform(con_type)
    this = to_term.transform(ret)
    for p in reversed(params.children):
      n, t = p.children
      this = DependantType(n.value, t, this)
    cons[name.value] = this
  def var_decl(self, args):
    name, type, _, value = args
    to_term = ToTerm()
    type = to_term.transform(type)
    value = to_term.transform(value)
    s, value = value.infer(self.context)
    cons = self.context.mapping
    s = s(unify(value, type))
    assert s
    cons[name.value] = s(type)

class ToTerm(Transformer):
    def application(self, args):
        return Application(*args)
    def abstraction(self, args):
        return Abstraction(*args)
    def var(self, args):
        return Var(args[0])
    def dependant_type(self, args):
        return DependantType(*args)
    def type_constructor(self, args):
        return TypeConstructor(args[0], args[1:])
    def type_func(self, args):
        return TypeConstructor("->", args)
    def type_var(self, args):
        return Var(args[0])
    def wildcard(self, _):
        return WildCard()
    def nat(self, args):
        return Nat(int(args[0].value))
    def NAME(self, token):
        return token.value
    def TYPE_NAME(self, token):
        return token.value
    
with open("demo.dep") as f:
    code = f.read()

tree = parser.parse(code)
context = GetDataDecls(Context({})).transform(tree)
tree: Any = tree.children[-1]
result = ToTerm().transform(tree).infer(context)
if isinstance(result, str):
    print(f"ERROR: {result}")
else:
    _, type = result
    print(f"TYPE: {type}")
