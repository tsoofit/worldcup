import streamlit as st
import json
import os
import pandas as pd

DATA_FILE = "predictions_db.json"

POINTS = {
    "final_winner": 5,
    "result_90min": 3,
    "exact_score": 5,
    "extra_time": 2,
    "penalties": 2,
}

MAX_POINTS = sum(POINTS.values())


def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"matches": []}


def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def map_result(value, home, away):
    if value == "home":
        return home
    if value == "away":
        return away
    if value == "draw":
        return "Draw"
    return ""


def infer_90_result(score):
    try:
        home_goals, away_goals = map(int, score.replace(":", "-").split("-"))
        if home_goals > away_goals:
            return "home"
        if away_goals > home_goals:
            return "away"
        return "draw"
    except Exception:
        return None


def predicted_extra_time(prediction):
    return prediction.get("result_90min") == "draw"


def predicted_penalties(prediction):
    return prediction.get("penalty_probability", 0) >= 50


def get_unique_matches(db):
    matches = {}
    for item in db["matches"]:
        key = item["match"]
        if key not in matches:
            matches[key] = {
                "match": item["match"],
                "home": item["home"],
                "away": item["away"]
            }
    return list(matches.values())


def score_prediction(prediction, actual):
    score = 0

    if prediction.get("final_winner") == actual.get("final_winner"):
        score += POINTS["final_winner"]

    if prediction.get("result_90min") == actual.get("result_90min"):
        score += POINTS["result_90min"]

    if prediction.get("score_90min") == actual.get("score_90min"):
        score += POINTS["exact_score"]

    if predicted_extra_time(prediction) == actual.get("went_extra_time"):
        score += POINTS["extra_time"]

    if predicted_penalties(prediction) == actual.get("went_penalties"):
        score += POINTS["penalties"]

    return score


def compute_leaderboard(db):
    stats = {}

    for item in db["matches"]:
        actual = item.get("actual")

        if not isinstance(actual, dict):
            continue

        model = item.get("model", "unknown")
        prediction = item.get("prediction", {})

        if model not in stats:
            stats[model] = {
                "Model": model,
                "Points": 0,
                "Max Points": 0,
                "Matches": 0,
                "Success Rate": 0.0
            }

        earned = score_prediction(prediction, actual)

        stats[model]["Points"] += earned
        stats[model]["Max Points"] += MAX_POINTS
        stats[model]["Matches"] += 1

    for model in stats:
        stats[model]["Success Rate"] = round(
            stats[model]["Points"] / stats[model]["Max Points"] * 100,
            1
        )

    return pd.DataFrame(stats.values())


st.set_page_config(page_title="World Cup Knockout Predictions", layout="wide")
st.title("⚽ World Cup Knockout AI Prediction League")

db = load_db()
unique_matches = get_unique_matches(db)


# ---------- Sidebar: actual result ----------
st.sidebar.header("Update Actual Result")

if unique_matches:
    match_options = [m["match"] for m in unique_matches]
    selected_match = st.sidebar.selectbox("Match", match_options)

    selected_match_data = next(m for m in unique_matches if m["match"] == selected_match)
    home = selected_match_data["home"]
    away = selected_match_data["away"]

    actual_score = st.sidebar.text_input("Actual 90min score", placeholder="1-1")

    actual_90_result = infer_90_result(actual_score) if actual_score else None

    final_winner_display = st.sidebar.selectbox(
        "Final winner",
        [home, away]
    )

    final_winner = "home" if final_winner_display == home else "away"

    went_extra_time = st.sidebar.checkbox("Went to extra time")
    went_penalties = st.sidebar.checkbox("Went to penalties")

    if st.sidebar.button("Save actual result"):
        if not actual_score or actual_90_result is None:
            st.sidebar.error("Please enter a valid 90min score, like 1-1 or 2-0.")
        else:
            actual_data = {
                "score_90min": actual_score.replace(":", "-"),
                "result_90min": actual_90_result,
                "final_winner": final_winner,
                "went_extra_time": went_extra_time,
                "went_penalties": went_penalties
            }

            for item in db["matches"]:
                if item["match"] == selected_match:
                    item["actual"] = actual_data

            save_db(db)
            st.success("Actual result saved.")
            st.rerun()
else:
    st.info("No predictions yet.")


# ---------- Leaderboard ----------
st.subheader("🏆 Model Leaderboard")

leaderboard_df = compute_leaderboard(db)

if not leaderboard_df.empty:
    leaderboard_df = leaderboard_df.sort_values(
        by=["Success Rate", "Points"],
        ascending=False
    )

    st.dataframe(leaderboard_df, use_container_width=True)
    st.bar_chart(leaderboard_df.set_index("Model")["Success Rate"])
else:
    st.info("No completed matches yet. Update actual results to activate the leaderboard.")


# ---------- Match predictions ----------
st.subheader("📋 Predictions by Match")

for match in unique_matches:
    match_name = match["match"]
    home = match["home"]
    away = match["away"]

    match_predictions = [
        item for item in db["matches"]
        if item["match"] == match_name
    ]

    actual = match_predictions[0].get("actual") if match_predictions else None

    st.markdown(f"## ⚽ {match_name}")

    if isinstance(actual, dict):
        st.markdown(
            f"""
            **Actual 90min score:** {actual["score_90min"]}  
            **Actual 90min result:** {map_result(actual["result_90min"], home, away)}  
            **Final winner:** {map_result(actual["final_winner"], home, away)}  
            **Extra time:** {"Yes" if actual["went_extra_time"] else "No"}  
            **Penalties:** {"Yes" if actual["went_penalties"] else "No"}
            """
        )
    else:
        st.markdown("**Actual result:** Not updated yet")

    rows = []

    for item in match_predictions:
        prediction = item.get("prediction", {})
        actual = item.get("actual")

        points = ""
        status = "⏳ Pending"

        if isinstance(actual, dict):
            earned = score_prediction(prediction, actual)
            points = f"{earned}/{MAX_POINTS}"
            status = "✅" if earned == MAX_POINTS else "🟡" if earned > 0 else "❌"

        rows.append({
            "Model": item.get("model", "unknown"),
            "90min Result": map_result(prediction.get("result_90min"), home, away),
            "Score 90min": prediction.get("score_90min"),
            "Extra Time %": prediction.get("extra_time_probability"),
            "Penalties %": prediction.get("penalty_probability"),
            "Final Winner": map_result(prediction.get("final_winner"), home, away),
            "Confidence": prediction.get("confidence"),
            "Risk": prediction.get("risk_level"),
            "Points": points,
            "Status": status,
            "Reasoning": prediction.get("reasoning")
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    st.divider()


with st.expander("Raw Data"):
    st.json(db)