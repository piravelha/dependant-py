from typing import Optional, overload, TypeAlias, Union
from abc import ABC, abstractmethod

Term: TypeAlias = Union[
  'Var',
  'TypeConstructor',
  'DependantType',
  'Nat',
  'Abstraction',
  'Application',
  'WildCard',
]

InferenceResult: TypeAlias = tuple['Substitution', Term] | str

class Inferrable(ABC):
    @abstractmethod
    def infer(self, context: 'Context') -> InferenceResult: ...

class TypeConstructor(Inferrable):
    def __init__(self, name: str, args: list[Term] = []) -> None:
        self.name = name
        self.args = args
    def infer(self, context: 'Context') -> InferenceResult:
        if not context.mapping.get(self.name):
          return "not found: " + self.name
        return Substitution(), context.mapping[self.name]
    def __repr__(self) -> str:
        if self.name == "->":
            l = str(self.args[0])
            r = str(self.args[1])
            if " " in l: l = f"({l})"
            if " " in r: r = f"({r})"
            return f"{l} -> {r}"
        args = "".join([f" {a}" for a in self.args])
        return f"{self.name}{args}"
    
class Nat(Inferrable):
    def __init__(self, value: int) -> None:
        self.value = value
    def infer(self, context: 'Context') -> InferenceResult:
        context = context
        return Substitution(), TypeConstructor("Nat")
    def __repr__(self) -> str:
        return f"{self.value}"

class Var(Inferrable):
    var_count = 0
    def __init__(self, name: Optional[str] = None) -> None:
        if not name:
            Var.var_count += 1
            name = f"t{Var.var_count}"
        self.name = name
    def infer(self, context: 'Context') -> InferenceResult:
        if self.name in context.mapping:
            return Substitution(), context.mapping[self.name]
        return f"Unbound variable: {self}"
    def __repr__(self) -> str:
        return self.name

class Abstraction(Inferrable):
    def __init__(self, param: str, type: Term, body: Term) -> None:
        self.param = param
        self.type = type
        self.body = body
    def infer(self, context: 'Context') -> InferenceResult:
        context = Context(context.mapping.copy())
        context.mapping[self.param] = self.type
        result = self.body.infer(context)
        if isinstance(result, str): return result
        s2, t1 = result
        return s2, TypeConstructor("->", [self.type, t1])
    def __repr__(self):
        return f"\\{self.param}: {self.type}. {self.body}"

class Application(Inferrable):
    def __init__(self, func: Term, arg: Term) -> None:
        self.func = func
        self.arg = arg
    def infer(self, context: 'Context') -> InferenceResult:
        result = self.func.infer(context)
        if isinstance(result, str): return result
        s1, t1 = result
        result = self.arg.infer(context)
        if isinstance(result, str): return result
        s2, t2 = result
        beta = Var()
        fn = TypeConstructor("->", [t2, beta])
        s3 = unify(t1, fn)
        if s3 is None:
            return f"Failed unification of function types: '{t1}' and '{fn}'"
        return s3(s2(s1)), s3(beta)
    def __repr__(self):
        f = str(self.func)
        a = str(self.arg)
        if " " in a:
          a = f"({a})"
        return f"{f} {a}"

class DependantType(Inferrable):
    def __init__(self, param: str, term: Term, body: Term) -> None:
        self.param = param
        self.term = term
        self.body = body
    def infer(self, context: 'Context') -> InferenceResult:
        context = Context(context.mapping.copy())
        result = self.term.infer(context)
        if isinstance(result, str): return result
        s1, t1 = result
        context.mapping[self.param] = t1
        result = self.body.infer(context)
        if isinstance(result, str): return result
        s2, t2 = result
        return s2(s1), DependantType(self.param, t1, t2)
    def __repr__(self):
        return f"|{self.param}: {self.term}. {self.body}"

class WildCard(Inferrable):
    def __init__(self):
        pass
    def infer(self, context: 'Context') -> InferenceResult:
        context = context
        return Substitution(), Var()
    def __repr__(self):
        return "?"

class Substitution:
    def __init__(self, mapping: dict[str, Term] = {}) -> None:
        self.mapping = mapping
    @overload
    def __call__(self, x: Term) -> Term: ...
    @overload
    def __call__(self, x: 'Substitution') -> 'Substitution': ...
    def __call__(self, x):
        if isinstance(x, Var):
            if x.name in self.mapping:
                return self.mapping[x.name]
            return x
        if isinstance(x, TypeConstructor):
            args = [self(a) for a in x.args]
            return TypeConstructor(x.name, args)
        if isinstance(x, DependantType):
            type = self(x.term)
            body = self(x.body)
            return DependantType(x.param, type, body)
        if isinstance(x, Nat):
            return x
        if isinstance(x, Application):
            return Application(self(x.func), self(x.arg))
        if isinstance(x, Substitution):
            s = self.mapping.copy()
            for k, v in x.mapping.items():
                s[k] = self(v)
            return Substitution(s)
    def __repr__(self) -> str:
        s = "S("
        for i, (k, v) in enumerate(self.mapping.items()):
            if i > 0:
                s += ", "
            s += f"{k} |-> {v}"
        return s + ")"

class Context:
    def __init__(self, mapping: dict[str, Term]) -> None:
        mapping["Nat"] = TypeConstructor("Type", [])
        mapping["true"] = TypeConstructor("Bool")
        mapping["false"] = TypeConstructor("Bool")
        mapping["Bool"] = TypeConstructor("Type")
        self.mapping = mapping
    def __repr__(self) -> str:
        s = "T("
        for i, (k, v) in enumerate(self.mapping.items()):
            if i > 0:
                s += ", "
            s += f"{k} |-> {v}"
        return s + ")"
    

def unify(t1: Term, t2: Term) -> Substitution | None:
    if isinstance(t2, WildCard) or isinstance(t1, WildCard):
        return Substitution()
    if isinstance(t1, Var) and isinstance(t2, Var) and t1.name == t2.name:
        return Substitution()
    if isinstance(t2, Var):
        return Substitution({t2.name: t1})
    if isinstance(t1, Var):
        return unify(t2, t1)
    if isinstance(t1, TypeConstructor) and isinstance(t2, TypeConstructor):
        if t1.name != t2.name: return None
        if len(t1.args) != len(t2.args): return None
        s = Substitution()
        for a1, a2 in zip(t1.args, t2.args):
            result = unify(a1, a2)
            if result is None: return None
            s = s(result)
        return s
    if isinstance(t1, DependantType) and isinstance(t2, DependantType):
        s = {}
        result = unify(t1.term, t2.term)
        if result is None: return None
        s |= result.mapping
        result = unify(t1.body, t2.body)
        if result is None: return None
        s |= result.mapping
        return Substitution(s)
    if isinstance(t1, Nat) and isinstance(t2, Nat):
        if t1.value != t2.value: return None
        return Substitution()
    if isinstance(t1, Abstraction) and isinstance(t2, Abstraction):        return unify(t1.body, t2.body)
    if isinstance(t1, Application) and isinstance(t2, Application):
        s = Substitution()
        result = unify(t1.func, t2.func)
        if result is None: return None
        s = result(s)
        result = unify(t1.arg, t2.arg)
        if result is None: return None
        s = result(s)
        return s

        
    return None
