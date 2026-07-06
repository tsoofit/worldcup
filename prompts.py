def build_prompt(team_a, team_b):
    return f"""
Predict the winner of this football match.

Return ONLY one of:
- {team_a}
- {team_b}
- Draw

No explanation.

Match: {team_a} vs {team_b}
"""
