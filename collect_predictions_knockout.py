import json
import os
from datetime import datetime

DATA_FILE = "predictions_db.json"


# ---------- Load / Save ----------
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"matches": []}


def save_db(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)


# ---------- JSON input ----------
def multi_line_input(prompt):
    print(prompt)
    print("(Paste JSON. Press ENTER twice to submit)\n")

    lines = []
    empty_count = 0

    while True:
        line = input()
        if line.strip() == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
            lines.append(line)

    return "\n".join(lines)


# ---------- Add prediction ----------
def add_prediction(db, home, away, model_name, raw_json):
    try:
        prediction = json.loads(raw_json)
    except Exception as e:
        print("❌ Invalid JSON")
        return

    db["matches"].append({
        "match": f"{home} vs {away}",
        "home": home,
        "away": away,
        "model": model_name,
        "prediction": prediction,
        "actual": None,
        "created_at": datetime.now().isoformat()
    })


# ---------- MAIN ----------
if __name__ == "__main__":
    db = load_db()

    print("\n⚽ World Cup Knockout Session\n")

    while True:
        print("\n============================")
        print("NEW MATCH (ENTER to stop)")
        print("============================")

        home = input("Home team: ")
        if home.strip() == "":
            break

        away = input("Away team: ")
        if away.strip() == "":
            break

        # ---- models loop ----
        while True:
            model_name = input("\nModel name (ENTER to finish match): ")

            if model_name.strip() == "":
                break

            raw_json = multi_line_input(f"\nPaste prediction for {model_name}")

            add_prediction(db, home, away, model_name, raw_json)

            print(f"✅ Saved {model_name} for {home} vs {away}")

    save_db(db)

    print("\n🎯 Session finished and saved!")