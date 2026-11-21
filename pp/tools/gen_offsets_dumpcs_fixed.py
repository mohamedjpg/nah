#!/usr/bin/env python3
"""Generate offsets directly from dump.cs (single-file IL2CPP dumper output)."""

import re
import sys
from pathlib import Path

FIELD_SPEC = [
    ("RR_OFF_WORLD_ENTITIES",       "WorldModel",              "<WorldEntitiesModel>k__BackingField"),
    ("RR_OFF_WEM_BATTLE_CHARS",     "WorldEntitiesModel",      "_battleCharacters"),
    ("RR_OFF_WEM_VEHICLES",         "WorldEntitiesModel",      "_vehicles"),
    ("RR_OFF_WEM_ROULETTES",        "WorldEntitiesModel",      "_rouletteModels"),
    ("RR_OFF_CHAR_ID",              "BattleCharacterModel",    "<Id>k__BackingField"),
    ("RR_OFF_CHAR_DATA",            "BattleCharacterModel",    "<Data>k__BackingField"),
    ("RR_OFF_CHAR_CONFIG",          "BattleCharacterModel",    "<Config>k__BackingField"),
    ("RR_OFF_CHAR_TRANSFORM",       "BattleCharacterModel",    "<Transform>k__BackingField"),
    ("RR_OFF_CHAR_REPL_TRANSFORM",  "BattleCharacterModel",    "<ReplicatedTransform>k__BackingField"),
    ("RR_OFF_CHAR_ISDEAD",          "BattleCharacterModel",    "<IsDead>k__BackingField"),
    ("RR_OFF_CHAR_PRIVATE",         "BattleCharacterModel",    "<PrivateModel>k__BackingField"),
    ("RR_OFF_CHAR_WEAPON",          "BattleCharacterModel",    "<Weapon>k__BackingField"),
    ("RR_OFF_CHAR_CROUCH",          "BattleCharacterModel",    "<CrouchModel>k__BackingField"),
    ("RR_OFF_CHAR_STANCE",          "BattleCharacterModel",    "<BattleStanceModel>k__BackingField"),
    ("RR_OFF_CHAR_PBM",             "BattleCharacterModel",    "<PlayerBattleModel>k__BackingField"),
    ("RR_OFF_RM_PHASE",             "RouletteModel",           "<Phase>k__BackingField"),
    ("RR_OFF_RM_PHASE_END",         "RouletteModel",           "<PhaseEndTs>k__BackingField"),
    ("RR_OFF_RM_WIN_NUMBER",        "RouletteModel",           "<WinningNumber>k__BackingField"),
    ("RR_OFF_RM_BETS_BY_CHAR",      "RouletteModel",           "_betsByCharacter"),
    ("RR_RVA_ADDBET",               "RouletteModel",           "AddBet"),
]

STATIC_FIELD_SPEC = [
    ("RR_SF_BET_STRAIGHT0", "RouletteBetDescriptions", "Straight0"),
    ("RR_SF_BET_DOZEN_1_12", "RouletteBetDescriptions", "Dozen_1_12"),
    ("RR_SF_BET_DOZEN_13_24", "RouletteBetDescriptions", "Dozen_13_24"),
    ("RR_SF_BET_DOZEN_25_36", "RouletteBetDescriptions", "Dozen_25_36"),
    ("RR_SF_BET_RED", "RouletteBetDescriptions", "Red"),
    ("RR_SF_BET_BLACK", "RouletteBetDescriptions", "Black"),
    ("RR_SF_CHIP_1K", "RouletteChipDescriptions", "<Chip1k>k__BackingField"),
    ("RR_SF_CHIP_5K", "RouletteChipDescriptions", "<Chip5k>k__BackingField"),
    ("RR_SF_CHIP_25K", "RouletteChipDescriptions", "<Chip25k>k__BackingField"),
    ("RR_SF_CHIP_50K", "RouletteChipDescriptions", "<Chip50k>k__BackingField"),
    ("RR_SF_CHIP_100K", "RouletteChipDescriptions", "<Chip100k>k__BackingField"),
]

def parse_dumpcs(dump_path):
    text = Path(dump_path).read_text(encoding="utf-8", errors="ignore")
    results = {}
    current_class = None
    in_class = False
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        class_match = re.match(r'^\s*(?:public\s+)?class\s+(\w+)', line)
        if class_match:
            current_class = class_match.group(1)
            in_class = True
            continue
        
        if in_class:
            if line.strip() == '}':
                in_class = False
                current_class = None
                continue
            
            field_match = re.search(r'(?:private|public|protected|internal)?\s*(?:readonly\s+)?\w+(?:<\w+>)?\s+(\w+)\s*;\s*//\s*0x([0-9A-Fa-f]+)', line)
            if field_match and current_class:
                field_name = field_match.group(1)
                offset = int(field_match.group(2), 16)
                results[(current_class, field_name)] = offset
                continue
            
            prop_match = re.search(r'\[CompilerGenerated\]\s+(?:private|public|protected|internal)?\s+(?:readonly\s+)?\w+(?:<\w+>)?\s+<(\w+)>k__BackingField\s*;\s*//\s*0x([0-9A-Fa-f]+)', line)
            if prop_match and current_class:
                field_name = "<" + prop_match.group(1) + ">k__BackingField"
                offset = int(prop_match.group(2), 16)
                results[(current_class, field_name)] = offset
                continue
            
            static_match = re.search(r'(?:public|private|protected|internal)?\s+static\s+(?:readonly\s+)?\w+(?:<\w+>)?\s+(\w+)\s*;\s*//\s*0x([0-9A-Fa-f]+)', line)
            if static_match and current_class:
                field_name = static_match.group(1)
                offset = int(static_match.group(2), 16)
                results[(current_class, field_name)] = offset
                continue
            
            method_rva_match = re.search(r'//\s*RVA:\s*0x([0-9A-Fa-f]+)\s+Offset:\s*0x([0-9A-Fa-f]+)\s+VA:\s*0x[0-9A-Fa-f]+', line)
            if method_rva_match and current_class:
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('//'):
                        method_name_match = re.match(r'(?:public|private|protected|internal)?\s+\w+\s+(\w+)\s*\(', next_line)
                        if method_name_match:
                            method_name = method_name_match.group(1)
                            rva = int(method_rva_match.group(1), 16)
                            results[(current_class, method_name)] = rva
                            break
    
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", required=True, help="Path to dump.cs")
    parser.add_argument("--header", required=True, help="Output header path")
    args = parser.parse_args()
    
    dump_path = Path(args.dump)
    header_path = Path(args.header)
    
    if not dump_path.exists():
        print(f"dump.cs not found at {dump_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Parsing {dump_path}...")
    offsets = parse_dumpcs(dump_path)
    print(f"Found {len(offsets)} fields/methods with offsets")
    
    lines = [
        "// Auto-generated from dump.cs by gen_offsets_dumpcs_fixed.py",
        "// DO NOT EDIT",
        "",
        "#pragma once",
        "",
    ]
    
    missing = []
    for macro, class_name, field_name in FIELD_SPEC:
        key = (class_name, field_name)
        if key in offsets:
            lines.append(f"#define {macro} 0x{offsets[key]:X}u")
        else:
            lines.append(f"// {macro} NOT FOUND ({class_name}::{field_name})")
            missing.append(f"{class_name}::{field_name}")
    
    lines.append("")
    lines.append("// Static field offsets (from static class field comments)")
    for macro, class_name, field_name in STATIC_FIELD_SPEC:
        key = (class_name, field_name)
        if key in offsets:
            lines.append(f"#define {macro} 0x{offsets[key]:X}u")
        else:
            lines.append(f"// {macro} NOT FOUND ({class_name}::{field_name})")
            missing.append(f"{class_name}::{field_name}")
    
    header_path.write_text('\n'.join(lines), encoding="utf-8")
    print(f"Written to {header_path}")
    
    if missing:
        print(f"WARNING: {len(missing)} offsets not found:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()