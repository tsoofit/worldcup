import streamlit as st
import json
import os
import pandas as pd

DATA_FILE = "predictions_db.json"


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


def compute_leaderboard(db):
    stats = {}

    for item in db["matches"]:
        actual = item.get("actual")
        if not actual:
            continue

        model = item.get("model", "unknown")
        prediction = item.get("prediction", {})
        predicted_winner = prediction.get("final_winner")

        if model not in stats:
            stats[model] = {
                "Model": model,
                "Correct": 0,
                "Total": 0,
                "Success Rate": 0.0
            }

        stats[model]["Total"] += 1

        if predicted_winner == actual:
            stats[model]["Correct"] += 1

    for model in stats:
        total = stats[model]["Total"]
        correct = stats[model]["Correct"]
        stats[model]["Success Rate"] = round((correct / total) * 100, 1)

    return pd.DataFrame(stats.values())


st.set_page_config(page_title="World Cup Knockout Predictions", layout="wide")

st.title("⚽ World Cup Knockout AI Prediction League")

db = load_db()
unique_matches = get_unique_matches(db)


# ---------- Sidebar: update actual results ----------
st.sidebar.header("Update Actual Result")

if unique_matches:
    match_options = [m["match"] for m in unique_matches]
    selected_match = st.sidebar.selectbox("Match", match_options)

    selected_match_data = next(m for m in unique_matches if m["match"] == selected_match)

    actual_display = st.sidebar.selectbox(
        "Actual winner",
        [
            selected_match_data["home"],
            selected_match_data["away"]
        ]
    )

    actual_value = (
        "home"
        if actual_display == selected_match_data["home"]
        else "away"
    )

    if st.sidebar.button("Save actual result"):
        for item in db["matches"]:
            if item["match"] == selected_match:
                item["actual"] = actual_value

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
        by=["Success Rate", "Correct"],
        ascending=False
    )

    st.dataframe(leaderboard_df, use_container_width=True)

    chart_df = leaderboard_df.set_index("Model")["Success Rate"]
    st.bar_chart(chart_df)
else:
    st.info("No completed matches yet. Update actual results to activate the leaderboard.")


# ---------- Match cards ----------
st.subheader("📋 Predictions by Match")

for match in unique_matches:
    match_name = match["match"]
    home = match["home"]
    away = match["away"]

    match_predictions = [
        item for item in db["matches"]
        if item["match"] == match_name
    ]

    actual_raw = match_predictions[0].get("actual") if match_predictions else None
    actual_display = map_result(actual_raw, home, away) if actual_raw else "Not updated yet"

    with st.container():
        st.markdown(f"## ⚽ {match_name}")
        st.markdown(f"**Actual winner:** {actual_display}")

        rows = []

        for item in match_predictions:
            prediction = item.get("prediction", {})

            model = item.get("model", "unknown")

            result_90 = map_result(
                prediction.get("result_90min"),
                home,
                away
            )

            final_winner = map_result(
                prediction.get("final_winner"),
                home,
                away
            )

            actual = item.get("actual")
            predicted_raw = prediction.get("final_winner")

            if actual:
                status = "✅ Correct" if predicted_raw == actual else "❌ Wrong"
            else:
                status = "⏳ Pending"

            rows.append({
                "Model": model,
                "90min Result": result_90,
                "Score 90min": prediction.get("score_90min"),
                "Extra Time %": prediction.get("extra_time_probability"),
                "Penalties %": prediction.get("penalty_probability"),
                "Final Winner": final_winner,
                "Confidence": prediction.get("confidence"),
                "Risk": prediction.get("risk_level"),
                "Status": status,
                "Reasoning": prediction.get("reasoning")
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        st.divider()


with st.expander("Raw Data"):
    st.json(db)