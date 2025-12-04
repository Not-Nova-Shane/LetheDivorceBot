# pyright: reportMissingImports=false
import random
import copy
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from everythingexcepthim import (megaload ,
    megasave ,
    autocomplete_page_names ,send_split_embeds,
    autocomplete_profile_names,globalpowerhandler)
from everythingexcepthim import process_effects, attackhandler, clashhandler
from THECORE import (PAGE_PATH ,   PROFILE_PATH ,  lock_command,symbol, ProfileMan )
async def minireset(interaction, data):
    data["StorageBox"] = {}
    profiles = ProfileMan.all_profiles()
    data["MD"]["turncount"] = 0

    for name, profile in profiles.items():
        profile.is_staggered = False
        profile.staggeredThisTurn = False
        profile.nextturn = {"light": 0}
        profile.buffs = {}
        profile.resistances = profile.original_resistances
        profile.effect_limits_perm = {}
        profile.effect_limits = {}
        profile.used = []
        if profile.PlayerOrEnemy == "Player":
            profile.passives = data["inventory"].get(name, {}).get("equippedpas", [])

    await interaction.followup.send("Dantehhh, rewind it back dantehhhhhhh but not fully", ephemeral=False)

async def newturnhandler(interaction,data,autotarget, trueEncounterStart):
    actually_profiles = ProfileMan.get_all_active_profiles()
    turn_log = {}
    log = []
    data["action"] = []
    await process_effects(ProfileMan.get_profile("Bankvorce"), None, None, "truenewturn", log=log,pageusetype="newturn",data=data,interaction=interaction)
    globalpowerhandler(totaldeletion=True, trigger="newturn", data=data)
    for name, profile in actually_profiles.items():

        if name in data["StorageBox"]:
            box = data["StorageBox"][name]
            for key in list(box.keys()):
                if key.endswith("ThisTurn"):
                    new_key = key[:-8] + "LastTurn"
                    box[new_key] = box.pop(key)
                elif key.endswith("LastTurn"):
                    del box[key]

        profile.name = name
        if False:
            pass
        else:
            profile.current_shield = 0
            profile.effect_limits = {}
            print(f"  Rolling speed for {name}...")
            profile.roll_unit_speed()
            print(f"    Speed in function is: {profile.current_speed}")

            profile.buffs = {k: v for k, v in profile.buffs.items() if isinstance(v, dict) and not v.get("volatile", False)}

            if "buffs" in profile.nextturn:
                profile.apply_nextturn_buffs()

            newturnpagelist = []
            for page in profile.hand:
                page_data = data["pages"].get(page)
                if page_data is not None:
                    newturnpagelist.append(page_data)

            profile.offense_level_sources = profile.calc_offense_levelDict()
            profile.defense_level_sources = profile.calc_defense_levelDict()

            await process_effects(profile, None, None, "newturn", source_page=newturnpagelist,log=log,pageusetype="newturn",data=data,interaction=interaction)
            log_drawn = []
            if profile.deck:
                draw_count = profile._current_pages_drawn
                if trueEncounterStart:
                    draw_count *= 3
                deck_counts = {}
                for page, pagedata in profile.deck.items():
                    deck_counts[page] = pagedata["amount"]

                log_drawn = []
                hand_counts = {}
                for _ in range(draw_count):
                    for page,pagedata in profile.hand.items():
                        hand_counts[page] = pagedata["amount"]
                    eligible_pages = [
                        page for page, max_count in deck_counts.items()
                        if hand_counts.get(page, 0) < max_count
                    ]

                    if not eligible_pages:
                        break
                    eligible_pages = [page for page in eligible_pages if page not in profile.used]
                    deckcount = 0
                    for page,pagedata in profile.deck.items():
                        deckcount += pagedata["amount"]
                    if deckcount < 9:
                        missing = 9 - deckcount
                        while missing > 0:
                            eligible_pages.append("Nothing")
                            missing -= 1
                    drawn = random.choice(eligible_pages)
                    if drawn == "Nothing":
                        log_drawn.append(drawn)
                        continue
                    if drawn in profile.hand:
                        profile.hand[drawn]["amount"] += 1
                    else:
                        profile.hand[drawn] = {"cost": profile.deck[drawn]["cost"], "amount": 1}
                    hand_counts[drawn] = hand_counts.get(drawn, 0) + 1
                    log_drawn.append(drawn)
        

            profile.gain_newTurnLight()
            await process_effects(profile, None, None, "on_lightgain", source_page=newturnpagelist,log=log,pageusetype="on_lightgain",data=data,interaction=interaction)
            turn_log.setdefault(name, {
                "gain": profile._current_light_gain,
                "speed": profile.current_speed,
                "draws": []
            })
            turn_log[name]["draws"].append(log_drawn)
        if profile.is_staggered:
            if profile.staggeredThisTurn:
                profile.staggeredThisTurn = False
            else:
                profile.is_staggered = False
                profile.current_stagger = profile.max_stagger
                profile.resistances = profile.original_resistances
        
        profile.evade_queue = []


    if autotarget:
        data["MD"]["turncount"] += 1
    embed = discord.Embed(
    title=f"🎲 New Turn Begins! Turn: {data['MD']['turncount']}",
    description="LETS GO GAMBLING!",
    color=discord.Color.blurple()
    )
    fields = []
    for name, entry in turn_log.items():
        profile = ProfileMan.get_profile(name)
        gain = profile.current_light
        speed = profile.current_speed
        draws = ", ".join(f"*{card}*" for card in entry["draws"]) if entry["draws"] else "*No cards drawn*"
        if "light_gain" in profile.hidden or "light_gain" in profile.temphidden:
            gain = "???"
        if "speed" in profile.hidden or "speed" in profile.temphidden:
            speed = "???"
        if "draw" in profile.hidden or "draw" in profile.temphidden:
            draws = "???"
        value = f"{symbol['light']} Currently has {gain}/{profile._current_max_light} Light | 🎯 Speed: **{speed}**\n➕ Draws: {draws}"
        fields.append((f"🧍 {name}", value, False))
    if log:
        current_chunk = ""
        log_chunks = []

        for line in log:
            if len(current_chunk) + len(line) + 1 > 1024:
                log_chunks.append(current_chunk.strip())
                current_chunk = ""
            current_chunk += line + "\n"

        if current_chunk:
            log_chunks.append(current_chunk.strip())

        for idx, chunk in enumerate(log_chunks):
            title = f"{symbol['buff']} Effects Log" if idx == 0 else f"{symbol['buff']} Effects Log (cont.)"
            fields.append((title, chunk, False))

    await send_split_embeds(interaction, embed, fields)
    if autotarget:
        embed = discord.Embed(
                title="📜 New Turn Began — Enemies will pick their pages soon",
                description="A new turn has began, Enemies will pick out their pages in 5 seconds",
                color=discord.Color.gold()
            )
        await interaction.followup.send(embed=embed)
        await asyncio.sleep(5)
        await targethandler(interaction,data)

async def targethandler(interaction,data):
    profiles = ProfileMan.get_all_active_profiles()
    pages = data["pages"]
    actions = data["action"]
    turn_log = {}

    print("on jah we all inside of targethandler")
    for name, profile in profiles.items():
        if profile.PlayerOrEnemy == "Player":
            continue

        attackslot = profile.attack_slot
        if hasattr(profile, "attackslotchange"):
            profile.attack_slot -= profile.attackslotchange
        if profile.is_staggered:
            attacks_with_targets = []
            for slot_index in range(1, attackslot + 1):
                attacks_with_targets.append({"Page": "Nothing", "Target": "Nobody", "SelfSlot": slot_index, "TargetSlot": -1})
                actions.append({
                    "actor": name,
                    "actorpage": "Nothing",
                    "target": "Nobody",
                    "selfslot": slot_index,
                    "targetslot": -1,
                    "mode": "Nothing"
                })
            turn_log[name] = attacks_with_targets
            continue

        light = profile.current_light
        hand = profile.hand
        hand_pool = [p for p,pagedata in hand.items() if p in pages and pagedata.get("cost", 0) <= light]
        chosen_attacks = []
        remaining_light = light
        current_pool = hand_pool.copy()

        for slot_index in range(1, attackslot + 1):
            affordable = [p for p in set(current_pool) if profile.hand[p].get("cost", 0) <= remaining_light]
            if not affordable:
                chosen_attacks.append((slot_index, None))
                continue
            random.shuffle(current_pool)
            picked = None
            for candidate in current_pool:
                cost = profile.hand[candidate].get("cost", 0)
                if cost <= remaining_light:
                    picked = candidate
                    break
            if not picked:
                chosen_attacks.append((slot_index, None))
                continue

            chosen_attacks.append((slot_index, picked))
            remaining_light -= profile.hand[picked].get("cost", 0)
            try:
                current_pool.remove(picked)
            except ValueError:
                pass

        if not profile.exclude_targets_from_indiscriminate:
            possible_targets = [
                p for p, pdata in ProfileMan.get_all_active_profiles().items()
                if p != name and "Player" in pdata.faction and pdata.is_active
            ]
        else:
            exclude = set(profile.exclude_targets_from_indiscriminate)
            possible_targets = [
                p for p, pdata in ProfileMan.get_all_active_profiles().items()
                if (
                        p != name
                        and pdata.is_active
                        and not exclude.intersection(pdata.faction)
                )
            ]

        attacks_with_targets = []
        for selfslot, picked_page in chosen_attacks:
            if picked_page is None:
                attacks_with_targets.append({"Page": "Nothing", "Target": "Nobody", "SelfSlot": selfslot, "TargetSlot": -1})
                actions.append({
                    "actor": name,
                    "actorpage": "Nothing",
                    "target": "Nobody",
                    "selfslot": selfslot,
                    "targetslot": -1,
                    "mode": "Nothing"
                })
            else:
                if not possible_targets:
                    target_name = "⚠️ No valid target"
                    targetslot = -1
                else:
                    target_name = random.choice(possible_targets)
                    targetslot = random.randint(1, profiles[target_name].attack_slot)

                attacks_with_targets.append({"Page": picked_page, "Target": target_name, "SelfSlot": selfslot, "TargetSlot": targetslot})
                actions.append({
                    "actor": name,
                    "actorpage": picked_page,
                    "target": target_name,
                    "selfslot": selfslot,
                    "targetslot": targetslot,
                    "ogtarget": target_name,
                    "mode": "Unopposed"
                })

        turn_log[name] = attacks_with_targets
    print(f"on jah we finna reached the end of targethandler")

    fields = []
    embed = discord.Embed(
        title="🎲 The Enemies Choose Their Targets!",
        description="LETS GO GAMBLING!",
        color=discord.Color.blurple()
    )

    for name, attacks in turn_log.items():
        header = f"🧍 {name}"
        for attack in attacks:
            page = attack["Page"]
            target = attack["Target"]
            # just for nightlong office. remove this once that combat ends!!
            # profile = ProfileMan.get_profile(name)
            # if "Lights Out Passive" in profile.passives:
            #     newPageName = page[0] + ("." * len(page))
            #     value = f"{name} uses {newPageName} on {target} ({attack['SelfSlot']}:{attack['TargetSlot']})"
            value = f"{name} uses {page} on {target} ({attack['SelfSlot']}:{attack['TargetSlot']})"
            fields.append((header, value, False))
            header = " "

    await send_split_embeds(interaction, embed, fields)
async def combatstarthandler(interaction,data):
    try:
        await interaction.followup.send("I think, therefore i am")
    except Exception:
        await interaction.channel.send("I think, therefore i am (fallback)")

    pages = data["pages"]
    action_queue = data["action"]

    await resetResonance(data)

    phase1_log = []

    pages_used_by_profile = {}
    for action in action_queue:
        actor_name = action.get("actor")
        page_name = action.get("actorpage")
        target = action.get("target")
        if not actor_name or not page_name:
            continue

        actor_profile = ProfileMan.get_profile(actor_name)
        try:
            target_profile = ProfileMan.get_profile(target)
        except Exception:
            target_profile = None
        if not actor_profile or not actor_profile.is_active or actor_profile.is_staggered:
            continue

        await handleResonanceForPage(actor_profile, data, page_name)
        if action.get("mode") == "Clash":
            await handleResonanceForPage(target_profile, data, action.get("targetpage"))

        if actor_name not in pages_used_by_profile:
            pages_used_by_profile[actor_name] = []

        if page_name in pages:
            pages_used_by_profile[actor_name].append(pages[page_name])

        actualPage = data["pages"].get(page_name)

        await process_effects(
            actor_profile, target_profile, None,
            "combat_start",
            source_page=actualPage,
            pagename=page_name if page_name else None,
            log=phase1_log,
            pageusetype="CombatStart",
            data=data, interaction=interaction
        )

    if phase1_log:
        embed = discord.Embed(
            title="📜 Combat Start Effects",
            description="",
            color=discord.Color.blue()
        )
        fields = [("•", entry, False) for entry in phase1_log]
        await send_split_embeds(interaction, embed, fields)
        await asyncio.sleep(2)

    if not action_queue:
        print("empty queue")
    for action in action_queue:
        actor = action["actor"]
        target = action["target"]
        pageName = action["actorpage"]
        action_type = action["mode"]

        if action_type == "Unopposed":
            await attackhandler(interaction, actor, target, pageName, data)

        elif action_type == "Clash":
            defender = action["target"]
            defender_page = action["targetpage"]
            await clashhandler(interaction, data, actor, pageName, defender, defender_page)

        await asyncio.sleep(3)
    enemy = False
    player = False

    phase2_log = []

    if phase2_log:
        embed = discord.Embed(
            title="📜 Turn End Effects",
            description="",
            color=discord.Color.blue()
        )
        fields = [("•", entry, False) for entry in phase2_log]
        await send_split_embeds(interaction, embed, fields)
        await asyncio.sleep(2)

    for action in data["action"]:
        newturnpagelist = []
        actor = action["actor"]
        target = action["target"]
        if target == "Nothing" or target == "None":
            continue

        mode = action.get("mode")
        page_name = action.get("actorpage", "")

        if page_name == "Nothing" or page_name == "None":
            continue


        page_data = data["pages"].get(page_name)
        if page_data is not None:
            newturnpagelist.append(page_data)

        actor_profile = ProfileMan.get_profile(actor)
        target_profile = ProfileMan.get_profile(target)

        await process_effects(actor_profile, target_profile, None, "turn_end", source_page=newturnpagelist, log=phase2_log,
                              pageusetype="turn_end", data=data, interaction=interaction)

        if mode == "Clash":
            targetPage = action.get("targetpage", "")
            newturnpagelist = []

            page_data = data["pages"].get(targetPage)
            if page_data is not None:
                newturnpagelist.append(page_data)

            await process_effects(target_profile, actor_profile, None, "turn_end", source_page=newturnpagelist,
                                  log=phase2_log,
                                  pageusetype="turn_end", data=data, interaction=interaction)


    for profile in ProfileMan.get_all_active_profiles().values():
        if player and enemy:
            break
        if "Player" == profile.PlayerOrEnemy:
            player = True
            continue
        enemy = True
    if enemy and player:
        embed = discord.Embed(
                title="📜 Combat Ended — Initiating New Turn Soon Soon",
                description="Combat has ended, a new turn will begin in 5 seconds.",
                color=discord.Color.gold()
            )
        await interaction.followup.send(embed=embed)
        await asyncio.sleep(5)
        await newturnhandler(interaction,data,True, False)
    else:
        desc = "Congratulations on Beating the Encounter!" if player else "You Have Perished."
        color = discord.Color.green() if player else discord.Color.red()
        embed = discord.Embed(
                title="📜 Encounter Ended",
                description=desc,
                color=color
            )
        await interaction.followup.send(embed=embed)
        await asyncio.sleep(1)
        await minireset(interaction,data)


async def handleResonanceForPage(actor_profile, data, page_name):
    pages = data["pages"]

    page_sin = (
        pages.get(page_name, {})
        .get("dice", [{}])[0]
        .get("sin")
    )
    if page_sin is not None:
        rightResonanceDict = "ResEnemy" if actor_profile.PlayerOrEnemy == "Enemy" else "ResPlayer"
        if page_sin in data["res"][rightResonanceDict]:
            data["res"][rightResonanceDict][page_sin] += 1
            print(f"{rightResonanceDict} for {page_sin} is now: {data["res"][rightResonanceDict][page_sin]}")


async def resetResonance(data):
    for side in ("ResPlayer", "ResEnemy"):
        if side in data["res"]:
            for key in data["res"][side]:
                data["res"][side][key] = 0


async def autocombatstart(interaction, data):
    actions = data["action"]

    action_counts = {name: 0 for name, prof in ProfileMan.get_all_profiles().items()}
    for act in actions:
        actor = act.get("actor")
        target = act.get("target")
        mode = str(act.get("mode", "")).lower()
        if actor in action_counts:
            action_counts[actor] = action_counts.get(actor, 0) + 1
        if target in action_counts and mode == "clash":
            action_counts[target] = action_counts.get(target, 0) + 1

    everyone_done = True
    incomplete = []
    for name, prof in ProfileMan.get_all_active_profiles().items():
        needed = prof.attack_slot
        has = action_counts.get(name, 0)
        if has < needed:
            everyone_done = False
            incomplete.append((name, has, needed))

    if everyone_done and actions:
        def get_action_speed(action, profiles):
            actor_speed = profiles[action["actor"]].current_speed
            if str(action.get("mode","")).lower() == "clash":
                target_speed = profiles[action["target"]].current_speed
                return max(actor_speed, target_speed)
            return actor_speed

        sorted_actions = sorted(actions, key=lambda a: (get_action_speed(a, ProfileMan.get_all_active_profiles()), -a.get("selfslot", 1)), reverse=True)

        embed = discord.Embed(
            title="📜 Queued Combat Actions — Initiating Combat Soon",
            description="All players/enemies have set their actions. Combat will begin in 5 seconds.",
            color=discord.Color.gold()
        )
        fields = []
        for action in sorted_actions:
            actor = action.get("actor")
            target = action.get("target")
            page_name = action.get("actorpage", "Unknown")
            selfslot = action.get("selfslot", 1)
            targetslot = action.get("targetslot", 1)
            mode = action.get("mode", "")

            if str(mode).lower() == "clash":
                target_page = action.get("targetpage", "Unknown")
                text = f"{actor} uses **{page_name}** to clash against {target}'s **{target_page}** ({selfslot}:{targetslot})"
            elif str(mode).lower() == "unopposed":
                text = f"{actor} attacks {target} with **{page_name}** ({selfslot}:{targetslot})"
            elif str(mode).lower() == "nothing":
                text = f"{actor} does nothing ({selfslot})"
            else:
                text = f"{actor} uses **{page_name}** → {mode} ({selfslot}:{targetslot})"

            fields.append((f"🎯 {actor}", text, False))

        await send_split_embeds(interaction, embed, fields)
        await asyncio.sleep(5)
        await combatstarthandler(interaction,data)
class NewTurnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="newturn")
    @lock_command
    async def newturn(self,interaction: discord.Interaction, autotarget: bool = True, realencounterstart: bool = False):
        data = megaload()
        await interaction.response.defer()
        await newturnhandler(interaction,data,autotarget, realencounterstart)
        megasave(data)

    # @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="target")
    @lock_command
    async def target(self, interaction,):
        data = megaload()
        await interaction.response.defer()
        await targethandler(interaction,data)
        megasave(data)


    async def autocomplete_EquippedPage_names(self, interaction: discord.Interaction, current: str):
        # Grab the profile argument if user has filled it in
        profile_name = getattr(interaction.namespace, "profile", None)
        if not profile_name:
            return []  # nothing to suggest if profile isn't selected yet

        # Load profile data
        profile = ProfileMan.get_profile(profile_name)
        if not profile:
            return []  # invalid profile name

        pages = getattr(profile, "hand", [])

        suggestions = [
            app_commands.Choice(name=page_name, value=page_name)
            for page_name in pages
            if current in page_name.lower()
        ]

        return suggestions[:25]  # max 25 suggestions

    def lightCostIsTooHigh(self, data, profile, pagename):
        actions = data["action"]
        total_light_cost = profile.hand[pagename]["cost"]
        for action in actions:
            if action["actor"] == profile.name:
                pageInHand = profile.hand.get(action["actorpage"], None)
                if pageInHand is None:
                    continue

                total_light_cost += pageInHand.get("cost", 0)

        if total_light_cost > profile.current_light:
            return True

        return False


    @app_commands.command(name="action")
    @app_commands.autocomplete(
        page=autocomplete_EquippedPage_names,
        profile=autocomplete_profile_names,
        target=autocomplete_profile_names
    )
    @lock_command
    async def action(self, interaction: discord.Interaction,
                    profile: str, page: str, target: str,
                    selfslot: int = 1, targetslot: int = 1):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.get_all_active_profiles()
        pages = data["pages"]
        actions = data["action"]
        thisProfile = profiles[profile]
        targetProfile = profiles[target]

        if thisProfile.PlayerOrEnemy != "Player" and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("You cannot send actions for enemies (unless you're an admin)")

        if profile not in profiles:
            print("profile not in profiles")
            await interaction.followup.send("Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return
        if target not in profiles:
            print("target not in profiles")
            await interaction.followup.send("Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return

        if page not in pages:
            print("page not in pages")
            await interaction.followup.send("Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return

        if thisProfile.attack_slot < selfslot:
            print("attack_slot lesser than selfslot")
            await interaction.followup.send(
                "Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return

        if targetProfile.attack_slot < targetslot:
            print ("target attack_slot lesser than targetslot")
            await interaction.followup.send(
                "Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return

        if targetslot <= 0:
            print("targetslot lesser than 0")
            await interaction.followup.send(
                "Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return

        if selfslot <= 0:
            print("selfslot lesser than 0")
            await interaction.followup.send(
                "Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
            return




        # if (profile not in profiles or
        #     target not in profiles or
        #     page not in pages or
        #     thisProfile.attack_slot < selfslot or
        #     targetProfile.attack_slot < targetslot or targetslot <= 0 or selfslot <= 0):
        #     await interaction.followup.send("Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows. also gets triggered when you try to act with a dead unit)")
        #     return
        for act in actions:
            mode = str(act.get("mode", "")).lower()
            if act.get("actor") == profile and act.get("selfslot") == selfslot:
                await interaction.followup.send(f"{profile} already has an action in selfslot {selfslot}.")
                return
            if act.get("target") == profile and act.get("targetslot") == selfslot and mode == "clash":
                await interaction.followup.send(f"{profile} is already clashing in slot {selfslot} as a target.")
                return



        if thisProfile.is_staggered:
            await interaction.followup.send(f"{profile} can't act (dead or staggered)")
            return
        if page not in thisProfile.hand:
            await interaction.followup.send("Page not usable because it's not in your hand")
            return

        if self.lightCostIsTooHigh(data, thisProfile, page):
            await interaction.followup.send("Page not usable because you have insufficient light.")
            return
        actionblock = {
            "actor": profile,
            "actorpage": page,
            "target": target,
            "selfslot": selfslot,
            "targetslot": targetslot,
            "mode": "Unopposed"
        }

        clashing = False
        targetpage = None

        for i, existing in enumerate(actions):
            if existing["mode"] == "Nothing":
                continue

            # Case 1: Mirror clash (both targeted each other directly)
            if (existing["actor"] == target
                    and existing["selfslot"] == targetslot
                    and existing["target"] == profile
                    and existing["targetslot"] == selfslot):
                clashing = True
                targetpage = existing["actorpage"]
                actions.pop(i)
                break

            # Case 2: Intercept clash (faster unit clashes target's slot)
            if (existing["actor"] == target
                    and existing["selfslot"] == targetslot):
                # Actor is faster than the enemy action on that slot
                if thisProfile.current_speed > targetProfile.current_speed:
                    clashing = True
                    targetpage = existing["actorpage"]
                    actions.pop(i)
                    break

        if clashing:
            actionblock["mode"] = "Clash"
            actionblock["targetpage"] = targetpage

        actions.append(actionblock)
        def get_action_speed(action, profiles):
            actor_speed = profiles[action["actor"]].current_speed

            if action["mode"].lower() == "clash":
                target_speed = profiles[action["target"]].current_speed
                return max(actor_speed, target_speed)
            
            return actor_speed

        actions.sort(
            key=lambda a: (
                get_action_speed(a, profiles),
                -a["selfslot"]
            ),
            reverse=True
        )

        data["action"] = actions
        await interaction.followup.send("Action added & queue sorted ✅")
        # await autocombatstart(interaction,data)
        megasave(data)


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="deleteallactions")
    @lock_command
    async def deleteallactions(self,interaction: discord.Interaction):
        data = megaload()
        data["action"] = []
        await interaction.response.defer()

        megasave(data)
        await interaction.followup.send(f"Deleted all actions in the action list")

    @app_commands.command(name="removeaction", description="Remove or adjust an action by actor and slot")
    @app_commands.autocomplete(
        actor=autocomplete_profile_names
    )
    @lock_command
    async def removeaction(self, interaction: discord.Interaction, actor: str, slot: int = 1):
        data = megaload()
        await interaction.response.defer()
        actions = data["action"]
        thisProfile = ProfileMan.get_profile(actor)

        if thisProfile.PlayerOrEnemy != "Player" and not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("You cannot remove actions for enemies (unless you're an admin)")

        removed = False
        for act in actions[:]:  # copy so we can safely modify
            if act.get("actor") == actor and act.get("selfslot") == slot:
                mode = str(act.get("mode", "")).lower()

                if mode in ("nothing", "unopposed"):
                    actions.remove(act)
                    removed = True
                    break

                elif mode == "clash":
                    # Restore the opponent's original action
                    restored_action = {
                        "actor": act["target"],  # the enemy becomes the actor
                        "actorpage": act["targetpage"],  # use the saved targetpage
                        "target": act["actor"],  # original actor becomes the target
                        "selfslot": act["targetslot"],
                        "targetslot": act["selfslot"],
                        "mode": "Unopposed"
                    }
                    actions.remove(act)  # remove the clash
                    actions.append(restored_action)  # put back the original action
                    removed = True
                    break

        if removed:
            megasave(data)
            await interaction.followup.send(f"Action for `{actor}` in slot `{slot}` removed/adjusted ✅")
        else:
            await interaction.followup.send(f"No matching action found for `{actor}` in slot `{slot}`.")

    @app_commands.command(name="nothing")
    @app_commands.autocomplete(
        profile=autocomplete_profile_names
    )
    @lock_command
    async def nothing(self, interaction: discord.Interaction, profile: str,selfslot: int = 1):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.get_all_active_profiles()
        pages = data["pages"]
        actions = data["action"]

        if (profile not in profiles or
            profiles[profile].attack_slot < selfslot):
            await interaction.followup.send("Invalid input, you MONKEY 🐒 (or the bot bugged out. who knows.)")
            return
        for act in actions:
            mode = str(act.get("mode", "")).lower()
            if act.get("actor") == profile and act.get("selfslot") == selfslot:
                await interaction.followup.send(f"{profile} already has an action in selfslot {selfslot}.")
                return
            if act.get("target") == profile and act.get("targetslot") == selfslot and mode == "clash":
                await interaction.followup.send(f"{profile} is already clashing in slot {selfslot} as a target.")
                return
        if profiles[profile].is_staggered:
            await interaction.followup.send(f"{profile} can't act (dead or staggered)")
            return

        actionblock = {
            "actor": profile,
            "actorpage": "Nothing",
            "target": "Nobody",
            "selfslot": selfslot,
            "targetslot": -1,
            "mode": "Nothing"
        }

        actions.append(actionblock)
        data["action"] = actions
        await interaction.followup.send("Action added & queue sorted ✅")
        # await autocombatstart(interaction,data)
        megasave(data)

    @app_commands.command(name="setdeploymentorder")
    @lock_command
    async def setdeploymentorder(self, interaction: discord.Interaction, profiles: str):
        data = megaload()
        await interaction.response.defer()
        profile_list = [p.strip() for p in profiles.split(",") if p.strip()]

        profilesDict : dict = {k: v for k, v in ProfileMan.get_all_active_profiles().items() if v.PlayerOrEnemy == "Player"}
        deploymentOrder = {}

        for index, profileName in enumerate(profile_list):
            profileData = profilesDict[profileName]
            deployment = index + 1

            profileData.deploymentOrder = deployment
            deploymentOrder[profileName] = deployment

        megasave(data)
        await interaction.followup.send(f"Dantehhh, the deployment order is {deploymentOrder}", ephemeral=False)



    @app_commands.command(name="viewactions", description="View all queued combat actions")
    async def viewactions(self, interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.get_all_active_profiles()
        actions = data["action"]

        if not actions:
            await interaction.followup.send("No actions queued.")
            return
        def get_action_speed(action, profiles):
            actor_speed = profiles[action["actor"]].current_speed

            if action["mode"].lower() == "clash":
                target_speed = profiles[action["target"]].current_speed
                return max(actor_speed, target_speed)
            
            return actor_speed

        actions.sort(
            key=lambda a: (
                get_action_speed(a, profiles),
                -a["selfslot"]
            ),
            reverse=True
        )
        embed = discord.Embed(
            title="📜 Queued Combat Actions",
            description="Upcoming actions in execution order.",
            color=discord.Color.gold()
        )

        fields = []
        for action in actions:
            profile = ProfileMan.get_profile(action["actor"])
            actor = action["actor"]
            target = action["target"]
            page_name = action.get("actorpage", "Unknown")
            selfslot = action.get("selfslot", 1)
            targetslot = action.get("targetslot", 1)

            if action.get("mode") == "Clash":
                target_page = action.get("targetpage", "Unknown")
                text = f"{actor} uses **{page_name}** to clash against {target}'s **{target_page}** ({selfslot}:{targetslot})"
            elif action.get("mode") == "Unopposed":
                text = f"{actor} attacks {target} with **{page_name}** ({selfslot}:{targetslot})"
            else:
                text = f"{actor} does nothing ({selfslot})"

            fields.append((f"🎯 {actor} (Speed: {profile.current_speed} || HP: {profile.current_hp}/{profile.max_hp})", text, False))

        await send_split_embeds(interaction, embed, fields)

    @app_commands.command(name="combatstart")
    @lock_command
    async def combatstart(self,interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        # print(f"[DEBUG] inside of combatstart, interaction is {interaction}")
        await combatstarthandler(interaction,data)
        megasave(data)
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="reset")
    @lock_command
    async def reset(self,interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.all_profiles()
        resources = data["res"]
        inventory = data["inventory"]
        md = data["MD"]
        for name, profile in profiles.items():
            profile.current_hp = profile.max_hp
            profile.current_stagger = profile.max_stagger
            profile.current_light = profile._current_max_light
            profile.is_staggered = False
            profile.staggeredThisTurn = False
            profile.hand = {}
            for page, pagedata in profile.deck.items():
                pagedata["cost"] = data["pages"][page]["light_cost"]
            profile.nextturn = {"light": 0}
            profile.buffs = {}
            profile.resistances = profile.original_resistances
            profile.is_active = False
            profile.effect_limits_perm = {}
            profile.effect_limits = {}
            profile.temphidden = []
            profile.used = []
            if profile.PlayerOrEnemy == "Player":
                profile.passives = data["inventory"].get(name, {}).get("equippedpas", [])

        data["StorageBox"] = {}
        for faction, sins in resources.items():
            for sin_name in sins:
                sins[sin_name] = 0
        for name, page in data["pages"].items():
            if "dice" not in page:
                print(f"{name} is missing dice!")
                continue
            for dice in page["dice"]:
                if dice.get("invoked",False):
                    dice["invoked"] = False
                    if dice.get("perminvoked"):
                        del dice["perminvoked"]
        for name,gift in data["gifts"].items():
            gift["acquired"] = False
            gift["level"] = 1
        megasave(data)
        await interaction.followup.send("Dantehhh, rewind it back dantehhhhhhh", ephemeral=False)
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="mdreset")
    @lock_command
    async def mdreset(self,interaction: discord.Interaction):
        data = megaload()
        await interaction.response.defer()
        await minireset(interaction, data)
        megasave(data)
    
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="enable")
    @lock_command
    async def enable(self,interaction: discord.Interaction, profile: str):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.get_profile(profile)
        if profiles:
            profiles.is_active = True
            profiles.current_hp = profiles.max_hp
            profiles.current_stagger = profiles.max_stagger
            profiles.current_light = profiles._current_max_light
        else:
            await interaction.followup.send(f"{profile} doesn't exist", ephemeral=False)
            return
        megasave(data)
        await interaction.followup.send(f"{profile} has been enabled", ephemeral=False)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="disable")
    @lock_command
    async def disable(self,interaction: discord.Interaction, profile: str):
        data = megaload()
        await interaction.response.defer()
        profiles = ProfileMan.get_profile(profile)
        if profiles:
            profiles.is_active = False
        else:
            await interaction.followup.send(f"{profile} doesn't exist", ephemeral=False)
            return
        megasave(data)
        await interaction.followup.send(f"{profile} has been disabled", ephemeral=False)

async def setup(bot):
    cog = NewTurnCog(bot)
    await bot.add_cog(cog)

