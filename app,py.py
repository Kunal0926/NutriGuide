import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ---------------------------------
# PAGE SETTINGS
# ---------------------------------

st.set_page_config(
    page_title="NutriGuide",
    page_icon="🥗",
    layout="wide"
)

st.title("🥗 NutriGuide")
st.subheader("Personalized Indian Diet Planner")

st.info(
    "This educational prototype provides approximate nutrition "
    "estimates for generally healthy adults aged 18–65. "
    "It is not a medical diet prescription."
)

# ---------------------------------
# FOOD DATABASE
# name, serving grams, kcal, protein,
# diet category, allergens, cost (INR)
#
# Illustrative estimates per prepared serving.
# ---------------------------------

FOODS = {
    "Breakfast": [
        ("Poha", 180, 260, 6, "Vegan", [], 25),
        ("Idli and sambar", 250, 280, 10, "Vegan", [], 35),
        ("Besan chilla", 180, 290, 13, "Vegan", [], 30),
        ("Paneer sandwich", 180, 340, 16,
         "Vegetarian", ["Dairy", "Gluten"], 55),
        ("Eggs and toast", 180, 320, 19,
         "Non-vegetarian", ["Eggs", "Gluten"], 45),
        ("Sprout salad", 200, 230, 13, "Vegan", [], 30),
    ],

    "Lunch": [
        ("Dal rice and sabzi", 350, 480, 16, "Vegan", [], 65),
        ("Rajma rice", 350, 490, 17, "Vegan", [], 65),
        ("Chole rice", 350, 510, 17, "Vegan", [], 65),
        ("Paneer rice", 350, 550, 24,
         "Vegetarian", ["Dairy"], 95),
        ("Chicken rice", 350, 540, 34,
         "Non-vegetarian", [], 110),
        ("Tofu rice", 350, 470, 21,
         "Vegan", ["Soy"], 85),
    ],

    "Snack": [
        ("Banana", 120, 105, 1.3, "Vegan", [], 10),
        ("Roasted chana", 40, 150, 8, "Vegan", [], 15),
        ("Seasonal fruit", 150, 90, 1, "Vegan", [], 20),
        ("Plain curd", 150, 100, 6,
         "Vegetarian", ["Dairy"], 25),
        ("Peanuts", 30, 170, 7,
         "Vegan", ["Peanuts"], 15),
        ("Boiled eggs", 100, 155, 13,
         "Non-vegetarian", ["Eggs"], 25),
    ],

    "Dinner": [
        ("Moong dal khichdi", 350, 420, 15, "Vegan", [], 55),
        ("Dal rice and sabzi", 350, 480, 16, "Vegan", [], 65),
        ("Chickpea curry and rice", 350, 490, 17,
         "Vegan", [], 65),
        ("Paneer bhurji and rice", 350, 510, 25,
         "Vegetarian", ["Dairy"], 90),
        ("Chicken curry and rice", 350, 550, 33,
         "Non-vegetarian", [], 110),
        ("Egg curry and rice", 350, 510, 22,
         "Non-vegetarian", ["Eggs"], 75),
    ],
}

# ---------------------------------
# USER DETAILS
# ---------------------------------

st.header("1. Enter Your Details")

with st.form("nutrition_form"):

    col1, col2 = st.columns(2)

    with col1:

        age = st.number_input(
            "Age (years)",
            min_value=18,
            max_value=65,
            value=25
        )

        gender = st.selectbox(
            "Calorie calculation formula",
            ["Male", "Female", "Prefer not to say"]
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=25.0,
            max_value=250.0,
            value=70.0
        )

    with col2:

        height_option = st.radio(
            "Height measurement",
            ["Centimeters (cm)", "Feet and Inches"]
        )

        if height_option == "Centimeters (cm)":

            height_cm = st.number_input(
                "Height in cm",
                min_value=100.0,
                max_value=230.0,
                value=170.0,
                step=0.5
            )

            total_inches = height_cm / 2.54

            ft = int(total_inches // 12)
            inch = total_inches % 12

            st.caption(
                f"Equivalent: {ft} feet {inch:.1f} inches"
            )

        else:

            feet = st.number_input(
                "Feet",
                min_value=3,
                max_value=7,
                value=5
            )

            inches = st.number_input(
                "Additional inches",
                min_value=0.0,
                max_value=11.9,
                value=7.0,
                step=0.1
            )

            height_cm = (feet * 12 + inches) * 2.54

            st.caption(
                f"Equivalent: {height_cm:.1f} cm"
            )

    activity = st.selectbox(
        "Daily Activity Level",
        [
            "Sedentary",
            "Lightly Active",
            "Moderately Active",
            "Very Active"
        ]
    )

    goal = st.selectbox(
        "Your Goal",
        [
            "Maintain Weight",
            "Gradual Weight Loss",
            "Gradual Weight Gain"
        ]
    )

    diet = st.selectbox(
        "Food Preference",
        ["Vegetarian", "Non-vegetarian", "Vegan"]
    )

    budget = st.selectbox(
        "Daily Food Budget",
        [
            "Under Rs. 150",
            "Rs. 150 - 250",
            "Flexible"
        ]
    )

    allergies = st.multiselect(
        "Ingredients to Avoid",
        ["Dairy", "Eggs", "Peanuts", "Soy", "Gluten"]
    )

    st.caption(
        "This demo cannot verify cross-contact, hidden allergens "
        "or every ingredient in prepared food. Do not use it as "
        "a safety check for severe food allergies."
    )

    submit = st.form_submit_button(
        "Generate My Diet Plan",
        use_container_width=True
    )

# ---------------------------------
# NUTRITION CALCULATIONS
# ---------------------------------

if submit:

    if not 100 <= height_cm <= 230:
        st.error("Please enter a valid height.")
        st.stop()

    bmi = weight / ((height_cm / 100) ** 2)

    constants = {
        "Male": 5,
        "Female": -161,
        "Prefer not to say": -78
    }

    # Mifflin-St Jeor BMR estimate
    bmr = (
        10 * weight
        + 6.25 * height_cm
        - 5 * age
        + constants[gender]
    )

    activity_factors = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725
    }

    maintenance = bmr * activity_factors[activity]

    adjustments = {
        "Maintain Weight": 0,
        "Gradual Weight Loss": -300,
        "Gradual Weight Gain": 200
    }

    target = maintenance + adjustments[goal]

    if target < 1500:
        st.warning(
            "Your calculated target falls below the demo's "
            "1500 kcal planning floor. Please consult a "
            "qualified dietitian for individualized advice."
        )
        target = 1500

    st.divider()
    st.header("2. Your Estimated Nutrition Results")

    a, b, c = st.columns(3)

    a.metric("BMI", f"{bmi:.1f}")
    b.metric("Maintenance", f"{maintenance:.0f} kcal")
    c.metric("Planning Target", f"{target:.0f} kcal")

    st.caption(
        "These are approximate population-based calculations. "
        "The unspecified formula option uses a midpoint constant "
        "that is not individually validated. BMI is not a diagnosis."
    )

    # ---------------------------------
    # FILTER FOODS
    # ---------------------------------

    def allowed(food):

        name, grams, kcal, protein, category, tags, cost = food

        if diet == "Vegan" and category != "Vegan":
            return False

        if diet == "Vegetarian" and category == "Non-vegetarian":
            return False

        if any(tag in allergies for tag in tags):
            return False

        return True

    available = {
        meal: [food for food in items if allowed(food)]
        for meal, items in FOODS.items()
    }

    if any(not items for items in available.values()):
        st.error(
            "No suitable food is available for one or more meals. "
            "Expand the food database before continuing."
        )
        st.stop()

    # ---------------------------------
    # GENERATE SEVEN-DAY PLAN
    # ---------------------------------

    days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    allocation = {
        "Breakfast": 0.25,
        "Lunch": 0.35,
        "Snack": 0.10,
        "Dinner": 0.30
    }

    budget_limit = {
        "Under Rs. 150": 150,
        "Rs. 150 - 250": 250,
        "Flexible": float("inf")
    }[budget]

    rows = []
    summaries = []

    for day_index, day in enumerate(days):

        daily_rows = []

        for meal, options in available.items():

            desired_kcal = target * allocation[meal]

            candidates = []

            for food in options:

                name, grams, kcal, protein, category, tags, cost = food

                # Scale an example serving, within demo limits.
                factor = max(
                    0.75,
                    min(desired_kcal / kcal, 1.75)
                )

                portion = round(grams * factor)
                calories = round(kcal * factor)
                protein_amount = round(protein * factor, 1)
                price = round(cost * factor)

                # Rotate the candidate order to encourage variety.
                candidates.append({
                    "Day": day,
                    "Meal": meal,
                    "Food": name,
                    "Quantity (g)": portion,
                    "Calories (kcal)": calories,
                    "Protein (g)": protein_amount,
                    "Cost (Rs)": price,
                    "Calorie difference": abs(calories - desired_kcal)
                })

            candidates.sort(
                key=lambda x: (
                    x["Calorie difference"],
                    x["Cost (Rs)"]
                )
            )

            # Rotate among reasonably close candidates.
            best_difference = candidates[0]["Calorie difference"]

            close = [
                item for item in candidates
                if item["Calorie difference"] <= best_difference + 80
            ]

            # Budget-sensitive ranking.
            if budget != "Flexible":
                close.sort(key=lambda x: x["Cost (Rs)"])

            selected = close[day_index % len(close)]

            daily_rows.append(selected)

        rows.extend(daily_rows)

        total_calories = sum(
            x["Calories (kcal)"] for x in daily_rows
        )

        total_protein = sum(
            x["Protein (g)"] for x in daily_rows
        )

        total_cost = sum(
            x["Cost (Rs)"] for x in daily_rows
        )

        summaries.append({
            "Day": day,
            "Calories (kcal)": total_calories,
            "Protein (g)": round(total_protein, 1),
            "Estimated Cost (Rs)": total_cost,
            "Within Budget": (
                "Yes" if total_cost <= budget_limit else "No"
            )
        })

    df = pd.DataFrame(rows)
    summary = pd.DataFrame(summaries)

    df = df.drop(columns=["Calorie difference"])

    # ---------------------------------
    # SHOW RESULTS
    # ---------------------------------

    st.divider()
    st.header("3. Your Seven-Day Indian Diet Plan")

    selected_day = st.selectbox(
        "Choose a Day",
        days
    )

    day_data = df[df["Day"] == selected_day]

    st.dataframe(
        day_data.drop(columns=["Day"]),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Weekly Summary")

    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True
    )

    if (summary["Within Budget"] == "No").any():
        st.warning(
            "Some days exceed your selected budget. "
            "The current food database cannot guarantee "
            "a meal plan within every budget."
        )

    st.caption(
        "Food quantities, nutrient values and prices are estimates. "
        "The generated plan is not verified for complete protein, "
        "vitamin, mineral or other nutritional requirements."
    )

    st.subheader("Daily Calorie Comparison")

    st.bar_chart(
        summary.set_index("Day")["Calories (kcal)"]
    )

    # ---------------------------------
    # PDF DOWNLOAD
    # ---------------------------------

    def generate_pdf():

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=(595, 842),
            rightMargin=35,
            leftMargin=35
        )

        styles = getSampleStyleSheet()

        content = [
            Paragraph(
                "NutriGuide - Seven-Day Diet Plan",
                styles["Title"]
            ),
            Spacer(1, 12),
            Paragraph(
                f"Age: {age} | Weight: {weight} kg | "
                f"Height: {height_cm:.1f} cm",
                styles["Normal"]
            ),
            Paragraph(
                f"Goal: {goal} | Diet: {diet}",
                styles["Normal"]
            ),
            Paragraph(
                f"Estimated planning target: {target:.0f} kcal/day",
                styles["Normal"]
            ),
            Spacer(1, 15)
        ]

        for day in days:

            content.append(
                Paragraph(day, styles["Heading2"])
            )

            table_data = [[
                "Meal", "Food", "Grams", "Kcal", "Protein"
            ]]

            day_records = df[df["Day"] == day]

            for _, item in day_records.iterrows():

                table_data.append([
                    item["Meal"],
                    Paragraph(str(item["Food"]), styles["Normal"]),
                    str(item["Quantity (g)"]),
                    str(item["Calories (kcal)"]),
                    str(item["Protein (g)"])
                ])

            table = Table(
                table_data,
                colWidths=[80, 180, 65, 65, 65],
                repeatRows=1
            )

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))

            content.append(table)
            content.append(Spacer(1, 15))

        content.append(
            Paragraph(
                "Educational estimates only. Not a medical "
                "prescription. Nutrition, ingredients and "
                "allergen safety require independent verification.",
                styles["Normal"]
            )
        )

        doc.build(content)

        buffer.seek(0)

        return buffer.getvalue()

    st.divider()
    st.header("4. Download Your Diet Plan")

    st.download_button(
        "Download Diet Plan as PDF",
        data=generate_pdf(),
        file_name="NutriGuide_Diet_Plan.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.success("Your sample diet plan is ready!")