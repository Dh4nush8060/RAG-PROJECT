"""Tools layer for generating charts data, diet plans, and health insights."""
import json


def generate_chart_data(test_results):
    """Generate chart data for visualization."""
    if not test_results:
        return {}

    charts = {}

    # Group by category
    categories = {}
    for test in test_results:
        cat = test.get("category", "General")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(test)

    # Bar chart: All test values vs reference range
    charts["lab_values"] = {
        "type": "bar",
        "title": "Your Lab Values vs Normal Range",
        "labels": [t["name"] for t in test_results[:15]],
        "datasets": [
            {
                "label": "Your Value",
                "data": [t["value"] for t in test_results[:15]],
                "backgroundColor": [
                    "rgba(76, 175, 80, 0.7)" if t["status"] == "Normal"
                    else "rgba(255, 152, 0, 0.7)" if t["status"] == "High"
                    else "rgba(244, 67, 54, 0.7)"
                    for t in test_results[:15]
                ],
                "borderColor": [
                    "rgba(76, 175, 80, 1)" if t["status"] == "Normal"
                    else "rgba(255, 152, 0, 1)" if t["status"] == "High"
                    else "rgba(244, 67, 54, 1)"
                    for t in test_results[:15]
                ],
                "borderWidth": 2
            },
            {
                "label": "Reference High",
                "data": [t.get("ref_high", 0) for t in test_results[:15]],
                "type": "line",
                "borderColor": "rgba(33, 150, 243, 0.8)",
                "borderDash": [5, 5],
                "fill": False,
                "pointRadius": 4
            }
        ]
    }

    # Donut chart: Status distribution
    normal_count = sum(1 for t in test_results if t["status"] == "Normal")
    high_count = sum(1 for t in test_results if t["status"] == "High")
    low_count = sum(1 for t in test_results if t["status"] == "Low")
    unknown_count = sum(1 for t in test_results if t["status"] == "Unknown")

    charts["status_distribution"] = {
        "type": "doughnut",
        "title": "Results Overview",
        "labels": ["Normal", "High", "Low", "Unknown"],
        "datasets": [{
            "data": [normal_count, high_count, low_count, unknown_count],
            "backgroundColor": [
                "rgba(76, 175, 80, 0.8)",
                "rgba(255, 152, 0, 0.8)",
                "rgba(244, 67, 54, 0.8)",
                "rgba(158, 158, 158, 0.8)"
            ],
            "borderWidth": 0
        }]
    }

    # Category breakdown
    charts["categories"] = {
        "type": "radar",
        "title": "Health Categories",
        "labels": list(categories.keys()),
        "datasets": [{
            "label": "Normal %",
            "data": [
                round(sum(1 for t in tests if t["status"] == "Normal") / len(tests) * 100)
                for tests in categories.values()
            ],
            "backgroundColor": "rgba(76, 175, 80, 0.2)",
            "borderColor": "rgba(76, 175, 80, 1)",
            "pointBackgroundColor": "rgba(76, 175, 80, 1)"
        }]
    }

    return charts


def generate_diet_plan(test_results):
    """Generate diet recommendations based on lab values."""
    diet = {
        "title": "Personalized Diet Recommendations",
        "recommendations": [],
        "foods_to_include": [],
        "foods_to_avoid": [],
        "meal_plan": {}
    }

    abnormal_tests = {t["name"]: t for t in test_results if t["status"] != "Normal"}

    # General healthy eating recommendation
    diet["recommendations"].append({
        "icon": "💧",
        "title": "Stay Hydrated",
        "description": "Drink 8-10 glasses of water daily"
    })

    # Specific recommendations based on abnormal values
    if "Total Cholesterol" in abnormal_tests or "LDL Cholesterol" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "🫒",
            "title": "Heart-Healthy Fats",
            "description": "Switch to olive oil, eat fatty fish 2-3 times/week, add nuts and avocados"
        })
        diet["foods_to_include"].extend(["Oats", "Almonds", "Salmon", "Olive Oil", "Avocado"])
        diet["foods_to_avoid"].extend(["Fried foods", "Processed meats", "Full-fat dairy", "Trans fats"])

    if "Blood Glucose Fasting" in abnormal_tests or "HbA1c" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "🥗",
            "title": "Blood Sugar Management",
            "description": "Choose low glycemic index foods, eat smaller frequent meals, avoid sugary drinks"
        })
        diet["foods_to_include"].extend(["Brown rice", "Whole wheat", "Leafy greens", "Cinnamon", "Legumes"])
        diet["foods_to_avoid"].extend(["White bread", "Sugary drinks", "Sweets", "White rice"])

    if "Hemoglobin" in abnormal_tests:
        hb = abnormal_tests["Hemoglobin"]
        if hb["status"] == "Low":
            diet["recommendations"].append({
                "icon": "🥩",
                "title": "Iron-Rich Diet",
                "description": "Increase iron intake with lean meats, spinach, and lentils. Pair with Vitamin C for better absorption."
            })
            diet["foods_to_include"].extend(["Spinach", "Lentils", "Pomegranate", "Beetroot", "Dates"])

    if "Creatinine" in abnormal_tests or "Blood Urea" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "🥬",
            "title": "Kidney-Friendly Diet",
            "description": "Moderate protein intake, reduce sodium, stay well hydrated"
        })
        diet["foods_to_include"].extend(["Cauliflower", "Blueberries", "Red peppers", "Cabbage"])
        diet["foods_to_avoid"].extend(["Excess salt", "Processed foods", "Excess protein"])

    if "SGOT" in abnormal_tests or "SGPT" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "🫐",
            "title": "Liver Support",
            "description": "Eat antioxidant-rich foods, avoid alcohol, reduce fatty foods"
        })
        diet["foods_to_include"].extend(["Green tea", "Turmeric", "Garlic", "Cruciferous vegetables"])
        diet["foods_to_avoid"].extend(["Alcohol", "Refined sugar", "Processed foods"])

    if "Uric Acid" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "🍒",
            "title": "Low Purine Diet",
            "description": "Reduce purine-rich foods, drink plenty of water, eat cherries"
        })
        diet["foods_to_include"].extend(["Cherries", "Low-fat dairy", "Vegetables", "Whole grains"])
        diet["foods_to_avoid"].extend(["Red meat", "Organ meats", "Shellfish", "Beer"])

    if "Vitamin D" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "☀️",
            "title": "Vitamin D Boost",
            "description": "Get 15-20 mins of morning sunlight, eat fortified foods"
        })
        diet["foods_to_include"].extend(["Egg yolks", "Mushrooms", "Fortified milk", "Fatty fish"])

    if "TSH" in abnormal_tests:
        diet["recommendations"].append({
            "icon": "🥜",
            "title": "Thyroid Support",
            "description": "Include selenium and iodine rich foods, avoid excess soy"
        })
        diet["foods_to_include"].extend(["Brazil nuts", "Seaweed", "Eggs", "Yogurt"])
        diet["foods_to_avoid"].extend(["Excess soy products", "Excess cruciferous vegetables raw"])

    # If no specific abnormalities, give general advice
    if not abnormal_tests:
        diet["recommendations"].extend([
            {"icon": "🥗", "title": "Balanced Diet", "description": "Your results look great! Maintain a balanced diet with plenty of fruits and vegetables."},
            {"icon": "🏃", "title": "Stay Active", "description": "Aim for 30 minutes of moderate exercise daily."},
            {"icon": "😴", "title": "Quality Sleep", "description": "Get 7-8 hours of quality sleep each night."}
        ])
        diet["foods_to_include"] = ["Fruits", "Vegetables", "Whole grains", "Lean protein", "Nuts"]

    # Remove duplicates
    diet["foods_to_include"] = list(set(diet["foods_to_include"]))
    diet["foods_to_avoid"] = list(set(diet["foods_to_avoid"]))

    # Sample meal plan
    diet["meal_plan"] = {
        "breakfast": "Oats with berries and nuts + Green tea",
        "mid_morning": "Seasonal fruit + handful of almonds",
        "lunch": "Brown rice + Dal + Sabzi + Salad + Buttermilk",
        "evening_snack": "Sprouts chaat or roasted chana",
        "dinner": "Multigrain roti + Vegetable curry + Soup",
        "bedtime": "Warm turmeric milk"
    }

    return diet


def generate_insights(test_results):
    """Generate key health insights from test results."""
    insights = {
        "overall_score": 0,
        "overall_status": "",
        "key_findings": [],
        "alerts": [],
        "positives": []
    }

    if not test_results:
        insights["overall_status"] = "No test results available"
        return insights

    total = len(test_results)
    normal = sum(1 for t in test_results if t["status"] == "Normal")
    score = round((normal / total) * 100) if total > 0 else 0
    insights["overall_score"] = score

    if score >= 90:
        insights["overall_status"] = "Excellent"
    elif score >= 70:
        insights["overall_status"] = "Good"
    elif score >= 50:
        insights["overall_status"] = "Needs Attention"
    else:
        insights["overall_status"] = "Consult Doctor Soon"

    # Key findings
    for test in test_results:
        if test["status"] == "High":
            insights["key_findings"].append({
                "type": "warning",
                "icon": "⚠️",
                "test": test["name"],
                "message": f"{test['name']} is elevated at {test['value']} {test['unit']} (normal: {test.get('ref_low', '?')}-{test.get('ref_high', '?')})"
            })
            insights["alerts"].append(f"{test['name']} is higher than normal")
        elif test["status"] == "Low":
            insights["key_findings"].append({
                "type": "alert",
                "icon": "🔻",
                "test": test["name"],
                "message": f"{test['name']} is below normal at {test['value']} {test['unit']} (normal: {test.get('ref_low', '?')}-{test.get('ref_high', '?')})"
            })
            insights["alerts"].append(f"{test['name']} is lower than normal")
        else:
            insights["positives"].append(f"{test['name']} is within normal range")

    return insights
