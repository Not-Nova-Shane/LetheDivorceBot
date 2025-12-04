# pyright: reportMissingImports=false
import random
import json
import re
import discord
import shutil
import os
import datetime
import copy
from discord import app_commands
from THECORE import (PAGE_PATH, PASSIVE_PATH, PROFILE_PATH, RES_PATH, INV_PATH, BUFF_PATH, GIFT_PATH,SHOP_PATH,PRESET_PATH,MD_PATH,BOX_PATH,SUPPORT_PATH, PASSHOP_PATH, ACTION_PATH, symbol, ProfileMan )
import asyncio
import math
from pathlib import Path
from UnitProfileCode import ProfileData
from modifierScripts.GlobalRegistry import MODIFIER_HANDLERS
async def send_split_embeds(interaction, base_embed: discord.Embed, fields: list, max_fields=25, max_chars=6000):
    # print(f"inside of thingie, you have {fields}")
    if not fields:
        await interaction.followup.send("No logs to show.")
        return
    processed_fields = []
    for name, value, inline in fields:
        if len(value) > 1024:
            while len(value) > 1024:
                split_index = value.rfind(", ", 0, 1024)
                if split_index == -1:
                    split_index = 1024
                chunk_value = value[:split_index]
                processed_fields.append((name, chunk_value, inline))
                name = f"{name} (cont.)"
                value = value[split_index + 2:] if split_index + 2 < len(value) else ""
            if value:
                processed_fields.append((name, value, inline))
        else:
            processed_fields.append((name, value, inline))
    chunks = []
    current_chunk = []
    current_char_count = len(base_embed.title or "") + len(base_embed.description or "")
    for name, value, inline in processed_fields:
        field_char_count = len(name) + len(value)
        if len(current_chunk) >= max_fields or current_char_count + field_char_count > max_chars:
            chunks.append(current_chunk)
            current_chunk = []
            current_char_count = len(base_embed.title or "") + len(base_embed.description or "")

        current_chunk.append((name, value, inline))
        current_char_count += field_char_count
    if current_chunk:
        chunks.append(current_chunk)
    for i, chunk in enumerate(chunks):
        embed = base_embed.copy()
        if len(chunks) > 1:
            embed.title = f"{base_embed.title} (Part {i + 1}/{len(chunks)})"
        for name, value, inline in chunk:
            embed.add_field(name=name, value=value, inline=inline)
        try:
            await interaction.followup.send(embed=embed)
            await asyncio.sleep(0.2)
        except discord.HTTPException as e:
            print(f"⚠ Failed to send embed chunk {i + 1}: {e}")
            continue

class TaggedData(dict):
    def __init__(self, data, source):
        super().__init__(data)
        self.source = source

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_json_from_folders(path):
    if os.path.isfile(path):
        return _tagged_load(path)

    data = {}
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            fpath = os.path.join(path, fname)
            chunk = _tagged_load(fpath)

            if isinstance(chunk, dict):
                for k, v in chunk.items():
                    data[k] = v
            elif isinstance(chunk, list):
                # tag each item individually
                if not isinstance(data, list):
                    data = []
                data.extend(chunk)
    return data

def _tagged_load(path):
    raw = load_json(path)
    if isinstance(raw, dict):
        return {k: TaggedData(v, path) for k, v in raw.items()}
    elif isinstance(raw, list):
        return [TaggedData(v, path) for v in raw]
    else:
        raise ValueError(f"Unsupported JSON structure in {path}")

def save_tagged_dict(data_dict, default_path):
    grouped = {}

    for key, entry in data_dict.items():
        src = getattr(entry, "source", default_path)
        if src not in grouped:
            grouped[src] = {}
        grouped[src][key] = dict(entry)  # strip wrapper back to plain dict

    for path, content in grouped.items():
        save_json(path, content)

def save_json(path, data):
    # base_dir = os.path.dirname(path)
    # file_name = os.path.basename(path)
    # backup_dir = os.path.join(base_dir, "backup")
    # os.makedirs(backup_dir, exist_ok=True)
    # for i in range(9, 0, -1):
    #     old = os.path.join(backup_dir, f"{file_name}.bak{i}")
    #     new = os.path.join(backup_dir, f"{file_name}.bak{i + 1}")
    #     if os.path.exists(old):
    #         os.rename(old, new)
    # bak10 = os.path.join(backup_dir, f"{file_name}.bak10")
    # if os.path.exists(bak10):
    #     os.remove(bak10)
    # if os.path.exists(path):
    #     bak1 = os.path.join(backup_dir, f"{file_name}.bak1")
    #     shutil.copy2(path, bak1)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def megaload():
    return {
        "pages": load_json_from_folders(PAGE_PATH),
        "buffs": load_json(BUFF_PATH),
        "passives": load_json(PASSIVE_PATH),
        "gifts": load_json(GIFT_PATH),
        "res": load_json(RES_PATH),
        "inventory": load_json(INV_PATH),
        "shop": load_json(SHOP_PATH),
        "presets": load_json(PRESET_PATH),
        "MD": load_json(MD_PATH),
        "StorageBox": load_json(BOX_PATH),
        "support": load_json(SUPPORT_PATH),
        "action": load_json(ACTION_PATH),
        "passhop": load_json(PASSHOP_PATH)
    }

def megasave(data):
    ProfileMan.save_profiles(PROFILE_PATH)
    # save_json(PAGE_PATH, data["pages"])
    save_tagged_dict(data["pages"], PAGE_PATH)
    save_json(BUFF_PATH, data["buffs"])
    save_json(PASSIVE_PATH, data["passives"])
    save_json(GIFT_PATH, data["gifts"])
    save_json(RES_PATH, data["res"])
    save_json(INV_PATH, data["inventory"])
    save_json(SHOP_PATH, data["shop"])
    save_json(PRESET_PATH, data["presets"])
    save_json(MD_PATH,data["MD"])
    save_json(BOX_PATH,data["StorageBox"])
    save_json(SUPPORT_PATH,data["support"])
    save_json(ACTION_PATH,data["action"])
    save_json(PASSHOP_PATH,data["passhop"])

BASE_PAGES = ["Focused Strikes", "Charge and Cover", "Light attack", "Light Defense", "Evade"]

# this is the unequip page code 
def UnequipPageCode(owner, page, data):
    inventory = data["inventory"]
    OwnerProfiles = ProfileMan.get_profile(owner)
    pages = data["pages"]

    # if page in inventory[owner].get("locked",[]):
    #     return False, "❌ That Page is locked to this profile"
    if page not in pages:
        return False, "❌ That page doesn't exist."

    if owner not in inventory or OwnerProfiles is None:
        return False, "❌ That profile doesn't exist."

    if page not in inventory[owner]["equipped"] and page not in BASE_PAGES:
        return False, "❌ The profile isn't equipping the page."

    if page not in BASE_PAGES:
        inventory[owner]["pages"].append(page)
        inventory[owner]["equipped"].remove(page)

    OwnerProfiles.remove_card(page)

    return True, f"{owner} has unequipped {page}!"

def UnequipPassiveCode(owner, passive, data):
    inventory = data["inventory"]
    OwnerProfiles = ProfileMan.get_profile(owner)
    passives = data["passives"]
    if passive not in passives:
        return False, "❌ That page doesn't exist."

    if owner not in inventory or OwnerProfiles is None:
        return False, "❌ That profile doesn't exist."

    if passive not in inventory[owner]["equippedpas"]:
        return False, "❌ The profile isn't equipping the passive."

    inventory[owner]["passives"].append(passive)
    inventory[owner]["equippedpas"].remove(passive)
    inventory[owner]["currentpascost"] -= passives[passive].get("cost", 10)
    OwnerProfiles.passives.remove(passive)

    return True, f"{owner} has unequipped {passive}!"

def get_rigged_roll(profile : ProfileData, min_val, max_val):
    rig_config = load_json("data/rig_config.json")
    if not rig_config.get("enabled"):
        return random.randint(min_val, max_val)

    force_rolls = rig_config.get("force_rolls", {})
    margins = rig_config.get("margins", {})

    name = profile.name
    faction = profile.PlayerOrEnemy

    # Get rig rule
    rule = force_rolls.get("profiles", {}).get(name, force_rolls.get(faction, "normal"))

    # Get margin set (profile > faction > empty)
    margin_set = margins.get(name, margins.get(faction, {}))

    if rule == "min":
        margin_list = margin_set.get("min", [])
        margin = random.choice(margin_list) if margin_list else 0
        return max(min_val, min(max_val, min_val + margin))

    elif rule == "max":
        margin_list = margin_set.get("max", [])
        margin = random.choice(margin_list) if margin_list else 0
        return max(min_val, min(max_val, max_val + margin))

    elif isinstance(rule, int):
        return max(min_val, min(max_val, rule))

    elif rule == "normal":
        # Use margin if available, random roll then tilt
        base_roll = random.randint(min_val, max_val)
        bias_pool = margin_set.get("normal") or margin_set.get("max") or margin_set.get("min") or []
        margin = random.choice(bias_pool) if bias_pool else 0
        return max(min_val, min(max_val, base_roll + margin))

    else:
        return random.randint(min_val, max_val)

def resolve_dynamic_target(target: str, condition_targets: list, all_profiles: list):
    match = re.match(r"(highest|lowest)_(\w+)", target)
    if not match:
        return []  # Not a dynamic stat target

    direction, stat = match.groups()

    # Filter condition_targets from all_profiles
    candidates = [p for p in all_profiles if p in condition_targets]

    if not candidates:
        return []

    if direction == "highest":
        return [max(candidates, key=lambda p: p.get(stat, float("-inf")))]
    else:
        return [min(candidates, key=lambda p: p.get(stat, float("inf")))]
def is_debtor_blocked(user_data):
    debt = user_data.get("debt", 0)
    due = user_data.get("loan_due")
    if debt > 0 and due:
        try:
            # hello chatgpt.
            return datetime.datetime.utcnow() > datetime.datetime.fromisoformat(due)
        except ValueError:
            return False
    return False

def globalpowerhandler(atk_page={} ,totaldeletion=False ,trigger="after_attack", deletebytrigger=False, data={}):
    if totaldeletion and (atk_page.get("globalpower") is not None and trigger != "newturn"):
        if trigger != "newturn":
            del atk_page["globalpower"]
            return
        else:
            for page in data["pages"]:
                if page.get("globalpower") is not None:
                    del page["globalpower"]
    if atk_page.get("globalpower") is None:
        return 0
    if deletebytrigger:
        removelist = []
        for globalpower in atk_page["globalpower"]:
            match trigger:
                case "after_attack":
                    if globalpower["trigger"] in ["on_use"]:
                        removelist.append(globalpower)
                
        for removed in removelist:
            atk_page["globalpower"].remove(removed)
    for dice in atk_page["dice"]:
        if dice.get("invoked",False) and not dice.get("perminvoked"):
            dice["invoked"] = False
    return sum(gp.get("value", 0) for gp in atk_page["globalpower"])

def get_speed_bonus(attackerProfile, targetProfile):
    # aspeed = attackerProfile.current_speed
    # tspeed = targetProfile.current_speed
    # return math.floor((aspeed-tspeed) / 3)
    return 0

async def handle_clash_win(
    attackerProfile : ProfileData, defenderProfile : ProfileData, a_die, d_die,
    a_base, d_base,
    a_roll, d_roll,
    attacker_page, defender_page, symbol, log,
    attacker_pageName,
    defender_pageName,
    a_is_evade_queue=None, d_is_evade_queue=None,
    pageusetype="",data={},dicelistcopy=[],interaction=None
):

    attacker_name = attackerProfile.name
    defender_name = defenderProfile.name

    print(f"a_roll BEFORE FEJIFJIJIEFJI JCGUARD IS {a_roll}")
    if d_die.get("type") == "guard":
        a_roll = max(0, a_roll - d_roll)

    print(f"a_roll AFTER GUARD IS {a_roll}")

    if a_die.get("type") not in ["evade"] or (a_die.get("type") in ["evade"] and d_die.get("type") not in ["slash","pierce", "blunt"]):
        log.append(f"{attacker_name} won the clash against {defender_name} — 🎲 {attacker_name}: [{a_base}] ➜ {a_roll} ({a_die['min']}-{a_die['max']}) vs 🎲 {defender_name}: [{d_base}] ➜ {d_roll} ({d_die['min']}-{d_die['max']})")
        print(f"[DEBUG] inside of handle_clash_win, interaction is {interaction}")
        await process_effects(attackerProfile, defenderProfile, a_die, "clash_win", [a_base], source_page=attacker_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy, interaction=interaction)
        await process_effects(defenderProfile, attackerProfile, d_die, "clash_lose", [d_base], source_page=defender_page, pagename=defender_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy, interaction=interaction)
    else:
        log.append(f"{attacker_name} Dodged {defender_name}'s attack — 🎲 {attacker_name}: [{a_base}] ➜ {a_roll} ({a_die['min']}-{a_die['max']}) vs 🎲 {defender_name}: [{d_base}] ➜ {d_roll} ({d_die['min']}-{d_die['max']})")
        attackerProfile.heal_stagger(a_roll)


    dmg = 0 if a_die.get("type") in ["evade", "guard"] else a_roll
    stagger = 0 if a_die.get("type") == "evade" else a_roll


    attackweight = attacker_page.get("attackweight", 1)
    indiscriminate = attacker_page.get("indiscriminate", False)
    attacker_faction = attackerProfile.PlayerOrEnemy

    main_target = defenderProfile
    extra_targets = get_extra_targets(main_target, attacker_faction, attackweight, indiscriminate)

    if d_die.get("type") == "evade":
        await process_effects(defenderProfile, attackerProfile, d_die, "on_failed_evade", [d_base], source_page=defender_page,
                              pagename=defender_pageName, log=log, pageusetype=pageusetype, data=data,
                              dicelistcopy=dicelistcopy, interaction=interaction)

    if a_die.get("type") not in ["evade", "guard"]:
        for hit_target in [main_target] + extra_targets:
            if not isinstance(hit_target, ProfileData):
                continue

            await CalculateOnHitEffects(attacker_page, attackerProfile, a_base, data, a_die, dicelistcopy,
                                        hit_target, interaction, log, attacker_pageName, pageusetype, a_roll)
    else:
        if a_die.get("type") == "evade":
            await process_effects(attackerProfile, defenderProfile, a_die, "on_evade", [a_base], source_page=attacker_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy, interaction=interaction)
            if a_is_evade_queue is not None and d_die.get("type") in ["blunt", "pierce", "slash"]:
                a_is_evade_queue.insert(0, a_die)
        elif a_die.get("type") == "guard":
            defenderProfile.take_st_damage(stagger)
            await applystatus(attackerProfile, defenderProfile, a_die, [a_base], [dmg], [stagger], attacker_page, log=log, pageusetype=pageusetype, data=data)
            await process_effects(attackerProfile, defenderProfile, a_die, "on_block", [a_base], source_page=attacker_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy)

def calculate_level_difference_Power(attackProfile: ProfileData, targetProfile: ProfileData, log):
    self_ol = attackProfile.offense_level() if callable(getattr(attackProfile, "offense_level", None)) else attackProfile.offense_level
    target_ol = targetProfile.offense_level() if callable(getattr(targetProfile, "offense_level", None)) else targetProfile.offense_level

    diff = self_ol - target_ol
    power_bonus = diff // 3 if diff >= 3 else 0

    if power_bonus and log is not None:
        log.append(
            f"{symbol['buff']} {attackProfile.name}'s roll gains +{power_bonus} power due to their level difference. {symbol['buff']}")

    return power_bonus

async def unopposedattack(attacker, dice, attackerProfile: ProfileData, targetProfile : ProfileData, attacker_Page, log, pageusetype, attacker_pageName, data={}, dicelistcopy=[], interaction=None):
    if dice.get("invokeable",False) and not dice.get("invoked",False):
        log.append(
            f"{attacker}'s {symbol['invokeable_'+dice.get('type','none')]} Invokeable {dice.get('type','none')} {symbol['invokeable_'+dice.get('type','none')]} is Uninvoked and does nothing"
        )                
        return True
    if attackerProfile.is_staggered:
        log.append(
            f"{attacker} is Staggered, Roll Cancelled, Does nothing"
        )                
        return True
    
    min_val = dice["min"]
    max_val = dice["max"]

    base_roll = min_val if min_val > max_val else get_rigged_roll(attackerProfile, min_val, max_val)

    pageusetype = "Unopposed"
    roll_val = [base_roll]

    await process_effects(attackerProfile, targetProfile, dice, "earliest_roll", roll_val, source_page=attacker_Page,
                          pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data,
                          dicelistcopy=dicelistcopy, interaction=interaction)

    roll_val[0] += calculate_level_difference_Power(attackerProfile, targetProfile, log)
    await process_effects(attackerProfile, targetProfile, dice, "before_on_roll", roll_val, source_page=attacker_Page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy, interaction=interaction)
    await process_effects(attackerProfile, targetProfile, dice, "on_roll", roll_val, source_page=attacker_Page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy, interaction=interaction)
    roll = max(0, roll_val[0] + globalpowerhandler(attacker_Page)) if "locked" not in roll_val else roll_val[0]

    if dice.get("type") in ["evade", "guard"]:
        log.append(f"{attacker}'s {symbol[dice.get('type','none')]}{dice.get('type','none')} is defensive and does nothing unopposed.")
        return True

    dmg = roll
    stagger = roll

    attackweight = attacker_Page.get("attackweight", 1)
    indiscriminate = attacker_Page.get("indiscriminate", False)
    attacker_faction = attackerProfile.PlayerOrEnemy

    all_targets = [targetProfile] + get_extra_targets(targetProfile, attacker_faction, attackweight, indiscriminate)
    if roll > 0:
        for hit_target in all_targets:
            if not isinstance(hit_target, ProfileData):
                continue

            await CalculateOnHitEffects(attacker_Page, attackerProfile, base_roll, data, dice, dicelistcopy, hit_target, interaction, log, attacker_pageName, pageusetype, roll)
    else:
        log.append(f"{attacker}'s dice rolled 0 or less, does not hit or trigger any effect")


async def CalculateOnHitEffects(attacker_Page, attackerProfile : ProfileData, base_roll, data, dice, dicelistcopy, hit_target : ProfileData, interaction, log, attacker_pageName, pageusetype, roll):
    dmgcont = [roll]
    staggercont = [roll]
    await process_effects(attackerProfile, hit_target, dice, "before_on_hit", [base_roll], source_page=attacker_Page,
                          pagename=attacker_pageName, damage=dmgcont, stagger=staggercont, log=log, pageusetype=pageusetype,
                          data=data, dicelistcopy=dicelistcopy, interaction=interaction)
    await process_effects(hit_target, attackerProfile, dice, "before_when_hit", [base_roll], damage=dmgcont,
                          stagger=staggercont, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy,
                          interaction=interaction)

    dmg = calculate_damage(dmgcont[0], hit_target, dice, attackerOffenseLevel=attackerProfile.offense_level, stagger=False)
    stagger = calculate_damage(staggercont[0], hit_target, dice, attackerOffenseLevel=attackerProfile.offense_level, stagger=True)

    hit_target.take_hp_damage(dmg)
    hit_target.take_st_damage(stagger)

    shown = {"roll": roll, "base_roll": base_roll, "dmg": dmg, "stagger": stagger, "min": dice['min'],
             "max": dice['max']}

    if dice.get("hidden", False):
        for name, value in shown.items():
            shown[name] = "???"
        print(shown)
        if not hasattr(hit_target, "temphidden"):
            hit_target.temphidden = []
        hidelist = hit_target.temphidden
        hidelist.append("hp")
        hidelist.append("stagger")

    dice_type = dice.get("type", "none")
    dice_symbol = symbol.get(dice_type, "")

    log.append(
        f"{attackerProfile.name} hits {hit_target.name} for "
        f"{dice_symbol}{shown['dmg']} HP damage and {dice_symbol}{shown['stagger']} Stagger damage "
        f"using a {dice_symbol}{dice_type} dice — 🎲 "
        f"{attackerProfile.name}: base roll [{shown['base_roll']}] ➜ {shown['roll']} ({shown['min']}-{shown['max']})"
    )
    await applystatus(attackerProfile, hit_target, dice, [base_roll], dmgcont, staggercont, attacker_Page, log=log,
                      pageusetype=pageusetype, data=data, interaction=interaction)
    dmgcont = [dmg]
    staggercont = [stagger]

    await process_effects(attackerProfile, hit_target, dice, "on_hit", [base_roll], source_page=attacker_Page, pagename=attacker_pageName,
                          damage=dmgcont, stagger=staggercont, log=log, pageusetype=pageusetype, data=data,
                          dicelistcopy=dicelistcopy, interaction=interaction)

    await process_effects(hit_target, attackerProfile, dice, "when_hit", [base_roll], damage=dmgcont,
                          stagger=staggercont, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopy,
                          interaction=interaction)


def handle_invokeables(a_die, d_die, attacker_name, defender_name, a_dice, d_dice, log):
    def check(die, owner):
        if die.get("invokeable", False) and not die.get("invoked", False):
            entry = (
                f"{owner}'s {symbol['invokeable_'+die.get('type','none')]} "
                f"Invokeable {die.get('type','none')} "
                f"{symbol['invokeable_'+die.get('type','none')]} is Uninvoked and does nothing"
            )
            return True, entry
        return False, None

    auninvoked, msg_a = check(a_die, attacker_name)
    if msg_a: log.append(msg_a)

    duninvoked, msg_d = check(d_die, defender_name)
    if msg_d: log.append(msg_d)

    # Handle cases
    if auninvoked and duninvoked:
        return True
    if auninvoked:
        d_dice.insert(0, d_die)
        return True
    if duninvoked:
        a_dice.insert(0, a_die)
        return True

    return False

def handle_staggered(a, d, attacker_name, defender_name, a_die, d_die, a_dice, d_dice, log):
    def check(entity : ProfileData, name):
        if entity.is_staggered:
            return True, f"{name} is Staggered, Roll Cancelled, Does nothing"
        return False, None

    astaggered, msg_a = check(a, attacker_name)
    if msg_a: log.append(msg_a)

    dstaggered, msg_d = check(d, defender_name)
    if msg_d: log.append(msg_d)

    if astaggered and dstaggered:
        return True
    if astaggered:
        d_dice.insert(0, d_die)
        return True
    if dstaggered:
        a_dice.insert(0, a_die)
        return True

    return False

async def mehandleclashingoooo(attacker_name, a_die, defender_name, d_die, d_dice, a_dice, attackerProfile : ProfileData, defenderProfile : ProfileData,
                               a_page, d_page, log,
                               pageusetype, a_evade_queue, d_evade_queue, attacker_pageName,
                               defender_pageName, data= {}, dicelistcopya= [], dicelistcopyd= [], interaction=None):
    if handle_invokeables(a_die, d_die, attacker_name, defender_name, a_dice, d_dice, log):
        return True

    if handle_staggered(attackerProfile, defenderProfile, attacker_name, defender_name, a_die, d_die, a_dice, d_dice, log):
        return True
    
    pageusetype = "Clash"
    min_val = a_die["min"]
    max_val = a_die["max"]
    a_base = min_val if min_val > max_val else get_rigged_roll(attackerProfile, min_val, max_val)

    min_val = d_die["min"]
    max_val = d_die["max"]
    d_base = min_val if min_val > max_val else get_rigged_roll(defenderProfile, min_val, max_val)

    a_roll_val = [a_base]
    d_roll_val = [d_base]

    await process_effects(attackerProfile, defenderProfile, a_die, "earliest_roll", a_roll_val, source_page=a_page,
                          pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data,
                          dicelistcopy=dicelistcopya, interaction=interaction)
    await process_effects(defenderProfile, attackerProfile, d_die, "earliest_roll", d_roll_val, source_page=d_page,
                          pagename=defender_pageName, log=log, pageusetype=pageusetype, data=data,
                          dicelistcopy=dicelistcopyd, interaction=interaction)

    attackerProfile.calc_total_defense_level()
    attackerProfile.calc_total_offense_level()
    defenderProfile.calc_total_defense_level()
    defenderProfile.calc_total_offense_level()

    a_roll_val[0] += calculate_level_difference_Power(attackerProfile, defenderProfile, log)
    d_roll_val[0] += calculate_level_difference_Power(defenderProfile, attackerProfile, log)

    await process_effects(attackerProfile, defenderProfile, a_die, "before_on_roll", a_roll_val, source_page=a_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopya, interaction=interaction)
    await process_effects(defenderProfile, attackerProfile, d_die, "before_on_roll", d_roll_val, source_page=d_page, pagename=defender_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopyd, interaction=interaction)
    await process_effects(attackerProfile, defenderProfile, a_die, "on_roll", a_roll_val, source_page=a_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopya, interaction=interaction)
    await process_effects(defenderProfile, attackerProfile, d_die, "on_roll", d_roll_val, source_page=d_page, pagename=defender_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopyd, interaction=interaction)

    a_roll = max(0, a_roll_val[0])
    d_roll = max(0, d_roll_val[0])

    if a_die.get("type") not in ["evade"] and "locked" not in a_roll_val:
        a_roll += globalpowerhandler(atk_page=a_page)
    else:
        a_roll += get_speed_bonus(attackerProfile, defenderProfile) + globalpowerhandler(atk_page=a_page)
    if d_die.get("type") not in ["evade"] and "locked" not in d_roll_val:
        d_roll +=  globalpowerhandler(atk_page=d_page)
    elif "locked" not in d_roll_val:
        d_roll += get_speed_bonus(defenderProfile, attackerProfile) + globalpowerhandler(atk_page=d_page)

    a_roll = int(a_roll)
    d_roll = int(d_roll)

    a_wins = a_roll > d_roll or (a_roll == d_roll and a_die.get("type") == "evade")
    d_wins = d_roll > a_roll or (d_roll == a_roll and d_die.get("type") == "evade")

    if a_wins and not d_wins:
        await handle_clash_win(attackerProfile, defenderProfile, a_die, d_die, a_base, d_base, a_roll, d_roll, a_page, d_page, symbol, log, attacker_pageName, defender_pageName, a_evade_queue, d_evade_queue, pageusetype, data=data, dicelistcopy=dicelistcopya, interaction=interaction)
    elif d_wins:
        print(f"[DEBUG] inside of mehandleclashingoooo, interaction is {interaction}")
        await handle_clash_win(defenderProfile, attackerProfile, d_die, a_die, d_base, a_base, d_roll, a_roll, d_page, a_page, symbol, log, attacker_pageName, defender_pageName, d_evade_queue, a_evade_queue, pageusetype, data=data, dicelistcopy=dicelistcopyd, interaction=interaction)
    else:
        log.append(f"{attacker_name}'s {symbol[a_die.get('type', 'none')]}{a_die.get('type', 'none')} ties with {defender_name}'s {symbol[d_die.get('type', 'none')]}{d_die.get('type', 'none')} → No effect. 🎲 {attacker_name}: [{a_base}] ➜ {a_roll} ({a_die['min']}-{a_die['max']}) vs 🎲 {defender_name}: [{d_base}] ➜ {d_roll} ({d_die['min']}-{d_die['max']})")
        await process_effects(attackerProfile, defenderProfile, a_die, "clash_tie", [a_base], source_page=a_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopyd, interaction=interaction)
        await process_effects(defenderProfile, attackerProfile, d_die, "clash_tie", [d_base], source_page=d_page, pagename=defender_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dicelistcopyd, interaction=interaction)

def resource(profile : ProfileData, page, data):
    resources = data["res"]
    faction = profile.PlayerOrEnemy
    
    dice_list = page.get("dice", [])
    if not dice_list:
        return 

    resource = dice_list[0].get("sin")
    if not resource or resource == "none":
        return 

    if resource in resources[faction]:
        resources[faction][resource] += 1

def calculate_OffenseDefenseLevel_mult(attackerOffenseLevel, defenderDefenseLevel):
    X = attackerOffenseLevel - defenderDefenseLevel
    finalMult = X / (abs(X) + 25)
    return finalMult

def calculate_damage(roll, defender : ProfileData, dice, attackerOffenseLevel, stagger=False, damageTypeOverwrite=None):
    if dice is None:
        dice_type = "blunt"

    if damageTypeOverwrite is not None:
        dice_type = damageTypeOverwrite
    else:
        dice_type = dice.get("type", "blunt")

    if dice is None:
        dice_sin = "Wrath"
    else:
        dice_sin = dice.get("sin", "Wrath")

    phys_resist = defender.stagger_resistances.get(dice_type, 1.0) if stagger else defender.resistances.get(dice_type, 1.0)
    sin_resist = defender.sin_resistances.get(dice_sin, 1.0)

    if defender.resistances != defender.original_resistances and not defender.is_staggered:
        defender.resistances = defender.original_resistances

    if (defender.sin_resistances != defender.original_sin_resistances):
        defender.sin_resistances = defender.original_sin_resistances
    
    def calculate_mults(x):
        if x < 0:
            return -0.5
        elif 0 <= x < 1:
            return (x - 1) / 2
        else: 
            return x - 1

    physical_mult = calculate_mults(phys_resist)
    sin_mult = calculate_mults(sin_resist)
    OL_DL_advantage = calculate_OffenseDefenseLevel_mult(attackerOffenseLevel, defender.defense_level)
    total_mult = 1 + physical_mult + sin_mult + OL_DL_advantage

    return max(0, int(roll * total_mult))


async def autocomplete_page_names(interaction: discord.Interaction, current: str):
    current = current.lower()
    data = megaload()
    pages = data["pages"]
    return [
        app_commands.Choice(name=page_name, value=page_name)
        for page_name in pages
        if current in page_name.lower()
    ][:25]

async def autocomplete_profile_names(interaction: discord.Interaction, current: str):
    profiles : dict = ProfileMan.get_all_active_profiles()
    current = current.lower()
    return [
        app_commands.Choice(name=profile_name, value=profile_name)
        for profile_name, profileData in profiles.items()
        if current in profile_name.lower()
    ][:25]

def get_extra_targets(main_target: ProfileData, attacker_faction, attackweight=1, indiscriminate=False):
    if attackweight <= 1:
        return []

    potential_targets = []
    for profileName, profile in ProfileMan.get_all_active_profiles().items():
        if profileName == main_target.name:
            continue

        if not indiscriminate and not profile.is_enemy_of(attacker_faction):
                continue
        potential_targets.append(profile)

    random.shuffle(potential_targets)
    return potential_targets[:attackweight - 1]

async def applystatus(attacker, target, atkdie, atkbase, atkdmg, atkstagger, atkpage, log, pageusetype="Clash", data={}, effect={}, interaction=None):
    data, effect = data or {}, effect or {}
    name = getattr(target, "name", "Unknown")

    async def trigger_effects(source, target, *triggers):
        for trig in triggers:
            await process_effects(
                source, target, atkdie, trig, atkbase, atkpage,
                damage=atkdmg, stagger=atkstagger, log=log,
                pageusetype=pageusetype, data=data, interaction=interaction
            )

    # --- Stagger ---
    if not target.is_staggered and target.current_stagger <= 0:
        log.append(f"{symbol['stagger']} {name} Has been Staggered! {symbol['stagger']}")
        target.is_staggered = True
        target.staggeredThisTurn = True
        target.resistances = {k: 2.0 for k in target.resistances}
        attacker.heal_light(1)
        if log is not None:
            log.append(
                f"{symbol['light']} {attacker.name} recovers 1 light. {symbol['light']}")
        await trigger_effects(attacker, target, "on_stagger")
        await trigger_effects(target, attacker, "when_stagger")

    elif target.is_staggered and target.current_stagger > 0:
        log.append(f"{symbol['stagger']} {name} Has been Unstaggered! {symbol['stagger']}")
        target.is_staggered = False
        target.staggeredThisTurn = False
        target.resistances = target.original_resistances

    # --- Death ---
    if target.current_hp <= 0 and target.is_active:
        target.is_active = False
        log.append(f"{symbol['stagger']} {name} Has been Killed! {symbol['stagger']}")
        attacker.heal_light(1)
        if log is not None:
            log.append(
                f"{symbol['light']} {attacker.name} recovers 1 light. {symbol['light']}")
        await trigger_effects(attacker, target, "on_kill")
        await trigger_effects(target, attacker, "on_death")

    # --- Revive ---
    elif target.current_hp > 0 and not target.is_active:
        target.is_active = True
        log.append(f"{symbol['stagger']} {name} Has been Revived! {symbol['stagger']}")
        await trigger_effects(attacker, target, "on_unkill")
        await trigger_effects(target, attacker, "on_revive")

async def page_is_valid(interaction, attackerProfile, pageName):
        if not attackerProfile.spend_light(pageName):
            return True

        if not attackerProfile.spend_page(pageName):
            return True

        return False

async def attackhandler(interaction: discord.Interaction, attacker: str, target: str, attacker_pageName: str, data: dict):
        pages = data["pages"]
        attackerProfile = ProfileMan.get_profile(attacker)
        targetProfile = ProfileMan.get_profile(target)
        attacker_page = pages.get(attacker_pageName)
        pageusetype = "Unopposed"

        if not all([attackerProfile, targetProfile, attacker_page]):
            await interaction.followup.send("Invalid input.")
            return
        
        if await page_is_valid(interaction, attackerProfile, attacker_pageName):
            attacker_pageName = "Empty Page"
            attacker_page = pages.get(attacker_pageName)

        log = []

        await CheckSingleUsePage(attackerProfile, attacker_page)

        dice_copy = copy.deepcopy(attacker_page["dice"])
        await process_effects(attackerProfile, targetProfile, None, "on_use", source_page=attacker_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, dicelistcopy=dice_copy, interaction=interaction)
        resource(attackerProfile,attacker_page,data)

        for dice in dice_copy:
            await unopposedattack(attacker, dice, attackerProfile, targetProfile, attacker_page, log, pageusetype,
                                  attacker_pageName=attacker_pageName, data=data, dicelistcopy=dice_copy, interaction=interaction)
            if dice.get("reuse",0) > 0:
                while dice["reuse"] > 0:
                    dice["reuse"] -= 1
                    await unopposedattack(attacker, dice, attackerProfile, targetProfile, attacker_page, log, pageusetype,
                                          attacker_pageName=attacker_pageName, data=data, dicelistcopy=dice_copy, interaction=interaction)

        await process_effects(attackerProfile, targetProfile, None, "after_attack", source_page=attacker_page, pagename=attacker_pageName, log=log, pageusetype=pageusetype, data=data, interaction=interaction)
        globalpowerhandler(atk_page=attacker_page,trigger="after_attack",deletebytrigger=True,data=data)

        attacker_page["attackweight"] = attacker_page.get("originalattackweight", 1)
        fields = []
        embed = discord.Embed(
            title=f"⚔️ {attacker} attacks {target} using {attacker_pageName}!",
            description="Combat breakdown:",
            color=discord.Color.red()
        )
        for entry in log:
            if len(entry) > 1024:
                entry = entry[:1021] + "..."
            fields.append(("•", entry,False))
        print(f"INSIDE OF ATTACKHANDLER: WE HAVE INTERACTION: {interaction}, EMBED: {embed}, FIELDS: {fields}")
        await send_split_embeds(interaction, embed, fields)

async def clashhandler(interaction, data, attacker_name, attacker_pageName, defender_name, defender_pageName):
    pages = data["pages"]

    attackerProfile = ProfileMan.get_profile(attacker_name)
    defenderProfile = ProfileMan.get_profile(defender_name)
    attacker_page = pages.get(attacker_pageName)
    defender_page = pages.get(defender_pageName)
    pageusetype = "Clash"

    if not all([attackerProfile, defenderProfile, attacker_page, defender_page]):
        await interaction.followup.send("Invalid input.")
        return

    # this condition passing means that our page is not valid. we either don't have it in hand, or we don't have enough light.
    if await page_is_valid(interaction, attackerProfile, attacker_pageName):
        attacker_pageName = "Empty Page"
        attacker_page = pages.get(attacker_pageName)

    if await page_is_valid(interaction, defenderProfile, defender_pageName):
        defender_pageName = "Empty Page"
        defender_page = pages.get(defender_pageName)

    log = []

    await CheckSingleUsePage(attackerProfile, attacker_page)
    await CheckSingleUsePage(defenderProfile, defender_page)

    a_dice_copy = copy.deepcopy(attacker_page["dice"])  # Full, unpopped list
    a_dice = a_dice_copy.copy()        # Shallow copy for popping, same objects
    d_dice_copy = copy.deepcopy(defender_page["dice"])  # Full, unpopped list
    d_dice = d_dice_copy.copy()        # Shallow copy for popping, same objects
    await process_effects(attackerProfile, defenderProfile, None, "on_use", source_page=attacker_page,pagename=attacker_pageName, log=log,pageusetype=pageusetype,data=data,dicelistcopy=a_dice_copy,interaction=interaction)
    await process_effects(defenderProfile, attackerProfile, None, "on_use", source_page=defender_page,pagename=defender_pageName, log=log,pageusetype=pageusetype,data=data,dicelistcopy=d_dice_copy,interaction=interaction)
    resource(attackerProfile,attacker_page,data)
    resource(defenderProfile,defender_page,data)
    
    a_evade_queue = []
    d_evade_queue = []


    def pop_with_origin(evade_queue, dice_queue):
        if evade_queue:
            return evade_queue.pop(0), evade_queue
        if dice_queue:
            return dice_queue.pop(0), dice_queue
        return None, None

    while a_dice or d_dice or a_evade_queue or d_evade_queue:
        a_die, a_origin = pop_with_origin(a_evade_queue, a_dice)
        d_die, d_origin = pop_with_origin(d_evade_queue, d_dice)

        if a_die and d_die:
            print(f"[DEBUG] inside of clashhandler, interaction is {interaction}")
            await mehandleclashingoooo(attacker_name, a_die, defender_name, d_die, d_dice, a_dice, attackerProfile, defenderProfile, attacker_page, defender_page, log, pageusetype, a_evade_queue, d_evade_queue, attacker_page, defender_page, data=data, dicelistcopya=a_dice_copy, dicelistcopyd=d_dice_copy, interaction=interaction)
            if a_die.get("reuse", 0) > 0 and a_origin is not None:
                while a_die["reuse"] > 0:
                    a_die["reuse"] -= 1
                    a_origin.insert(0, a_die)
                    log.append(f"Dice from {attacker_name}'s {attacker_pageName} reuses and will clash next.")
            if d_die.get("reuse", 0) > 0 and d_origin is not None:
                while d_die["reuse"] > 0:
                    d_die["reuse"] -= 1
                    d_origin.insert(0, d_die)
                    log.append(f"Dice from {defender_name}'s {defender_pageName} reuses and will clash next.")
        elif a_die:
            await unopposedattack(attacker_name, a_die, attackerProfile, defenderProfile, attacker_page, log, "attack", attacker_pageName, data=data, dicelistcopy=a_dice_copy)
            if a_die.get("reuse",0) > 0:
                while a_die["reuse"] > 0:
                    a_die["reuse"] -= 1
                    await unopposedattack(attacker_name, a_die, attackerProfile, defenderProfile, attacker_page, log, "attack", attacker_pageName, data=data, dicelistcopy=a_dice_copy)
        elif d_die:
            await unopposedattack(defender_name, d_die, defenderProfile, attackerProfile, defender_page, log, "attack", defender_pageName, data=data, dicelistcopy=d_dice_copy)
            if d_die.get("reuse",0) > 0:
                while d_die["reuse"] > 0:
                    d_die["reuse"] -= 1
                    await unopposedattack(defender_name, d_die, defenderProfile, attackerProfile, defender_page, log, "attack", attacker_pageName, data=data, dicelistcopy=d_dice_copy)

    
    await process_effects(attackerProfile, defenderProfile, None, "after_attack", source_page=attacker_page,pagename=attacker_pageName, log=log,pageusetype=pageusetype,data=data,interaction=interaction)
    await process_effects(defenderProfile, attackerProfile, None, "after_attack", source_page=defender_page,pagename=defender_pageName, log=log,pageusetype=pageusetype,data=data,interaction=interaction)
    globalpowerhandler(atk_page=attacker_page,trigger="after_attack",deletebytrigger=True,data=data)
    globalpowerhandler(atk_page=defender_page,trigger="after_attack",deletebytrigger=True,data=data)

    fields = []
    embed = discord.Embed(
        title=f"⚔️ {attacker_name} clashes with {attacker_pageName}!",
        description=f"{attacker_name} uses {attacker_pageName} | {defender_name} uses {defender_pageName}",
        color=discord.Color.orange()
    )
    for entry in log:
        if len(entry) > 1024:
            entry = entry[:1021] + "..."
        fields.append(("•", entry, False))

    # print(f"INSIDE OF CLASHHANDLER: WE HAVE INTERACTION: {interaction}, EMBED: {embed}, FIELDS: {fields}")
    await send_split_embeds(interaction, embed, fields)


async def CheckSingleUsePage(unit_Profile : ProfileData, unit_Page):
    if unit_Page.get("single", False):
        unit_Profile.used = []
        unit_Profile.used.append(unit_Page.get("name", "nameNotFound"))

def CalcConditions(profile: ProfileData, page, effect, pages, source_page, source, dice, pageusetype, resources, modifier_target,condition_target,target, data):
            condition_blocks = effect.get("condition", [])
            if not isinstance(condition_blocks, list):
                condition_blocks = [condition_blocks]

            page_name = next((k for k, v in pages.items() if v is source_page), None)
            source_factions = source.faction

            if not isinstance(profile, ProfileData):
                return True

            if isinstance(profile, ProfileData):
                target_factions = profile.faction
            else:
                target_factions = []
            handcount = 0
            deckcount = 0
            notsingleton = True

            if profile is not None:
                for page in profile.hand:
                    handcount += profile.hand[page]["amount"]
                for page in profile.deck:
                    deckcount += profile.deck[page]["amount"]
                    if profile.deck[page]["amount"] > 1:
                        notsingleton = False

            def getCrumblingArmorEqualityCheckTrue(profile: ProfileData, data: dict) -> bool:
                storage_box = data.setdefault("StorageBox", {})
                damage_dict = storage_box.get("CrumblingArmorHighestDamageCalc", {})
                already_got_dict = storage_box.setdefault("CrumblingArmorAlreadyGotDaredevil", {})

                if not damage_dict:
                    return True

                sorted_units = sorted(damage_dict.items(), key=lambda x: x[1], reverse=True)

                selected_unit = None

                for name, _ in sorted_units:
                    if name not in already_got_dict:
                        selected_unit = name
                        break

                # Everyone already got it — reset and pick top again
                if not selected_unit:
                    already_got_dict.clear()
                    selected_unit = sorted_units[0][0]

                # Update tracking dict
                already_got_dict.clear()
                already_got_dict[selected_unit] = True

                # Return False ONLY for the top unit
                return profile.name != selected_unit  # <-- fixed: False for highest damage dealer

            def getCrumblingArmorEqualityCheckFalse(profile: ProfileData, data: dict) -> bool:
                storage_box = data.setdefault("StorageBox", {})
                damage_dict = storage_box.get("CrumblingArmorHighestDamageCalc", {})

                if not damage_dict:
                    return True

                top_unit = max(damage_dict, key=damage_dict.get)

                return profile.name == top_unit

            def getCrumblingArmorShit(profile: ProfileData, data: dict, equality_check: bool = True) -> bool:
                if equality_check:
                    return getCrumblingArmorEqualityCheckTrue(profile, data)
                else:
                    return getCrumblingArmorEqualityCheckFalse(profile, data)

            checks = {
                # --- Stat-based checks ---

                "crumblingArmorCondBelongs": lambda cond: getCrumblingArmorShit(profile, data,True),
                "crumblingArmorCondNotBelongs": lambda cond: getCrumblingArmorShit(profile, data,False),

                "HasMoreOLThanCondTarget": lambda cond: source.offense_level < profile.offense_level,

                "hp_min": lambda cond: profile.current_hp < cond["hp_min"],
                "hp_max": lambda cond: profile.current_hp > cond["hp_max"],

                "hp_min%": lambda cond: profile.current_hp * 100 / (profile._max_hp or 1) < cond["hp_min%"],
                "hp_max%": lambda cond: profile.current_hp * 100 / (profile._max_hp or 1) > cond["hp_max%"],

                "stagger_min": lambda cond: profile.current_stagger < cond["stagger_min"],
                "stagger_max": lambda cond: profile.current_stagger > cond["stagger_max"],

                "stagger_min%": lambda cond: profile.current_stagger * 100 / (profile._max_stagger or 1) < cond["stagger_min%"],
                "stagger_max%": lambda cond: profile.current_stagger * 100 / (profile._max_stagger or 1) > cond["stagger_max%"],

                "speed_min": lambda cond: profile.current_speed < cond["speed_min"],
                "speed_max": lambda cond: profile.current_speed > cond["speed_max"],

                "faster": lambda cond: profile.current_speed > source.current_speed,
                "faster_by": lambda cond: (profile.current_speed - cond["faster_by"]) > source.current_speed,

                "slower": lambda cond: profile.current_speed < source.current_speed,
                "slower_by": lambda cond: (profile.current_speed - cond["slower_by"]) < source.current_speed,

                "light_min": lambda cond: profile.current_light < cond["light_min"],
                "light_max": lambda cond: profile.current_light > cond["light_max"],

                "lightcost_min": lambda cond: profile.deck[page_name]["cost"] < cond["lightcost_min"],
                "lightcost_max": lambda cond: profile.deck[page_name]["cost"] > cond["lightcost_max"],

                # --- Page / passive / misc checks ---
                "pagecheck": lambda cond: page_name != cond["pagecheck"],
                "pagechecklist": lambda cond: page_name not in cond["pagechecklist"],
                "hand_min": lambda cond: handcount < cond["hand_min"],
                "hand_max": lambda cond: handcount > cond["hand_max"],
                "hand_check": lambda cond: cond["hand_check"] not in profile.hand,
                "passivecheck": lambda cond: cond["passivecheck"] not in profile.passives,
                "antipassivecheck": lambda cond: cond["antipassivecheck"] in profile.passives,
                "dice_type": lambda cond: dice and dice.get("type") not in cond["dice_type"],
                "dice_sin": lambda cond: dice and dice.get("sin") not in cond["dice_sin"],
                "pageusetype": lambda cond: pageusetype not in cond["pageusetype"],
                "hasStatus": lambda cond: cond["hasStatus"] not in page["pageTagList"],
                "notHasStatus": lambda cond: cond["notHasStatus"] in page["pageTagList"],
                "isDeploymentOrder": lambda cond: profile.deploymentOrder not in cond["isDeploymentOrder"],

                "dicecount_min": lambda cond: sum(
                    1 for d in page["dice"]
                    if cond["dicecount_min"]["dice_type"] == "all"
                    or (
                            isinstance(cond["dicecount_min"]["dice_type"], str)
                            and d["type"] == cond["dicecount_min"]["dice_type"]
                    )
                    or (
                            isinstance(cond["dicecount_min"]["dice_type"], list)
                            and d["type"] in cond["dicecount_min"]["dice_type"]
                    )
                ) < cond["dicecount_min"]["value"],

                "dicecount_max": lambda cond: sum(
                    1 for d in page["dice"]
                    if cond["dicecount_max"]["dice_type"] == "all"
                    or (
                            isinstance(cond["dicecount_max"]["dice_type"], str)
                            and d["type"] == cond["dicecount_max"]["dice_type"]
                    )
                    or (
                            isinstance(cond["dicecount_max"]["dice_type"], list)
                            and d["type"] in cond["dicecount_max"]["dice_type"]
                    )
                ) > cond["dicecount_max"]["value"],

                # --- Faction checks ---
                "factioncheck": lambda cond: not any(
                    (req == "Player" and any(f in source_factions for f in target_factions)) or
                    (req == "Enemy" and not any(f in source_factions for f in target_factions)) or
                    (req in target_factions)
                    for req in cond["factioncheck"]
                ),
                "absolutefactioncheck": lambda cond: not any(
                    f in target_factions for f in cond["absolutefactioncheck"]),

                # --- Chance ---
                "chance": lambda cond: random.uniform(1, 100) <= cond["chance"],

                # --- Buff / stack / count / total / surge checks ---
                "stack_min": lambda cond: profile.buffs.get(cond["stack_min"]["buff"], {}).get("stack", 0) <
                                          cond["stack_min"]["value"],
                "stack_max": lambda cond: profile.buffs.get(cond["stack_max"]["buff"], {}).get("stack", 0) >
                                          cond["stack_max"]["value"],

                "count_min": lambda cond: profile.buffs.get(cond["count_min"]["buff"], {}).get("count", 0) <
                                          cond["count_min"]["value"],
                "count_max": lambda cond: profile.buffs.get(cond["count_max"]["buff"], {}).get("count", 0) >
                                          cond["count_max"]["value"],

                "total_min": lambda cond: (
                                                  profile.buffs.get(cond["total_min"]["buff"], {}).get("stack", 0) +
                                                  profile.buffs.get(cond["total_min"]["buff"], {}).get("count", 0)
                                          ) < cond["total_min"]["value"],

                "total_max": lambda cond: (
                                                  profile.buffs.get(cond["total_max"]["buff"], {}).get("stack", 0) +
                                                  profile.buffs.get(cond["total_max"]["buff"], {}).get("count", 0)
                                          ) > cond["total_max"]["value"],

                "surge_min": lambda cond: (
                                                  profile.buffs.get(cond["surge_min"]["buff"], {}).get("stack", 0) *
                                                  profile.buffs.get(cond["surge_min"]["buff"], {}).get("count", 0)
                                          ) < cond["surge_min"]["value"],

                "surge_max": lambda cond: (
                                                  profile.buffs.get(cond["surge_max"]["buff"], {}).get("stack", 0) *
                                                  profile.buffs.get(cond["surge_max"]["buff"], {}).get("count", 0)
                                          ) > cond["surge_max"]["value"],

                # --- Staggered / singleton checks ---
                "ifstaggered": lambda cond: profile.is_staggered is not cond["ifstaggered"],
                "singleton": lambda cond: notsingleton or deckcount != 9,

                "resist_min": lambda cond: getattr(profile, cond["resist_min"]["restype"])[cond["resist_min"]["res"]] <
                               cond["resist_min"]["value"],
                "resist_max": lambda cond: getattr(profile, cond["resist_max"]["restype"])[cond["resist_max"]["res"]] >
                               cond["resist_max"]["value"],

                "buffamount_min": lambda cond: (
                        len([
                            buff for buff in profile.buffs
                            if cond["buffamount_min"]["type"] == "all" or data["buffs"][buff].get("type") ==
                               cond["buffamount_min"]["type"]
                        ]) < cond["buffamount_min"]["value"]
                ),

                "buffamount_max": lambda cond: (
                        len([
                            buff for buff in profile.buffs
                            if cond["buffamount_max"]["type"] == "all" or data["buffs"][buff].get("type") ==
                               cond["buffamount_max"]["type"]
                        ]) > cond["buffamount_max"]["value"]
                ),

                "resonance_min": lambda cond: (
                        resources[
                            "ResPlayer"
                            if cond["resonance_min"].get("absolute", False)
                            else (
                                "ResPlayer"
                                if (cond["resonance_min"].get("faction", "Player") == "Player") ==
                                   ("Player" in source.faction)
                                else "ResEnemy"
                            )
                        ][cond["resonance_min"]["sin"]] < cond["resonance_min"]["value"]
                ),

                "resource_min": lambda cond: (
                        resources[
                            ("Player" if cond["resource_min"].get("absolute", False)
                             else ("Player" if ("Player" if cond["resource_min"].get("faction",
                                                                                     "Player") == "Player" else "Enemy")
                                               == ("Player" if "Player" in source.faction else "Enemy")
                                   else "Enemy"))
                        ][cond["resource_min"]["sin"]] < cond["resource_min"]["value"]
                ),

                "resource_max": lambda cond: (
                        resources[
                            ("Player" if cond["resource_max"].get("absolute", False)
                             else ("Player" if ("Player" if cond["resource_max"].get("faction",
                                                                                     "Player") == "Player" else "Enemy")
                                               == ("Player" if "Player" in modifier_target.get("faction",
                                                                                               []) else "Enemy")
                                   else "Enemy"))
                        ][cond["resource_max"]["sin"]] > cond["resource_max"]["value"]
                ),

                "storagebox_check": lambda cond: any(
                    (
                            (("min" in entry) and (data.get("StorageBox", {}).get(
                                {"modifier_target": getattr(modifier_target, "name", None),
                                 "condition_target": getattr(condition_target, "name", None),
                                 "self": source.name,
                                 "target": getattr(target, "name", None)
                                }.get(entry["name"], entry["name"]),
                                {}
                            ).get(entry["valuename"], 0) < entry["min"]))
                            or
                            (("max" in entry) and (data.get("StorageBox", {}).get(
                                {
                                    "modifier_target": getattr(modifier_target, "name", None),
                                    "condition_target": getattr(condition_target, "name", None),
                                    "self": source.name,
                                    "target": getattr(target, "name", None)
                                }.get(entry["name"], entry["name"]),
                                {}
                            ).get(entry["valuename"], 0) > entry["max"]))
                            or
                            (("equal" in entry) and (data.get("StorageBox", {}).get(
                                {"modifier_target": getattr(modifier_target, "name", None),
                                 "condition_target": getattr(condition_target, "name", None),
                                 "self": source.name,
                                 "target": getattr(target, "name", None)
                                }.get(entry["name"], entry["name"]),
                                {}
                            ).get(entry["valuename"], 0) != entry["equal"]))
                    )
                    for entry in cond["storagebox_check"]
                ),
            }

            failed = next(((cond, key) for cond in condition_blocks for key, check in checks.items() if
                           key in cond and check(cond)), None)

            if failed:
                cond, key = failed
                print(f"[CalcConditions] Failed check → condition: {cond}, key: {key}, source.name: {source.name}, profile.name: {profile.name}")

            if any(check(cond) for cond in condition_blocks for key, check in checks.items() if key in cond):
                return False

            return True

def resolve_value(val, acquired_values, default=1):
    result = None  # ensure it's always defined
    if isinstance(val, str):
        result = acquired_values.get(val)
    elif isinstance(val, (int, float)):
        result = val
    result = int(result) if result is float else result
    return result if result is not None else default

async def process_effects(source : ProfileData, target : ProfileData, dice, trigger, roll_container=None,
                          source_page=None, pagename=None,damage=None, stagger=None,
                          log=None, pageusetype="Clash",data={},dicelistcopy=[],interaction=None):
    if log is None:
        log = []

    passives = data["passives"]
    buffs = data["buffs"]
    gifts = data["gifts"]
    pages = data["pages"]
    resources = data["res"]
    effects = []

    print(f"we now trigger an effect with the trigger: {trigger}")
    
    for egogift in gifts.values():
        if not egogift.get("acquired"):
            continue

        level = str(egogift.get("level", 1))
        for fallback_level in [level, "2", "1"]:
            effects_block = egogift.get(fallback_level, {})
            if effects_block.get("effects"):
                break
        else:
            print(f"No effects found for gift {egogift}")
            effects_block = {}

        effects.extend(effects_block.get("effects", []))

    for passive_name in source.passives:
        passive_data = passives.get(passive_name, {})
        effects.extend(passive_data.get("effects", []))

    for buff_name, buff_data in source.buffs.items():
        buff_def = buffs.get(buff_name)
        if buff_def:
            for eff in buff_def.get("effects", []):
                eff = eff.copy()
                eff["_buff_name"] = buff_name
                effects.append(eff)

    if isinstance(source_page, dict):
        effects.extend(source_page.get("effects", []))
    elif isinstance(source_page, list):
        for sourcepage in source_page:
            if isinstance(sourcepage, dict):
                effects.extend(sourcepage.get("effects", []))

    if dice and isinstance(dice, dict):
        effects.extend(dice.get("effects", []))

    # print(f"hoo boys, long one: {effects}\n\n")


    common_kwargs = {
        "source": source,
        "target": target,
        "dice": dice,
        "source_page": source_page,
        "pageusetype": pageusetype,
        "data": data,
        "gifts": gifts,
        "buffs": buffs,
        "pages": pages,
        "dicelistcopy": dicelistcopy,
        "interaction": interaction,
        "damage": damage,
        "stagger": stagger,
        "trigger": trigger,
        "effects": effects
    }

    def evaluate_cond(profile : ProfileData, page):
            if CalcConditions(profile, page, effect, pages, source_page, source, dice, pageusetype, resources, modifier_target,condition_target,target, data):
                print("[DEBUG] CALC COND RETURNED TRUE; EVALUATE COND RETURNED TRUE")
                return True
            else:
                print("[DEBUG] CALC COND RETURNED FALSE; EVALUATE COND RETURNED FALSE")
                return False


    async def handle_everyone_logic(effect, source : ProfileData, target : ProfileData, log, roll_container, acquired_values):
        condition_target_key = effect.get("conditionTarget", "self")
        modifier_target_key = effect.get("modifierTarget", "self")
        condition = effect.get("condition", {})
        modifiers = effect.get("modifiers", {})
        OG_all_profiles = ProfileMan.get_all_active_profiles()
        all_profiles = {}

        if effect.get("filterfaction"):
            right_faction = source.PlayerOrEnemy
            requested = set(effect["filterfaction"])
            if "AlliesOnly" in requested:
                requested.add(right_faction)
            elif "OpponentsOnly" in requested:
                right_faction = "Enemy" if source.PlayerOrEnemy == "Player" else "Player"
                requested.add(right_faction)

            for name, profile in OG_all_profiles.items():
                target_faction = set(profile.faction)

                # does target have at least one of the requested factions?
                if requested & target_faction:  # set intersection not empty
                    all_profiles[name] = profile
        else:
            all_profiles = OG_all_profiles.copy()

        if condition_target_key == "everyone" and modifier_target_key != "everyone":
            if all(evaluate_cond(p,source_page) for p in all_profiles):
                target_profile = source if modifier_target_key == "self" else target
                await apply_modifiers(modifiers, target_profile, acquired_values, effect, log, roll_container,pagename, **common_kwargs)

        elif condition_target_key != "everyone" and modifier_target_key == "everyone":
            cond_profile = source if condition_target_key == "self" else target
            if evaluate_cond(cond_profile,source_page):
                for name, p in all_profiles.items():
                    await apply_modifiers(modifiers, p, acquired_values, effect, log, roll_container,pagename, **common_kwargs)

        elif condition_target_key == "everyone" and modifier_target_key == "everyone":
            for name, p in all_profiles.items():
                if evaluate_cond(p,source_page):
                    print("[DEBUG] COND KEY IS EVERYONE AND MODIFIER KEY IS EVERYONE")
                    await apply_modifiers(modifiers, p, acquired_values, effect, log, roll_container,pagename, **common_kwargs)

    async def apply_modifiers(modifiers, modifier_target : ProfileData, acquired_values, effect, log, roll_container, pagename,
                              **kwargs):
        # === Modifiers ===

        lookup = {}

        if modifier_target is not None:
            lookup["modifier_target"] = modifier_target.name

        if condition_target is not None:
            lookup["condition_target"] = condition_target.name

        if source is not None:
            lookup["self"] = source.name

        kwargs["lookup"] = lookup
        kwargs["modifiers"] = modifiers
        kwargs["interaction"] = interaction

        if roll_container is not None:
            if "setpower" in modifiers and "locked" not in roll_container:
                val = resolve_value(modifiers["setpower"], acquired_values)
                roll_container[0] = val
                roll_container.append("locked")
                if log is not None:
                    log.append(f"{symbol['buff']} {source.name}'s roll is SET to {val} and now locked. {symbol['buff']}")
            if "setpowerunlocked" in modifiers and "locked" not in roll_container:
                val = resolve_value(modifiers["setpowerunlocked"], acquired_values)
                roll_container[0] = val
                if log is not None:
                    log.append(f"{symbol['buff']} {source.name}'s roll is SET to {val} {symbol['buff']}")

            if "power_bonus" in modifiers and "locked" not in roll_container:
                bonus = resolve_value(modifiers["power_bonus"], acquired_values)
                roll_container[0] += bonus  # always just add

                if log is not None:
                    sign = "+" if bonus >= 0 else "-"
                    print(f"we inside of apply_modifiers now bish")
                    log.append(
                        f"{symbol['buff']} {source.name} gains {sign}{abs(bonus)} power to their roll. {symbol['buff']}"
                    )

            if "power_bonus_per_stack" in modifiers and "locked" not in roll_container:
                buff_name = effect.get("_buff_name")
                stack = source.buffs.get(buff_name, {}).get("stack", 0)
                bonus = stack * modifiers["power_bonus_per_stack"]
                roll_container[0] += bonus
                if log is not None:
                    log.append(f"{symbol['buff']} {source.name} gains +{bonus} power from {stack} stack of {buff_name}. {symbol['buff']}")

        elif source_page is not None:
            if "power_bonus" in modifiers:
                bonus = resolve_value(modifiers["power_bonus"], acquired_values)

                # initialize only once
                if "globalpower" not in source_page:
                    source_page["globalpower"] = []

                source_page["globalpower"].append({"value": bonus, "trigger": trigger})
                if log is not None:
                    sign = "+" if bonus >= 0 else "-"
                    print(f"we inside of apply_modifiers now bish (specifically the second part")
                    log.append(
                        f"{symbol['buff']} {source.name} gains {sign}{abs(bonus)} power to their roll. {symbol['buff']}"
                    )

        for key, raw_value in modifiers.items():

            if raw_value is None:
                continue

            handler = MODIFIER_HANDLERS.get(key)
            if handler:
                print(f"{kwargs["damage"]}")
                await handler.apply(raw_value, modifier_target, acquired_values, effect, log,
                                    roll_container, pagename, symbol, **kwargs)

        # Polarize
        # if "polarize" in modifiers:
        #     for stat in modifiers["polarize"]:
        #         if stat in ["Pride", "Wrath", "Lust", "Sloth", "Gluttony", "Gloom", "Envy", "White", "Black"]:
        #             modifier_target["sin_resistances"][stat] = 2.0 - modifier_target["sin_resistances"][stat]
        #             log.append(f"{symbol['stagger']} {modifier_target.get('name', 'Unknown')} had their {stat} Resistance Polarized into {modifier_target['sin_resistances'][stat]} {symbol['stagger']}")
        #             continue
        #         if stat in ["blunt","slash","pierce"]:
        #             modifier_target["resistances"][stat] = 2.0 - modifier_target["resistances"][stat]
        #             log.append(f"{symbol['stagger']} {modifier_target.get('name', 'Unknown')} had their {stat} Resistance Polarized into {modifier_target['resistances'][stat]} {symbol['stagger']}")
        #             continue
        #         if stat in ["stagger blunt","stagger slash","stagger pierce"]:
        #             modifier_target["stagger_resistances"][stat[8:]] = 2.0 - modifier_target["stagger_resistances"][stat[8:]]
        #             log.append(f"{symbol['stagger']} {modifier_target.get('name', 'Unknown')} had their {stat} Resistance Polarized into {modifier_target['stagger_resistances'][stat[8:]]} {symbol['stagger']}")
        #             continue
        #         if isinstance(modifier_target[stat], bool):
        #             modifier_target[stat] = not modifier_target[stat]
        #             continue
        #         if stat in ["hp","light","stagger"]:
        #             modifier_target[stat] = modifier_target["max_"+stat] - modifier_target[stat]
        #             log.append(f"{symbol['stagger'] if stat != 'light' else symbol['light']} {modifier_target.get('name', 'Unknown')} had their {stat.capitalize() if len(stat) > 2 else stat.upper()} Polarized into {modifier_target[stat]} {symbol['stagger'] if stat != 'light' else symbol['light']}")
        #             continue
        #
        #

    for effect in effects:
        # print(f"[DEBUG] Considering effect: {effect} earlier because of trigger: {trigger}")
        if effect.get("trigger") != trigger:
            continue

        effect_id = f"{trigger}_{json.dumps(effect)}"
        global CURRENT_EFFECT_ID
        CURRENT_EFFECT_ID = effect_id

        # --- Per Turn Limit ---
        limit = effect.get("limit_per_turn")
        if limit is not None:
            effect_log = source.effect_limits
            count = effect_log.get(effect_id, 0)

            if count >= limit:
                continue
            else:
                effect_log[effect_id] = count + 1

        # --- Per Encounter Limit ---
        limit = effect.get("limit_per_encounter")
        if limit is not None:
            effect_log = source.effect_limits_perm
            count = effect_log.get(effect_id, 0)

            if count >= limit:
                continue
            else:
                effect_log[effect_id] = count + 1

        modifiers = effect.get("modifiers", {})
        condition_target_key = effect.get("conditionTarget", "self")
        modifier_target_key = effect.get("modifierTarget", "self")
        condition_target = source if condition_target_key == "self" else target
        modifier_target = source if modifier_target_key == "self" else target
        acquired_values = {}
        get_block = effect.get("get", {})

        def handle_condition_target_tomfoolery(condition_target_key):
            random_match = re.match(r"random(?:(\d+)|_VALUE:(.+))", modifier_target_key)
            dynamic_match = re.match(r"(highest|lowest)_(\w+)", modifier_target_key)

            if condition_target_key == "modifierTarget":
                return True

            elif condition_target_key == "self":
                if evaluate_cond(source, source_page):
                    return True
                else:
                    return False

            elif condition_target_key == "target":
                if evaluate_cond(target, source_page):
                    return True
                else:
                    return False

            elif random_match:
                candidates = random_match_targetting(random_match)
                for candidate in candidates:
                    if not evaluate_cond(candidate, source_page):
                        return False

                return True

            elif dynamic_match:
                candidates = dynamic_match_targetting(dynamic_match)
                if evaluate_cond(candidates, source_page):
                    return True
                else:
                    return False

            else:
                print("\n\n  WE REACHED THE FALLBACK ON CONDITION TARGET AND THATS VERY BAD!!!!  \n\n")
                return False

        def random_match_targetting(random_match):
            print(f"\n\nYO WE ACTUALLY GOT INSIDE OF random_match\n\n")
            try:
                if random_match.group(1):  # case: random5
                    amount = int(random_match.group(1))
                elif random_match.group(2):  # case: random_VALUE:SomeName
                    amount = resolve_value(random_match.group(2), acquired_values)
                else:
                    amount = 1
            except (ValueError, TypeError):
                amount = 1


            print(f"random_match_targetting. amount: {amount}")


            eligible = []
            OG_all_profiles = ProfileMan.get_all_active_profiles()
            all_profiles = {}

            if effect.get("filterfaction"):
                right_faction = source.PlayerOrEnemy
                requested = set(effect["filterfaction"])
                if "AlliesOnly" in requested:
                    requested.add(right_faction)
                elif "OpponentsOnly" in requested:
                    right_faction = "Enemy" if source.PlayerOrEnemy == "Player" else "Player"
                    requested.add(right_faction)
                for name, profile in OG_all_profiles.items():
                    target_faction = set(profile.faction)

                    if requested & target_faction:
                        all_profiles[name] = profile
            else:
                all_profiles = OG_all_profiles.copy()

            all_profilesList = list(all_profiles.values())
            debugCandidates = [p.name for p in all_profilesList]
            print(f"\n\n\n[DEBUG] candidates: {debugCandidates}\n\n\n")

            random.shuffle(all_profilesList)
            for p in all_profilesList:
                eligible.append(p)
                if len(eligible) == amount:
                    break

            if eligible:
                return eligible
            else:
                return None

        def dynamic_match_targetting(dynamic_match):
            direction, stat = dynamic_match.groups()

            OG_all_profiles = ProfileMan.get_all_active_profiles()
            all_profiles = {}

            if effect.get("filterfaction"):
                right_faction = source.PlayerOrEnemy
                requested = set(effect["filterfaction"])
                if "AlliesOnly" in requested:
                    requested.add(right_faction)
                elif "OpponentsOnly" in requested:
                    right_faction = "Enemy" if source.PlayerOrEnemy == "Player" else "Player"
                    requested.add(right_faction)
                for name, profile in OG_all_profiles.items():
                    target_faction = set(profile.faction)

                    if requested & target_faction:
                        all_profiles[name] = profile
            else:
                all_profiles = OG_all_profiles.copy()

            candidates = list(all_profiles.values())

            mode = "stat"
            for suffix in ("_stack", "_count"):
                if stat.endswith(suffix):
                    stat = stat.removesuffix(suffix)
                    suffix = suffix.removeprefix("_")
                    mode = "buffs"
                    break

            debugCandidates = [p.name for p in candidates]
            print(f"\n\n\n[DEBUG] candidates: {debugCandidates}\n\n\n")

            if candidates:
                def get_value(p: ProfileData):
                    if mode == "stat":
                        return getattr(p, stat, float("-inf") if direction == "highest" else float("inf"))
                    else:
                        return (
                            p.buffs
                            .get(stat, {})
                            .get(suffix, float("-inf") if direction == "highest" else float("inf"))
                        )

                extreme_func = max if direction == "highest" else min
                newtarget = extreme_func(candidates, key=get_value)
                return newtarget
            else:
                return None

        # this does all of the information getters
        for key, transform in get_block.items():
            val = None
            if key == "StorageBox" and isinstance(transform, list):
                print(f"we currently entered StorageBox getter with the modifier_target: {modifier_target.name}. condition_target: {condition_target.name}. source: {source.name} and the transform {transform} ")
                if not (modifier_target and condition_target and source):
                    print("early return, something here is None")
                    continue

                lookup = {
                    "modifier_target": modifier_target.name,
                    "condition_target": condition_target.name,
                    "self": source.name,
                }

                if target is not None:
                    lookup["target"] = target.name
                for entry in transform:
                    resolved_name = lookup.get(entry["name"], entry["name"])
                    print(f"\n\n[DEBUG] resolved name: {resolved_name}\n\n")

                    valuename = entry["valuename"]
                    print(f"\n\n[DEBUG] value name: {valuename}\n\n")
                    val = data.get("StorageBox", {}).get(resolved_name, {}).get(valuename, 0)
                    print(f"\n\n[DEBUG] val: {val}\n\n")

                    if val is None:
                        print("VAL IS NONE INSIDE OF STORAGE BOX")
                        continue

                    if "mult" in entry:
                        mult = 0.01 * entry["mult"] if isinstance(entry["mult"], int) else resolve_value(entry["mult"], acquired_values)
                        val *= mult
                        val = int(val)
                    if "divide" in entry:
                        val = int(val // entry["divide"] if isinstance(entry["divide"], int) else resolve_value(entry["divide"], acquired_values))
                    if "add" in entry:
                        add = entry["add"] if isinstance(entry["add"], int) else resolve_value(entry["add"], acquired_values)
                        val += add
                        val = int(val)
                    if "max" in entry:
                        val = min(val, resolve_value(entry["max"], acquired_values))
                        val = int(val)
                    if "min" in entry:
                        val = max(val, resolve_value(entry["min"],acquired_values))
                        val = int(val)
                    if "fix" in entry:
                        val = math.floor(val)
                    if "toAbsoluteValue" in entry:
                        print(f"toAbsoluteValue before transformation: {val}")
                        val = abs(val)
                        print(f"toAbsoluteValue after transformation: {val}")
                    if "firstDivideThenMult" in entry:
                        val = int(val // entry["firstDivideThenMult"]["divide"] if isinstance(entry["firstDivideThenMult"]["divide"], int) else resolve_value(entry["firstDivideThenMult"]["divide"], acquired_values))
                        val = int(val * entry["firstDivideThenMult"]["multiply"] if isinstance(entry["firstDivideThenMult"]["multiply"], int) else resolve_value(entry["firstDivideThenMult"]["multiply"], acquired_values))

                    alias_key = f"SB_{valuename}"
                    acquired_values[alias_key] = val
                continue

            if isinstance(transform, dict) and "value" in transform:
                gettarget = source
                if "targetOverride" in transform:
                    gettarget = source if "targetOverride" == "self" else target

                buff_name = key
                field = transform["value"]
                val = gettarget.buffs.get(buff_name, {}).get(field,0)
                if val is None:
                    continue

                try:
                    val = int(val)
                except (TypeError, ValueError):
                    continue

                if "mult" in transform:
                    mult = 0.01 * transform["mult"] if isinstance(transform["mult"], int) else resolve_value(transform["mult"], acquired_values)
                    val *= mult
                if "divide" in transform:
                    divide = resolve_value(transform["divide"], acquired_values)
                    val = int(val / divide)
                if "add" in transform:
                    add = transform["add"] if isinstance(transform["add"], int) else resolve_value(transform["add"], acquired_values)
                    val += add
                if "multbycountstack" in transform:
                    val *= gettarget.buffs.get(buff_name, {}).get(transform["multbycountstack"],1)
                if "addbycountstack" in transform:
                    val += gettarget.buffs.get(buff_name, {}).get(transform["addbycountstack"],1)
                if "max" in transform:
                    val = min(val, resolve_value(transform["max"],acquired_values))
                if "min" in transform:
                    val = max(val, resolve_value(transform["min"],acquired_values))
                if "fix" in transform:
                    val = math.floor(val)
                if "toAbsoluteValue" in transform:
                    val = abs(val)
                if "toNegative" in transform:
                    val = -abs(val)
                alias_key = f"{buff_name}_{field}"
                acquired_values[alias_key] = val
                continue

            if isinstance(transform, dict) and key in ["STR", "DEX", "CON", "INT", "CHA"]:
                gettarget = source
                if "targetOverride" in transform:
                    gettarget = source if "targetOverride" == "self" else target

                buff_name = key
                val = gettarget.calc_stat_mod(key)

                if val is None:
                    continue

                try:
                    val = int(val)
                except (TypeError, ValueError):
                    continue

                if "mult" in transform:
                    mult = 0.01 * transform["mult"] if isinstance(transform["mult"], int) else resolve_value(transform["mult"], acquired_values)
                    val *= mult
                if "divide" in transform:
                    divide = resolve_value(transform["divide"], acquired_values)
                    val = val // divide
                if "add" in transform:
                    add = transform["add"] if isinstance(transform["add"], int) else resolve_value(transform["add"], acquired_values)
                    val += add
                if "max" in transform:
                    val = min(val, resolve_value(transform["max"],acquired_values))
                if "min" in transform:
                    val = max(val, resolve_value(transform["min"],acquired_values))
                if "fix" in transform:
                    val = math.floor(val)
                if "toAbsoluteValue" in transform:
                    val = abs(val)
                if "toNegative" in transform:
                    val = -abs(val)

                alias_key = f"{buff_name}_mod"
                acquired_values[alias_key] = val
                continue

            if isinstance(transform, dict) and key in ["Pride", "Wrath", "Lust", "Sloth", "Gluttony", "Gloom", "Envy", "White", "Black"]:
                gettarget = source
                if "targetOverride" in transform:
                    gettarget = source if "targetOverride" == "self" else target

                if transform.get("faction", False):
                    finalfaction = resolve_value(transform["faction"], acquired_values)
                else:
                    finalfaction = gettarget.PlayerOrEnemy

                sin = key

                if "resonance" in transform:
                    rightLocation = "ResPlayer" if finalfaction == "Player" else "ResEnemy"
                    val = resources[rightLocation][sin]
                    print(val)
                else:
                    val = resources[finalfaction][sin]
                    print(val)

                if val is None:
                    continue

                try:
                    val = int(val)
                except (TypeError, ValueError):
                    continue

                if "mult" in transform:
                    mult = 0.01 * transform["mult"] if isinstance(transform["mult"], int) else resolve_value(transform["mult"], acquired_values)
                    val *= mult
                if "max" in transform:
                    val = min(val, resolve_value(transform["max"],acquired_values))
                if "fix" in transform:
                    val = math.floor(val)
                alias_key = f"{sin}_resource"
                acquired_values[alias_key] = val
                continue

            elif key == "speedDifference":
                print("\n\n\n\n WE ARE CURRENTLY INSIDE OF speedDifference\n\n\n\n")
                val = source.current_speed - target.current_speed
                if isinstance(transform, dict) and "divide" in transform:
                    print(f"val rn is: {val}")
                    val = int(val / transform["divide"])
                    print(f"val rn is: {val}")
                if isinstance(transform, dict) and "max" in transform:
                    print("\n\n")
                    print(f"val rn is: {val}")
                    val = min(val, transform["max"])
                    print(f"val rn is: {val}")
                if val <= 0:
                    val = 0
                    print("\n\n")
                    print(f"val rn is: {val}")
                    print(val)

            elif key == "negativeBuffCount":
                buffsDict = data["buffs"]
                neg_count = 0
                for key, value in source.buffs.items():
                    buffInfo = buffsDict.get(key, {})
                    if buffInfo.get("type", "Pos") == "Neg":
                        neg_count += 1

                val = neg_count

            elif key == "BuffCount":
                neg_count = 0
                for key, value in source.buffs.items():
                    neg_count += 1

                val = neg_count

            elif key == "currentHP":
                val = source.current_hp
                if isinstance(transform, dict) and "divide" in transform:
                    val = val // transform["divide"]
                if isinstance(transform, dict) and "mult" in transform:
                    mult = 0.01 * transform["mult"]
                    val *= mult
                if isinstance(transform, dict) and "max" in transform:
                    val = min(val, transform["max"])

            elif key == "currentStagger":
                val = source.current_stagger

            elif key == "currentMaxHP":
                val = source.max_hp
                print(f"so currently we got currentMaxHP and its: {val}")

                if isinstance(transform, dict) and "divide" in transform:
                    val = val // transform["divide"]
                    print(f"so currently we got currentMaxHP and now, after transformation, it's: {val}")

            elif key == "currentLight":
                val = source.current_light

            elif key == "damagedealt":
                val = damage[0]
            elif key == "minroll":
                val = dice["min"]
            elif key == "maxroll":
                val = dice["max"]
            elif key == "staggerdealt":
                val = stagger[0]
            elif key == "roll":
                val = roll_container[0] if roll_container else 0
            elif key == "dicecount":
                dice_type = transform.get("dice_type", "all")

                count = sum(
                    1 for d in source_page["dice"]
                    if dice_type == "all"
                    or (isinstance(dice_type, str) and d["type"] == dice_type)
                    or (isinstance(dice_type, list) and d["type"] in dice_type)
                )

                val = count

            elif key == "lightcost":
                val = source_page["light_cost"]
            elif key == "random":
                val = random.randint(transform["min"],transform["max"])
            elif key == "hand":
                val = len(source.hand)
            elif key == "handname":
                page_name = next((k for k, v in pages.items() if v is source_page), None)
                val = page_name
            else:
                gettarget = source
                if "targetOverrideStat" in get_block:
                    gettarget = target
                if hasattr(gettarget, key):
                    val = getattr(gettarget, key)
            if val is None:
                continue

            if isinstance(transform, str):
                if transform == "none":
                    val = val
                else:
                    value = resolve_value(transform, acquired_values)
                    val *= value

            if isinstance(transform, int):
                mult = 0.01 * transform
                val *= mult
            acquired_values[key] = val

        for _ in range(int(resolve_value(effect.get("foreach", 1), acquired_values))):
            if "everyone" in (condition_target_key, modifier_target_key):
                await handle_everyone_logic(effect, source, target, log, roll_container, acquired_values)
                continue

            if not handle_condition_target_tomfoolery(condition_target_key):
                print(f"we did not pass handle_condition_target_tomfoolery {condition_target_key}")
                continue

            random_match = re.match(r"random(?:(\d+)|_VALUE:(.+))", modifier_target_key)
            if random_match:
                eligibleModifierTargets = random_match_targetting(random_match)

                for mod_target in eligibleModifierTargets:
                    if condition_target_key == "modifierTarget":
                        print("uhh this is all the tomfoolery")
                        if evaluate_cond(mod_target, source_page):
                            print(f"modifier target: {mod_target.name} went and passed")
                            await apply_modifiers(modifiers, mod_target, acquired_values, effect, log, roll_container,
                                                  pagename, **common_kwargs)
                        else:
                            print(f"modifier target: {mod_target.name} went and failed. like a whore.")
                    else:
                        await apply_modifiers(modifiers, mod_target, acquired_values, effect, log, roll_container,pagename, **common_kwargs)

                continue

            dynamic_match = re.match(r"(highest|lowest)_(\w+)", modifier_target_key)
            if dynamic_match:
                newModifierTarget = dynamic_match_targetting(dynamic_match)

                if condition_target_key == "modifierTarget":
                    if evaluate_cond(newModifierTarget, source_page):
                        await apply_modifiers(modifiers, newModifierTarget, acquired_values, effect, log, roll_container, pagename, **common_kwargs)
                else:
                    await apply_modifiers(modifiers, newModifierTarget, acquired_values, effect, log, roll_container, pagename, **common_kwargs)


                continue


            if condition_target is None or modifier_target is None:
                continue
            else:
                await apply_modifiers(modifiers, modifier_target, acquired_values, effect, log, roll_container,pagename, **common_kwargs)
                continue