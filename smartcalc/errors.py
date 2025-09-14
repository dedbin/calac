class SmartCalcError(Exception):
    pass

class LexError(SmartCalcError):
    pass

class ParseError(SmartCalcError):
    pass

class NameResolutionError(SmartCalcError):
    pass

class EvalError(SmartCalcError):
    pass