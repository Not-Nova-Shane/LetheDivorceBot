import json
from pathlib import Path
import random
import os
from pathlib import Path
from typing import Iterable, Generator, Dict, Any

# Keywords mapped to the tag name you want added
TAG_KEYWORDS: Iterable[str] = [
    "Offense Level Up",
    "Defense Level Up",
    "Defense Level Down",
    "Lights Out",
    "Overstimulated",
    "ThornArrow",
    "RawFuel",
    "ReadyFuel",
    "Heated",
    "Overheated",
    "Poison",
    "Attack Power Up",
    "Power Up",
    "Power Down",
    "Attack Power Down",
    "Defense Power Up",
    "Defense Power Down",
    "Clash Power Down",
    "Paralyze",
    "Bruise",
    "Haste",
    "Bind",
    "Burn",
    "Tremor",
    "Rupture",
    "Sinking",
    "Bleed",
    "Charge",
    "Ammo",
    "Black Belt",
    "Poise",
    "Stagger Protection",
    "Protection",
    "Fragile",
    "Pierce Fragility",
    "Pierce Damage Up",
    "Stagger Fragility",
    "Blunt Stagger Damage Up",
    "Stagger Damage Up",
    "Blunt Stagger Damage Down",
    "Charge Barrier",
    "Damage Up",
    "Clash Power Up",
    "Lust Power Up",
    "Black Power Up",
    "White Power Up",
]


# HELPER FUNCTIONS

def load_json(file_path: str) -> Any:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Any, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({"list": data}, f, indent=4, ensure_ascii=False)

def iter_strings(obj: Any, include_keys: bool = True) -> Generator[str, None, None]:
    """
    Recursively yield ALL string content from dicts/lists.
    - Includes dict KEYS (so we catch tags like "Bleed" used as keys)
    - Yields lowercase strings for case-insensitive matching
    """
    if isinstance(obj, dict):
        if include_keys:
            for k in obj.keys():
                if isinstance(k, str) and k:
                    yield k.lower()
        for v in obj.values():
            yield from iter_strings(v, include_keys=include_keys)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_strings(item, include_keys=include_keys)
    elif isinstance(obj, str):
        if obj:
            yield obj.lower()
    # Non-strings are ignored (int, bool, None, etc.)

def export_buff_names(json_file="buffs.json", output_file="buff_names.txt"):
    # Load buffs.json
    buffs = load_json(json_file)
    
    # Extract names — assumes each entry has a "name" key
    names = [buff for buff in buffs]
    # Write to text file with newline after each name
    with open(output_file, "w", encoding="utf-8") as f:
        for name in names:
            f.write(f'"' + name + f'",' + "\n")

    print(f"✅ Exported {len(names)} buff names to {output_file}")

TAG_FIELD = "pageTagList"  # or "skillTagList" if that's what you use

def OVERWRITE_PAGES_WITH_PAGETAGLIST(input_path, output_path):
    # Load JSON
    pages = load_json(input_path)

    for card_name, card_data in pages.items():
        card_data.setdefault(TAG_FIELD, [])

        # Gather search corpus from 'effects' and 'dice'
        corpus = []
        if "effects" in card_data:
            corpus.extend(iter_strings(card_data["effects"], include_keys=True))
        if "dice" in card_data:
            corpus.extend(iter_strings(card_data["dice"], include_keys=True))

        # Deduplicate the corpus a bit for speed
        corpus_set = set(corpus)

        # For each tag, do a case-insensitive substring check
        for tag in TAG_KEYWORDS:
            tag_l = tag.lower()
            if any(tag_l in s for s in corpus_set):
                if tag not in card_data[TAG_FIELD]:
                    card_data[TAG_FIELD].append(tag)

    # Save updated JSON
    save_json(pages, output_path)

def OVERWRITE_ENTIRE_FOLDER(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(folder_path, f"{filename}")

            print(f"Processing {input_path} -> {output_path}")
            OVERWRITE_PAGES_WITH_PAGETAGLIST(input_path, output_path)

def unwrap_list_wrappers(data):
    """Recursively unwrap 'list' keys at the top level until clean."""
    while isinstance(data, dict) and "list" in data and isinstance(data["list"], dict):
        data = data["list"]
    return data

def fix_json_format(file_path, overwrite=True):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Unwrap all nested "list" wrappers
    fixed_data = unwrap_list_wrappers(data)

    # Decide output path
    out_path = file_path if overwrite else file_path.replace(".json", "_fixed.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=4)

    print(f"Fixed: {file_path} -> {out_path}")

def fix_folder(folder_path, overwrite=True):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            fix_json_format(os.path.join(folder_path, filename), overwrite=overwrite)

def main():
    # export_buff_names()

    # then provide it with the pages.json's correct path and boom it spits out what you need
    # OVERWRITE_ENTIRE_FOLDER(r"pages")
    fix_folder(r"pages", overwrite=True)


if __name__ == "__main__":
    main()