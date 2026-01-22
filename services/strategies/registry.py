# Phase IH: Strategy Registry

STRATEGIES = {}

def register(name):
    def deco(fn):
        STRATEGIES[name] = fn
        return fn
    return deco
