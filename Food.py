import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Calorie Tracker", layout="wide")

HISTORY_FILE = "history.xlsx"

# ---------------- CLASSES ----------------

class FoodItem:
    def __init__(self, name, cal, p, c, f):
        self.name = name
        self.cal = cal
        self.p = p
        self.c = c
        self.f = f


class MealItem:
    def __init__(self, food, grams):
        self.food = food
        self.grams = grams

    def calc(self, value):
        return (value / 100) * self.grams


class Tracker:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def delete(self, i):
        if 0 <= i < len(self.items):
            del self.items[i]

    def clear(self):
        self.items = []

    def totals(self):
        return {
            "cal": sum(i.calc(i.food.cal) for i in self.items),
            "p": sum(i.calc(i.food.p) for i in self.items),
            "c": sum(i.calc(i.food.c) for i in self.items),
            "f": sum(i.calc(i.food.f) for i in self.items),
        }


# ---------------- DATA ----------------

def load_food():
    df = pd.read_excel("Food_Database.xlsx")
    return {
        r["Food Name"]: FoodItem(r["Food Name"], r["Calories"], r["Protein"], r["Carbs"], r["Fat"])
        for _, r in df.iterrows()
    }


def save_history(date, totals):
    new = pd.DataFrame([{
        "Date": date,
        "Calories": totals["cal"],
        "Protein": totals["p"],
        "Carbs": totals["c"],
        "Fat": totals["f"]
    }])

    if os.path.exists(HISTORY_FILE):
        df = pd.concat([pd.read_excel(HISTORY_FILE), new], ignore_index=True)
    else:
        df = new

    df.to_excel(HISTORY_FILE, index=False)


def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_excel(HISTORY_FILE)
    return pd.DataFrame()


# ---------------- STATE ----------------

if "tracker" not in st.session_state:
    st.session_state.tracker = Tracker()

if "food" not in st.session_state:
    st.session_state.food = load_food()

if "goals" not in st.session_state:
    st.session_state.goals = {"cal": 2000, "p": 150, "c": 250, "f": 70}


tracker = st.session_state.tracker
food_db = st.session_state.food
goals = st.session_state.goals


# ---------------- NAV ----------------

st.sidebar.title("🏋️ Fitness App")
page = st.sidebar.radio("Navigate", [
    "🏠 Home",
    "➕ Add Food",
    "📋 Entries",
    "🎯 Goals",
    "📊 Progress",
    "🧁 Macro Chart",
    "📅 History"
])


# ================= HOME =================

if page == "🏠 Home":
    st.title("🏠 Dashboard")

    totals = tracker.totals()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Calories", f"{totals['cal']:.0f}")
    col2.metric("Protein", f"{totals['p']:.0f} g")
    col3.metric("Carbs", f"{totals['c']:.0f} g")
    col4.metric("Fat", f"{totals['f']:.0f} g")

    st.write("### Today's Progress")
    st.progress(min(totals["cal"] / goals["cal"], 1.0))


# ================= ADD =================

elif page == "➕ Add Food":
    st.title("Add Food")

    f = st.selectbox("Food", list(food_db.keys()))
    g = st.number_input("Grams", 1.0, value=100.0)

    if st.button("Add"):
        tracker.add(MealItem(food_db[f], g))
        st.success("Added!")


# ================= ENTRIES =================

elif page == "📋 Entries":
    st.title("Entries")

    if tracker.items:
        data = []
        labels = []

        for i, item in enumerate(tracker.items):
            labels.append(f"{i+1}. {item.food.name} ({item.grams}g)")
            data.append([
                item.food.name,
                item.grams,
                round(item.calc(item.food.cal), 1),
                round(item.calc(item.food.p), 1),
                round(item.calc(item.food.c), 1),
                round(item.calc(item.food.f), 1),
            ])

        df = pd.DataFrame(data, columns=["Food", "Grams", "Cal", "Protein", "Carbs", "Fat"])
        st.dataframe(df, width="stretch")

        sel = st.selectbox("Delete item", labels)
        idx = labels.index(sel)

        if st.button("Delete"):
            tracker.delete(idx)
            st.rerun()

        if st.button("Clear All"):
            tracker.clear()
            st.rerun()

    else:
        st.info("No data")


# ================= GOALS =================

elif page == "🎯 Goals":
    st.title("Set Goals")

    goals["cal"] = st.number_input("Calories", value=goals["cal"])
    goals["p"] = st.number_input("Protein", value=goals["p"])
    goals["c"] = st.number_input("Carbs", value=goals["c"])
    goals["f"] = st.number_input("Fat", value=goals["f"])

    st.success("Goals updated!")


# ================= PROGRESS =================

elif page == "📊 Progress":
    st.title("Progress")

    t = tracker.totals()

    st.write("Calories")
    st.progress(min(t["cal"] / goals["cal"], 1.0))

    st.write("Protein")
    st.progress(min(t["p"] / goals["p"], 1.0))

    st.write("Carbs")
    st.progress(min(t["c"] / goals["c"], 1.0))

    st.write("Fat")
    st.progress(min(t["f"] / goals["f"], 1.0))


# ================= PIE =================

elif page == "🧁 Macro Chart":
    st.title("Macro Split")

    t = tracker.totals()

    # Convert safely & handle NaN
    protein = float(t.get("p", 0) or 0)
    carbs = float(t.get("c", 0) or 0)
    fat = float(t.get("f", 0) or 0)

    values = [protein, carbs, fat]

    # 🚫 Prevent crash if all zero
    if sum(values) == 0:
        st.warning("⚠️ Add food to see macro chart")
    else:
        col1, col2 = st.columns([2, 1])

        with col2:
            fig, ax = plt.subplots(figsize=(3, 3))
            ax.pie(values, autopct="%1.1f%%")
            ax.set_title("Macro Split", fontsize=10)

            st.pyplot(fig)


# ================= HISTORY =================

elif page == "📅 History":
    st.title("History")

    t = tracker.totals()
    d = st.date_input("Date")

    if st.button("Save Day"):
        save_history(d, t)
        st.success("Saved")

    hist = load_history()

    if not hist.empty:
        hist["Date"] = pd.to_datetime(hist["Date"])
        hist = hist.sort_values("Date")
        st.line_chart(hist.set_index("Date")["Calories"])