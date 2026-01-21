# RFG Palette System - Scoring Engine
# This module handles all the season determination logic


# IMPROVED RECIPES - Gets 10/12 passing
SEASON_RECIPES = {
    # SUMMERS
    "soft_summer":   {"cool": 1.0, "soft": 1.6, "contrast_low": 0.8},
    "cool_summer":   {"cool": 1.8, "soft": 0.4, "bright": 0.8, "contrast_low": 0.3},
    "light_summer":  {"cool": 1.0, "light": 4.0, "soft": 0.4},
    
    # WINTERS  
    "bright_winter": {"cool": 1.1, "bright": 2.0, "contrast_high": 1.2},
    "cool_winter":   {"cool": 1.9, "bright": 0.7, "contrast_high": 1.2},
    "dark_winter":   {"cool": 1.0, "deep": 1.8, "contrast_high": 1.0},
    
    # AUTUMNS
    "soft_autumn":   {"warm": 1.0, "soft": 1.8, "contrast_low": 0.5},
    "warm_autumn":   {"warm": 2.0, "soft": 0.2, "deep": 0.8},
    "dark_autumn":   {"warm": 1.0, "deep": 2.5, "contrast_high": 0.8},
    
    # SPRINGS
    "bright_spring": {"warm": 1.3, "bright": 1.9, "contrast_high": 0.8},
    "warm_spring":   {"warm": 1.8, "bright": 1.0, "contrast_low": 0.3},
    "light_spring":  {"warm": 0.5, "light": 5.0, "bright": 0.5}
}


def calculate_traits(answers):
    """
    Takes a dict of user answers and returns a dict of trait scores.
    
    Args:
        answers: dict with keys like 'eye_color', 'hair_color', 'skin_tone', etc.
    
    Returns:
        dict of trait scores like {'cool': 12, 'warm': 5, 'soft': 8, ...}
    """
    # Initialize trait buckets
    traits = {
        "cool": 0,
        "warm": 0,
        "soft": 0,
        "bright": 0,
        "contrast_high": 0,
        "contrast_low": 0,
        "light": 0,
        "deep": 0,
    }
    
    # Constants
    PRIMARY = 2  # Multiplier for primary traits
    cool_vein_colors = ["blue", "purple", "lavender", "violet"]
    warm_vein_colors = ["green", "blue-green", "teal"]
    
    # Extract answers
    skin_tone = answers.get("skin_tone")
    jewelry = answers.get("jewelry")
    veins = answers.get("veins")
    eyes = answers.get("eyes")
    contrast = answers.get("contrast")
    hair_color = answers.get("hair_color")
    eye_color = answers.get("eye_color")
    black_test = answers.get("black_test")
    white_test = answers.get("white_test")
    wrong_metal = answers.get("wrong_metal")
    worst_color = answers.get("worst_color")
    best_comp = answers.get("best_comp")
    
    # 1. Skin Tone (Primary) - Multiplied
    if skin_tone == "cool":
        traits["cool"] += (2 * PRIMARY)
    elif skin_tone == "warm":
        traits["warm"] += (2 * PRIMARY)
    else:  # neutral
        traits["cool"] += (1 * PRIMARY)
        traits["warm"] += (1 * PRIMARY)
    
    # 2. Jewelry (Secondary) - Standard
    if jewelry == "silver":
        traits["cool"] += 1
    elif jewelry == "gold":
        traits["warm"] += 1
    else:  # both
        traits["cool"] += 1
        traits["warm"] += 1
    
    # 3. Veins (Secondary) - Standard
    if veins in cool_vein_colors:
        traits["cool"] += 2
    elif veins in warm_vein_colors:
        traits["warm"] += 2
    
    # 4. Eye Quality (Primary) - Multiplied
    if eyes == "soft":
        traits["soft"] += (2 * PRIMARY)
    else:
        traits["bright"] += (2 * PRIMARY)
    
    # 5. Contrast (Secondary) - Standard
    if contrast == "high":
        traits["contrast_high"] += 2
        traits["deep"] += 1
    else:
        traits["contrast_low"] += 2
        traits["soft"] += 1
    
    # 6. Hair Depth (Primary) - Multiplied
    if hair_color in ["black", "dark brown"]:
        traits["deep"] += (2 * PRIMARY)
    elif hair_color == "blonde":
        traits["light"] += (2 * PRIMARY)
    elif hair_color == "red":
        traits["warm"] += (2 * PRIMARY)
    
    # 7. Eye Color (Primary) - Multiplied
    if eye_color in ["blue", "green"]:
        traits["cool"] += (1 * PRIMARY)
        traits["bright"] += 1
    elif eye_color == "brown":
        traits["deep"] += 1
        if hair_color in ["black", "dark brown"]:
            traits["warm"] += 1  # Dark hair + brown eyes often warm
    elif eye_color == "hazel":
        traits["warm"] += (1 * PRIMARY)
        traits["soft"] += 1
    
    # 8. Black Test (High Signal for Contrast/Depth)
    if black_test == "yes":
        traits["contrast_high"] += (2 * PRIMARY)
        traits["deep"] += 1
    elif black_test == "softened":
        traits["contrast_high"] += 1
        traits["soft"] += 1
    else:  # no
        traits["contrast_low"] += (2 * PRIMARY)
        traits["soft"] += 1
    
    # 9. White Test (Moderate Signal)
    if white_test == "optic":
        traits["cool"] += 1
        traits["bright"] += 1
    elif white_test == "soft":
        traits["cool"] += 1
        traits["soft"] += 1
    else:  # cream
        traits["warm"] += 1
        traits["soft"] += 1
    
    # 10. Wrong Metal Effect (High Signal for Undertone)
    if wrong_metal == "gold_sallow":
        traits["cool"] += (2 * PRIMARY)
    elif wrong_metal == "silver_gray":
        traits["warm"] += (2 * PRIMARY)
    # no_diff -> neutral, no change
    
    # 11. Worst Color (Moderate Signal)
    if worst_color == "mustard":
        traits["cool"] += (1 * PRIMARY)
    elif worst_color == "icypink":
        traits["warm"] += (1 * PRIMARY)
    elif worst_color == "black":
        traits["soft"] += 2
        traits["contrast_low"] += 1
    elif worst_color == "hotpink":
        traits["soft"] += 1
        traits["cool"] += 1
    elif worst_color == "camel":
        traits["cool"] += 1
        traits["soft"] += 1
    
    # 12. Best Compliment (Lower Signal - Subjective)
    if best_comp == "dusty_rose":
        traits["soft"] += 2
        traits["cool"] += 1
    elif best_comp == "coral":
        traits["warm"] += 2
        traits["bright"] += 1
    elif best_comp == "cobalt":
        traits["cool"] += 2
        traits["bright"] += 1
        traits["contrast_high"] += 1
    elif best_comp == "rust":
        traits["warm"] += 2
        traits["deep"] += 1
    elif best_comp == "icy_lavender":
        traits["cool"] += 2
        traits["light"] += 1
    elif best_comp == "chartreuse":
        traits["warm"] += 1
        traits["bright"] += 2
    
    return traits


def determine_season(traits):
    """
    Takes trait scores and returns season determination results.
    
    Args:
        traits: dict of trait scores from calculate_traits()
    
    Returns:
        dict with keys:
            - 'season': winning season name
            - 'confidence_percent': int 0-100
            - 'confidence_label': string description
            - 'winner_score': int
            - 'runner_up': season name
            - 'runner_score': int
            - 'ranked': list of (season, score) tuples sorted by score
    """
    # Score each season
    season_scores = {}
    for season, recipe in SEASON_RECIPES.items():
        season_scores[season] = sum(traits[k] * w for k, w in recipe.items())
    
    # Pick winner + runner up
    ranked = sorted(season_scores.items(), key=lambda x: x[1], reverse=True)
    winner, winner_score = ranked[0]
    runner, runner_score = ranked[1]
    
    # Calculate confidence
    all_scores = list(season_scores.values())
    average_score = sum(all_scores) / len(all_scores)
    raw_lead = winner_score - average_score
    gap = winner_score - runner_score
    
    if winner_score > 0:
        accuracy_calc = ((raw_lead + gap) / winner_score) * 100
        confidence_percent = round(min(max(accuracy_calc, 0), 100))
    else:
        confidence_percent = 0
    
    # Confidence label
    if confidence_percent > 75:
        confidence_label = "High (Clear Winner)"
    elif confidence_percent > 45:
        confidence_label = "Medium (Likely Match)"
    else:
        confidence_label = "Low (Borderline/Mixed)"
    
    return {
        'season': winner,
        'confidence_percent': confidence_percent,
        'confidence_label': confidence_label,
        'winner_score': winner_score,
        'runner_up': runner,
        'runner_score': runner_score,
        'ranked': ranked
    }


def trait_label(key):
    """Turn internal trait keys into human-friendly labels."""
    labels = {
        "cool": "Cool",
        "warm": "Warm",
        "soft": "Soft",
        "bright": "Bright",
        "contrast_high": "High Contrast",
        "contrast_low": "Low Contrast",
        "light": "Light",
        "deep": "Deep",
    }
    return labels.get(key, key.replace("_", " ").title())


def trait_summary(traits, top_n=3, weak_n=2):
    """
    Return two lists of tuples: (dominant, weak)
    dominant: top_n traits by score (excluding zeros)
    weak: weak_n lowest nonzero traits, excluding anything already in dominant
    """
    items = list(traits.items())
    
    # Dominant = highest scores first
    dominant = sorted(items, key=lambda kv: kv[1], reverse=True)
    dominant = [(k, v) for k, v in dominant if v > 0][:top_n]
    
    # Weak = lowest nonzero scores, excluding dominant traits
    dominant_keys = {k for k, _ in dominant}
    nonzero = [(k, v) for k, v in items if v > 0 and k not in dominant_keys]
    weak = sorted(nonzero, key=lambda kv: kv[1])[:weak_n]
    
    return dominant, weak


def season_label(season_key):
    """Convert season key to human-friendly label."""
    return season_key.replace("_", " ").title()


def detect_tensions(traits):
    """Identify conflicting trait signals."""
    tensions = []
    
    # Soft vs Bright
    if traits["soft"] > 0 and traits["bright"] > 0:
        diff = abs(traits["soft"] - traits["bright"])
        if diff <= 2:
            tensions.append("soft vs bright (mixed chroma signal)")
        elif traits["soft"] > traits["bright"]:
            tensions.append("mostly soft, with some brightness present")
        else:
            tensions.append("mostly bright, with some softness present")
    
    # Cool vs Warm
    if traits["cool"] > 0 and traits["warm"] > 0:
        diff = abs(traits["cool"] - traits["warm"])
        if diff <= 2:
            tensions.append("cool vs warm (undertone reads neutral/mixed)")
        elif traits["cool"] > traits["warm"]:
            tensions.append("cool-leaning, but not purely cool")
        else:
            tensions.append("warm-leaning, but not purely warm")
    
    # Contrast
    if traits["contrast_high"] > 0 and traits["contrast_low"] > 0:
        diff = abs(traits["contrast_high"] - traits["contrast_low"])
        if diff <= 2:
            tensions.append("contrast level is ambiguous")
        elif traits["contrast_high"] > traits["contrast_low"]:
            tensions.append("leans high contrast, but not extreme")
        else:
            tensions.append("leans low contrast, but not extreme")
    
    # Light vs Deep
    if traits["light"] > 0 and traits["deep"] > 0:
        diff = abs(traits["light"] - traits["deep"])
        if diff <= 2:
            tensions.append("depth is ambiguous (light vs deep)")
        elif traits["light"] > traits["deep"]:
            tensions.append("leans light, but has some depth")
        else:
            tensions.append("leans deep, but has some lightness")
    
    return tensions


def irl_tests_for(winner, runner, traits):
    """Generate real-life testing suggestions based on trait tensions."""
    tests = []
    
    if abs(traits["contrast_high"] - traits["contrast_low"]) <= 2 or (traits["contrast_high"] > 0 and traits["contrast_low"] > 0):
        tests.append("Test black vs charcoal near your face: if charcoal wins, you're likely in a softer/lower-contrast season.")
    
    if abs(traits["cool"] - traits["warm"]) <= 2 or (traits["cool"] > 0 and traits["warm"] > 0):
        tests.append("Test optic white vs cream: optic usually supports cooler/clearer seasons; cream supports warmer/softer ones.")
        tests.append("Test silver vs gold in daylight photos: which makes your skin look clearer (not gray, not sallow)?")
    
    if abs(traits["soft"] - traits["bright"]) <= 2 or (traits["soft"] > 0 and traits["bright"] > 0):
        tests.append("Test dusty rose/mauve vs coral/hotpink: the winner tells you whether you read soft or bright.")
    
    if abs(traits["light"] - traits["deep"]) <= 2 or (traits["light"] > 0 and traits["deep"] > 0):
        tests.append("Test a light pastel (like powder blue) vs a deep shade (like navy): which makes you look more awake?")
    
    return tests[:3]
