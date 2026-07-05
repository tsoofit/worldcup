# ⚽ World Cup Knockout AI Prediction League

![Python](https://img.shields.io/badge/python-3.12-blue)
![Streamlit](https://img.shields.io/badge/streamlit-app-red)
![Status](https://img.shields.io/badge/status-active-success)

A lightweight **AI benchmarking system** for comparing football match predictions from multiple AI models in FIFA World Cup knockout games.

---

## 🚀 Overview

This project lets you:
- Compare multiple AI models (GPT, Claude, etc.)
- Collect structured predictions for knockout matches
- Track accuracy over time
- Visualize results in a Streamlit dashboard

---

## 📊 Features

- 🧠 Multi-model prediction comparison
- ⚽ FIFA World Cup knockout format support
- 📈 Live leaderboard (accuracy tracking)
- 💾 Simple JSON-based storage (no DB required)
- 🎯 Score + winner consistency validation
- 📊 Streamlit interactive dashboard

---

## 📁 Project Structure

```
ai-betting-league/
│
├── collect_predictions_knockout.py   # CLI for entering model predictions
├── app.py                            # Streamlit dashboard
├── predictions_db.json               # Local data store (auto-generated)
└── README.md
```

---

## ▶️ How to Run

### 1. Install dependencies

```bash
py -3.12 -m pip install streamlit pandas
```

Optional (for styled tables):

```bash
py -3.12 -m pip install jinja2
```

---

### 2. Run dashboard

```bash
py -3.12 -m streamlit run app.py
```

Open:
```
http://localhost:8501
```

---

### 3. Add predictions

```bash
py -3.12 -m collect_predictions_knockout.py
```

Enter:
- Home team
- Away team
- Model name
- JSON prediction (from AI model)

---

## 🧾 Prediction Format

```json
{
  "score_90min": "1-1",
  "result_90min": "draw",
  "extra_time_probability": 45,
  "penalty_probability": 30,
  "final_winner": "home",
  "confidence": 78,
  "risk_level": "medium",
  "reasoning": "Balanced knockout match with slight home advantage."
}
```

---

## 🖥️ Dashboard Preview

(Add screenshot here)

```
📌 Tip: run Streamlit locally and take a screenshot of:
- Match table
- Leaderboard
```

---

## 🧠 Key Idea

A human-in-the-loop system for evaluating how different AI models reason about football outcomes.

---

## ⚽ Knockout Logic

- 90-minute prediction
- Extra time probability
- Penalty shootout probability
- Final winner after full match context

---

## 🏆 Future Improvements

- Elo rating system for models
- Automatic prediction validation
- Bracket visualization (World Cup style)
- Real-time match updates
- Confidence calibration scoring

---

## 🛠 Tech Stack

- Python 3.12
- Streamlit
- Pandas
- JSON storage

---

## 👩‍💻 Author

Built for experimenting with AI reasoning quality in structured sports prediction tasks.
