from lark import Lark, Transformer
from typecheck import *

with open("grammar.lark") as f:
    grammar = f.read()

parser = Lark(grammar)

class ToTerm(Transformer):
    def dependant_abstraction(self, args):
        return DependantAbstraction(*args)
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
        return TypeVar(args[0])
    def wildcard(self, args):
        return WildCard()
    def NAT(self, token):
        return Nat(int(token.value))
    def NAME(self, token):
        return token.value
    
code = r"""
(\x: 10. x) ten
"""

tree = parser.parse(code)
result = ToTerm().transform(tree).infer(Context({"ten": Nat(10)}))
if isinstance(result, str):
    print(f"ERROR: {result}")
else:
    substitution, type = result
    print(f"SUBSTITUTION: {substitution}")
    print(f"TYPE: {type}")