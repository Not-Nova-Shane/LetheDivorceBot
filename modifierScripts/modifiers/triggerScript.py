from modifierScripts.GlobalRegistry import *
from everythingexcepthim import process_effects, resolve_value
from UnitProfileCode import ProfileData

@register_modifier
class TriggerHandler(ModifierHandler):
    name = "trigger"

    async def apply(self, value, modifier_target : ProfileData, acquired_values, effect, log, roll_container, pagename, symbol, **kwargs):
        triggerBlock = value
        amount = resolve_value(triggerBlock.get("amount", 1), acquired_values)
        target = kwargs.get("target") or modifier_target

        for _ in range(amount):
            if log is not None and triggerBlock.get("message"):
                log.append(
                    triggerBlock.get("message").format(
                        stagger=symbol['stagger'],
                        target_name=modifier_target.name
                    )
                )
            await process_effects(target, modifier_target, kwargs["dice"], f"when_{triggerBlock.get("trigger")}",
                                  roll_container, kwargs["source_page"], kwargs["damage"], kwargs["stagger"],
                                  log, pageusetype=kwargs["pageusetype"], data=kwargs["data"], interaction=kwargs["interaction"])
            await process_effects(modifier_target, target, kwargs["dice"], f"on_{triggerBlock.get("trigger")}",
                                  roll_container, kwargs["source_page"], kwargs["damage"], kwargs["stagger"],
                                  log, pageusetype=kwargs["pageusetype"], data=kwargs["data"], interaction=kwargs["interaction"])