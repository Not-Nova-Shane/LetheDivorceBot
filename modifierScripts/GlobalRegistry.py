MODIFIER_HANDLERS = {}

def register_modifier(cls):
    if cls.name:
        MODIFIER_HANDLERS[cls.name] = cls()
    # print("Registered handlers:", list(MODIFIER_HANDLERS.keys()))
    return cls

class ModifierHandler:
    name = None  # subclasses set this

    async def apply(self, value, modifier_target, acquired_values, effect, log, roll_container, pagename, symbol, **kwargs):
        raise NotImplementedError
