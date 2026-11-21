#!/usr/bin/env python3
"""Generate offsets directly from dump.cs (single-file IL2CPP dumper output)."""

import re
import sys
from pathlib import Path

FIELD_SPEC = [
    # World and entity graph.
    ("RR_OFF_WORLD_ENTITIES",       "WorldModel",              "WorldEntitiesModel"),
    ("RR_OFF_WEM_BATTLE_CHARS",     "WorldEntitiesModel",      "_battleCharacters"),
    ("RR_OFF_WEM_VEHICLES",         "WorldEntitiesModel",      "_vehicles"),
    # Character model.
    ("RR_OFF_CHAR_ID",              "BattleCharacterModel",    "Id"),
    ("RR_OFF_CHAR_DATA",            "BattleCharacterModel",    "Data"),
    ("RR_OFF_CHAR_CONFIG",          "BattleCharacterModel",    "Config"),
    ("RR_OFF_CHAR_TRANSFORM",       "BattleCharacterModel",    "Transform"),
    ("RR_OFF_CHAR_REPL_TRANSFORM",  "BattleCharacterModel",    "ReplicatedTransform"),
    ("RR_OFF_CHAR_ISDEAD",          "BattleCharacterModel",    "IsDead"),
    ("RR_OFF_CHAR_PRIVATE",         "BattleCharacterModel",    "PrivateModel"),
    # Transform models.
    ("RR_OFF_CTM_X",                "CharacterTransformModel", "X"),
    ("RR_OFF_CTM_Y",                "CharacterTransformModel", "Y"),
    ("RR_OFF_CTM_Z",                "CharacterTransformModel", "Z"),
    ("RR_OFF_CTM_PITCH",            "CharacterTransformModel", "Pitch"),
    ("RR_OFF_CTM_YAW",              "CharacterTransformModel", "Yaw"),
    ("RR_OFF_CTM_ROLL",             "CharacterTransformModel", "Roll"),
    ("RR_OFF_TRANSFORM_X",          "TransformModel",          "_x"),
    ("RR_OFF_TRANSFORM_Y",          "TransformModel",          "_y"),
    ("RR_OFF_TRANSFORM_Z",          "TransformModel",          "_z"),
    ("RR_OFF_TRANSFORM_RX",         "TransformModel",          "_rx"),
    ("RR_OFF_TRANSFORM_RY",         "TransformModel",          "_ry"),
    ("RR_OFF_TRANSFORM_RZ",         "TransformModel",          "_rz"),
    ("RR_OFF_RTRANSFORM_POS",       "CharacterReplicatedTransformModel", "_position"),
    ("RR_OFF_RTRANSFORM_RX",        "CharacterReplicatedTransformModel", "_rx"),
    ("RR_OFF_RTRANSFORM_RY",        "CharacterReplicatedTransformModel", "_ry"),
    ("RR_OFF_RTRANSFORM_RZ",        "CharacterReplicatedTransformModel", "_rz"),
    # Shared, private and public character data.
    ("RR_OFF_DATA_COMMON",          "BattleCharacterData",      "CommonData"),
    ("RR_OFF_DATA_PRIVATE",         "BattleCharacterData",      "PrivateData"),
    ("RR_OFF_DATA_PUBLIC",          "BattleCharacterData",      "PublicData"),
    ("RR_OFF_COMMON_ROLE",          "BattleCharacterCommonData","Role"),
    ("RR_OFF_PRIVATE_HEALTH",       "BattleCharacterPrivateData","Health"),
    ("RR_OFF_PUBLIC_ARMOR",         "BattleCharacterPublicData","HasArmor"),
    ("RR_OFF_CHAR_WEAPON",          "BattleCharacterModel",     "Weapon"),
    ("RR_OFF_CHAR_CROUCH",          "BattleCharacterModel",     "CrouchModel"),
    ("RR_OFF_CHAR_STANCE",          "BattleCharacterModel",     "BattleStanceModel"),
    ("RR_OFF_CHAR_PBM",             "BattleCharacterModel",     "PlayerBattleModel"),
    ("RR_OFF_WEAPON_ITEM",          "WeaponModel",              "_itemInHands"),
    ("RR_OFF_CROUCH_BOOL",          "CrouchModel",              "_isCrouching"),
    ("RR_OFF_STANCE_REF",           "BattleStanceModel",        "_battleStance"),
    ("RR_OFF_PBM_DATA",             "PlayerBattleModel",        "Data"),
    # Camera fields.
    ("RR_OFF_CAM_POS",              "BattleCameraModel",       "Position"),
    ("RR_OFF_CAM_ROT",              "BattleCameraModel",       "Orientation"),
    ("RR_OFF_CAM_FWD",              "BattleCameraModel",       "Forward"),
    ("RR_OFF_CAM_RIGHT",            "BattleCameraModel",       "Right"),
    ("RR_OFF_CAM_UP",               "BattleCameraModel",       "Up"),
    ("RR_OFF_CAM_DIST",             "BattleCameraModel",       "DistanceToFollowTarget"),
    # Health model fields.
    ("RR_OFF_HEALTH_VALUE",         "HealthModel",             "_health"),
    ("RR_OFF_HEALTH_DEAD",          "HealthModel",             "_isDead"),
    ("RR_OFF_HEALTH_MAX",           "HealthModel",             "_maxAmount"),
    # Roulette
    ("RR_OFF_WEM_ROULETTES",        "WorldEntitiesModel",      "_rouletteModels"),
    ("RR_OFF_RM_PHASE",             "RouletteModel",           "<Phase>k__BackingField"),
    ("RR_OFF_RM_PHASE_END",         "RouletteModel",           "<PhaseEndTs>k__BackingField"),
    ("RR_OFF_RM_WIN_NUMBER",        "RouletteModel",           "<WinningNumber>k__BackingField"),
    ("RR_OFF_RM_BETS_BY_CHAR",      "RouletteModel",           "_betsByCharacter"),
    # AddBet RVA
    ("RR_RVA_ADDBET",               "RouletteModel",           "AddBet"),
]

STATIC_FIELD_SPEC = [
    ("RR_SF_BET_STRAIGHT0", "RouletteBetDescriptions", "Straight0"),
    ("RR_SF_BET_DOZEN_1_12", "RouletteBetDescriptions", "Dozen_1_12"),
    ("RR_SF_BET_DOZEN_13_24", "RouletteBetDescriptions", "Dozen_13_24"),
    ("RR_SF_BET_DOZEN_25_36", "RouletteBetDescriptions", "Dozen_25_36"),
    ("RR_SF_BET_RED", "RouletteBetDescriptions", "Red"),
    ("RR_SF_BET_BLACK", "RouletteBetDescriptions", "Black"),
    ("RR_SF_CHIP_1K", "RouletteChipDescriptions", "Chip1k"),
    ("RR_SF_CHIP_5K", "RouletteChipDescriptions", "Chip5k"),
    ("RR_SF_CHIP_25K", "RouletteChipDescriptions", "Chip25k"),
    ("RR_SF_CHIP_50K", "RouletteChipDescriptions", "Chip50k"),
    ("RR_SF_CHIP_100K", "RouletteChipDescriptions", "Chip100k"),
]

def parse_dumpcs(dump_path):
    """Parse dump.cs and return dict: (class_name, field_name) -> offset"""
    text = Path(dump_path).read_text(encoding="utf-8", errors="ignore")
    
    # Find all class definitions with fields
    # Pattern: // RVA: 0xXXXXXXXX Offset: 0xXXXXXXXX VA: 0xXXXXXXXX
    # public class ClassName { ... fields with // 0xXXX comments ... }
    
    results = {}
    current_class = None
    in_class = False
    
    # First pass: find class names and their field offsets
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Match class definition
        class_match = re.match(r'^\s*(?:public\s+)?class\s+(\w+)', line)
        if class_match:
            current_class = class_match.group(1)
            in_class = True
            continue
        
        if in_class:
            # End of class
            if line.strip() == '}':
                in_class = False
                current_class = None
                continue
            
            # Field with offset comment: private readonly Type _fieldName; // 0xXX
            field_match = re.search(r'(?:private|public|protected|internal)?\s*(?:readonly\s+)?\w+(?:<\w+>)?\s+(\w+)\s*;\s*//\s*0x([0-9A-Fa-f]+)', line)
            if field_match and current_class:
                field_name = field_match.group(1)
                offset = int(field_match.group(2), 16)
                results[(current_class, field_name)] = offset
                continue
            
            # Property with backing field: [CompilerGenerated] private readonly Type <Name>k__BackingField; // 0xXX
            prop_match = re.search(r'\[CompilerGenerated\]\s+(?:private|public|protected|internal)?\s+(?:readonly\s+)?\w+(?:<\w+>)?\s+<(\w+)>k__BackingField\s*;\s*//\s*0x([0-9A-Fa-f]+)', line)
            if prop_match and current_class:
                field_name = "<" + prop_match.group(1) + ">k__BackingField"
                offset = int(prop_match.group(2), 16)
                results[(current_class, field_name)] = offset
                continue
            
            # Method with RVA: // RVA: 0xXXXXXXXX Offset: 0xXXXXXXXX VA: 0xXXXXXXXX
            # public ReturnType MethodName() { }
            method_match = re.search(r'//\s*RVA:\s*0x([0-9A-Fa-f]+)\s+Offset:\s*0x([0-9A-Fa-f]+)\s+VA:\s*0x[0-9A-Fa-f]+', line)
            if method_match and current_class:
                # Look at next non-empty line for method name
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('//'):
                        method_name_match = re.match(r'(?:public|private|protected|internal)?\s+\w+\s+(\w+)\s*\(', next_line)
                        if method_name_match:
                            method_name = method_name_match.group(1)
                            rva = int(method_match.group(1), 16)
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
    
    # Generate header
    lines = [
        "// Auto-generated from dump.cs by gen_offsets_dumpcs.py",
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