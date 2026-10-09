from itertools import combinations

SIX_STAR = {
    frozenset({"top-operator"}),
}
 
FIVE_STAR = {
    frozenset({"senior-operator"}),
    frozenset({"crowd-control", "dp-recovery"}),
    frozenset({"crowd-control", "melee"}),
    frozenset({"crowd-control", "vanguard"}),
    frozenset({"crowd-control", "summon"}),
    frozenset({"crowd-control", "supporter"}),
    frozenset({"crowd-control", "fast-redeploy"}),
    frozenset({"crowd-control", "specialist"}),
    frozenset({"crowd-control", "slow"}),
    frozenset({"debuff", "aoe"}),
    frozenset({"debuff", "supporter"}),
    frozenset({"debuff", "fast-redeploy"}),
    frozenset({"debuff", "melee"}),
    frozenset({"debuff", "specialist"}),
    frozenset({"support", "dp-recovery"}),
    frozenset({"support", "vanguard"}),
    frozenset({"support", "supporter"}),
    frozenset({"support", "survival"}),
    frozenset({"shift", "defender"}),
    frozenset({"shift", "defense"}),
    frozenset({"shift", "dps"}),
    frozenset({"shift", "slow"}),
    frozenset({"nuker", "ranged"}),
    frozenset({"nuker", "sniper"}),
    frozenset({"nuker", "aoe"}),
    frozenset({"nuker", "caster"}),
    frozenset({"specialist", "survival"}),
    frozenset({"specialist", "slow"}),
    frozenset({"summon", "supporter"}),
    frozenset({"slow", "caster", "dps"}),
    frozenset({"dps", "defender"}),
    frozenset({"dps", "defense"}),
    frozenset({"dps", "supporter"}),
    frozenset({"dps", "healing"}),
    frozenset({"dps", "aoe", "guard"}),
    frozenset({"dps", "aoe", "melee"}),
    frozenset({"defense", "survival"}),
    frozenset({"defense", "guard"}),
    frozenset({"defense", "aoe"}),
    frozenset({"defense", "caster"}),
    frozenset({"defense", "ranged"}),
    frozenset({"survival", "defender"}),
    frozenset({"survival", "supporter"}),
    frozenset({"healing", "caster"}),
}
 
FOUR_STAR = {
    frozenset({"crowd-control"}),
    frozenset({"debuff"}),
    frozenset({"support"}),
    frozenset({"shift"}),
    frozenset({"nuker"}),
    frozenset({"specialist"}),
    frozenset({"summon"}),
    frozenset({"fast-redeploy"}),
    frozenset({"slow", "aoe"}),
    frozenset({"slow", "sniper"}),
    frozenset({"slow", "dps"}),
    frozenset({"slow", "guard"}),
    frozenset({"slow", "melee"}),
    frozenset({"slow", "caster"}),
    frozenset({"slow", "healing"}),
    frozenset({"dps", "aoe"}),
    frozenset({"survival", "ranged"}),
    frozenset({"survival", "sniper"}),
    frozenset({"healing", "dp-recovery"}),
    frozenset({"healing", "vanguard"}),
    frozenset({"healing", "supporter"}),
    frozenset({"ranged", "dp-recovery"}),
    frozenset({"ranged", "vanguard"}),
}


TIERS = ((6, SIX_STAR), (5, FIVE_STAR), (4, FOUR_STAR))
MAX_COMBINATION_SIZE = 3


def find_best_combination(tags):
    names = set()
    for tag in tags:
        names.update(tag if isinstance(tag, list) else [tag])
    names = sorted(name.lower() for name in names)

    best_stars, best_combination = None, None

    for size in range(MAX_COMBINATION_SIZE, 0 , -1):
        for combination in combinations(names, size):
            key = frozenset(combination)
            for stars, tier in TIERS:
                if key in tier:
                    if best_stars is None or stars > best_stars:
                        best_stars, best_combination = stars, list(combination)
                    break

    if best_stars is None:
        print("No matching combination found for tags:", names)
    return best_stars, best_combination