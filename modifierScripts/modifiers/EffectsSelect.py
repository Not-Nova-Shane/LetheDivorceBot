from modifierScripts.GlobalRegistry import *
from everythingexcepthim import resolve_value
from UnitProfileCode import ProfileData

@register_modifier
class EffectsSelectHandler(ModifierHandler):
    name = "effectselect"

    async def apply(self, value, modifier_target : ProfileData, acquired_values, effect, log, roll_container, pagename, symbol, **kwargs):
        selectblock = value
        effectslist = selectblock.get("effectLists", [])
        selector = resolve_value(selectblock.get("selector",0))

        selectedEffectsList = effectslist[selector]
        effects: list = kwargs["effects"]
        effects.extend(selectedEffectsList)