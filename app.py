import streamlit as st
import json
import os
import pandas as pd
import hmac
import altair as alt

DATA_FILE = "predictions_db.json"

POINTS = {
    "final_winner": 5,
    "result_90min": 3,
    "exact_score": 5,
    "extra_time": 2,
    "penalties": 2,
}

MAX_POINTS = sum(POINTS.values())

# --------------------------------------------------
# DATA
# --------------------------------------------------

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"matches": []}


def save_db(db):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

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
        home_goals, away_goals = map(
            int,
            score.replace(":", "-").split("-")
        )

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


def is_human(model_name):
    human_names = [
        "human",
        "tsoofit"
    ]

    return model_name.lower().strip() in human_names


def match_has_actual(db, match_name):
    match_predictions = [
        item
        for item in db["matches"]
        if item["match"] == match_name
    ]

    return (
        bool(match_predictions)
        and isinstance(
            match_predictions[0].get("actual"),
            dict
        )
    )


# --------------------------------------------------
# SCORING
# --------------------------------------------------

def score_prediction(prediction, actual):
    score = 0

    if (
        prediction.get("final_winner")
        == actual.get("final_winner")
    ):
        score += POINTS["final_winner"]

    if (
        prediction.get("result_90min")
        == actual.get("result_90min")
    ):
        score += POINTS["result_90min"]

    if (
        prediction.get("score_90min")
        == actual.get("score_90min")
    ):
        score += POINTS["exact_score"]

    if (
        predicted_extra_time(prediction)
        == actual.get("went_extra_time")
    ):
        score += POINTS["extra_time"]

    if (
        predicted_penalties(prediction)
        == actual.get("went_penalties")
    ):
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
                "Model":
                (
                    "15y old teenager"
                    if is_human(model)
                    else model
                ),
                "Type": (
                    "👤 Human"
                    if is_human(model)
                    else "🤖 AI"
                ),
                "Points": 0,
                "Max Points": 0,
                "Matches": 0,
                "Success Rate": 0.0
            }

        earned = score_prediction(
            prediction,
            actual
        )

        stats[model]["Points"] += earned
        stats[model]["Max Points"] += MAX_POINTS
        stats[model]["Matches"] += 1

    for model in stats:

        stats[model]["Success Rate"] = round(
            stats[model]["Points"]
            / stats[model]["Max Points"]
            * 100,
            1
        )

    return pd.DataFrame(stats.values())


# --------------------------------------------------
# ADMIN AUTH
# --------------------------------------------------

def check_admin_password(password):
    try:
        expected_password = st.secrets[
            "ADMIN_PASSWORD"
        ]

    except Exception:
        return False

    return hmac.compare_digest(
        str(password).strip(),
        str(expected_password).strip()
    )


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="World Cup Knockout Predictions",
    page_icon="⚽",
    layout="wide"
)

st.title(
    "⚽ World Cup Knockout AI Prediction League"
)

st.caption(
    "AI models vs human prediction benchmark"
)

db = load_db()

unique_matches = get_unique_matches(db)


# --------------------------------------------------
# ADMIN LOGIN
# --------------------------------------------------

st.sidebar.header("🔐 Admin")

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


if not st.session_state.admin_authenticated:

    admin_password = st.sidebar.text_input(
        "Admin password",
        type="password"
    )

    if st.sidebar.button("Login"):

        if check_admin_password(
            admin_password
        ):

            st.session_state.admin_authenticated = True

            st.rerun()

        else:

            st.sidebar.error(
                "Incorrect password"
            )


else:

    st.sidebar.success(
        "Admin mode enabled"
    )

    if st.sidebar.button("Logout"):

        st.session_state.admin_authenticated = False

        st.rerun()


# --------------------------------------------------
# ADMIN RESULT UPDATE
# --------------------------------------------------

if st.session_state.admin_authenticated:

    st.sidebar.divider()

    st.sidebar.header(
        "Update Actual Result"
    )

    if unique_matches:

        match_options = [
            match["match"]
            for match in unique_matches
        ]

        selected_match = st.sidebar.selectbox(
            "Match",
            match_options
        )

        selected_match_data = next(
            match
            for match in unique_matches
            if match["match"] == selected_match
        )

        home = selected_match_data["home"]
        away = selected_match_data["away"]

        actual_score = st.sidebar.text_input(
            "Actual 90min score",
            placeholder="1-1"
        )

        actual_90_result = (
            infer_90_result(actual_score)
            if actual_score
            else None
        )

        final_winner_display = st.sidebar.selectbox(
            "Final winner",
            [
                home,
                away
            ]
        )

        final_winner = (
            "home"
            if final_winner_display == home
            else "away"
        )

        went_extra_time = st.sidebar.checkbox(
            "Went to extra time"
        )

        went_penalties = st.sidebar.checkbox(
            "Went to penalties"
        )

        if st.sidebar.button(
            "Save actual result"
        ):

            if (
                not actual_score
                or actual_90_result is None
            ):

                st.sidebar.error(
                    "Enter a valid score such as "
                    "1-1 or 2-0."
                )

            else:

                actual_data = {
                    "score_90min":
                        actual_score.replace(
                            ":",
                            "-"
                        ),

                    "result_90min":
                        actual_90_result,

                    "final_winner":
                        final_winner,

                    "went_extra_time":
                        went_extra_time,

                    "went_penalties":
                        went_penalties
                }

                for item in db["matches"]:

                    if (
                        item["match"]
                        == selected_match
                    ):

                        item["actual"] = (
                            actual_data
                        )

                save_db(db)

                st.sidebar.success(
                    "Result saved!"
                )

                st.rerun()


# --------------------------------------------------
# LEADERBOARD
# --------------------------------------------------

st.subheader(
    "🏆 Prediction Leaderboard"
)

leaderboard_df = compute_leaderboard(db)

if not leaderboard_df.empty:

    leaderboard_df = (
        leaderboard_df.sort_values(
            by=[
                "Success Rate",
                "Points"
            ],
            ascending=False
        )
    )

    leaderboard_df.insert(
        0,
        "Rank",
        range(
            1,
            len(leaderboard_df) + 1
        )
    )

    st.dataframe(
        leaderboard_df,
        use_container_width=True,
        hide_index=True
    )

    chart_df = (
        leaderboard_df
        .set_index("Model")[
            "Success Rate"
        ]
    )

    chart = (
    alt.Chart(leaderboard_df)
    .mark_bar()
    .encode(
        x=alt.X("Success Rate:Q", title="Success Rate (%)"),
        y=alt.Y("Model:N", sort="-x"),
        color=alt.Color("Model:N", legend=None),
        tooltip=["Model", "Type", "Points", "Max Points", "Matches", "Success Rate"]
    )
    )
    st.altair_chart(chart, use_container_width=True)

else:

    st.info(
        "No completed matches yet. "
        "Actual results must be entered "
        "before the leaderboard is calculated."
    )


# --------------------------------------------------
# SPLIT MATCHES
# --------------------------------------------------
completed_matches = [
    match
    for match in unique_matches
    if match_has_actual(db, match["match"])
]

pending_matches = [
    match
    for match in unique_matches
    if not match_has_actual(db, match["match"])
]

# Show newest matches first
completed_matches = list(reversed(completed_matches))
pending_matches = list(reversed(pending_matches))

# --------------------------------------------------
# RENDER MATCH
# --------------------------------------------------

def render_match(match):

    match_name = match["match"]

    home = match["home"]

    away = match["away"]

    match_predictions = [
        item
        for item in db["matches"]
        if item["match"] == match_name
    ]

    actual = (
        match_predictions[0].get("actual")
        if match_predictions
        else None
    )

    st.markdown(
        f"### ⚽ {match_name}"
    )

    # ACTUAL RESULT

    if isinstance(actual, dict):

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "90 Min Score",
                actual["score_90min"]
            )

        with col2:

            st.metric(
                "Final Winner",
                map_result(
                    actual["final_winner"],
                    home,
                    away
                )
            )

        with col3:

            match_end = "90 Minutes"

            if actual["went_penalties"]:

                match_end = "Penalties"

            elif actual["went_extra_time"]:

                match_end = "Extra Time"

            st.metric(
                "Match Ended",
                match_end
            )

    else:

        st.info(
            "Actual result not updated yet"
        )


    # PREDICTIONS TABLE

    rows = []

    for item in match_predictions:

        prediction = item.get(
            "prediction",
            {}
        )

        actual = item.get(
            "actual"
        )

        model = item.get(
            "model",
            "unknown"
        )

        points = ""
        status = "⏳ Pending"
        is_match_winner = False

        if isinstance(actual, dict):
            earned = score_prediction(prediction, actual)
            points = f"{earned}/{MAX_POINTS}"

            match_max_score = max(
                score_prediction(i.get("prediction", {}), actual)
                for i in match_predictions
            )

            is_match_winner = earned == match_max_score and earned > 0

            if is_match_winner:
                status = "🥇 Match Winner"
            elif earned == MAX_POINTS:
                status = "🏆 Perfect"
            elif earned >= 10:
                status = "✅ Good"
            elif earned > 0:
                status = "🟡 Partial"
            else:
                status = "❌ Miss"

        rows.append({

            "Type":
                (
                    "👤 Human"
                    if is_human(model)
                    else "🤖 AI"
                ),

            "Model":
                (
                    f"🥇 {'15y old teenager' if is_human(model) else model}"
                    if is_match_winner
                    else (
                        "15y old teenager"
                        if is_human(model)
                        else model
                    )
                ),
            "90min Result":
                map_result(
                    prediction.get(
                        "result_90min"
                    ),
                    home,
                    away
                ),

            "Score":
                prediction.get(
                    "score_90min"
                ),

            "Extra Time %":
                prediction.get(
                    "extra_time_probability"
                ),

            "Penalties %":
                prediction.get(
                    "penalty_probability"
                ),

            "Final Winner":
                map_result(
                    prediction.get(
                        "final_winner"
                    ),
                    home,
                    away
                ),

            "Confidence":
                prediction.get(
                    "confidence"
                ),

            "Risk":
                prediction.get(
                    "risk_level"
                ),

            "Points":
                points,

            "Status":
                status,

            "Reasoning":
                prediction.get(
                    "reasoning"
                )
        })


    prediction_df = pd.DataFrame(
        rows
    )

    def highlight_match_winner(row):
        if row["Status"] == "🥇 Match Winner":
            return ["font-weight: bold" for _ in row]
        return ["" for _ in row]

    styled_prediction_df = prediction_df.style.apply(
        highlight_match_winner,
        axis=1
    )

    st.dataframe(
        styled_prediction_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()


# --------------------------------------------------
# UPCOMING MATCHES
# --------------------------------------------------

st.markdown(
    "## ⏳ Upcoming / Pending Matches"
)

if pending_matches:

    for match in pending_matches:

        render_match(
            match
        )

else:

    st.success(
        "No pending matches."
    )


# --------------------------------------------------
# COMPLETED MATCHES
# --------------------------------------------------

st.markdown(
    "## ✅ Completed Matches"
)

if completed_matches:

    for match in completed_matches:

        render_match(
            match
        )

else:

    st.info(
        "No completed matches yet."
    )


# --------------------------------------------------
# RAW DATA - ADMIN ONLY
# --------------------------------------------------

if st.session_state.admin_authenticated:

    with st.expander(
        "Raw Data"
    ):

        st.json(
            db
        )