# ============================================================
# AGRIEDGE SMART FARM
# Person 3 - Decision Engine
# Phase 1
# ============================================================


# ============================================================
# SENSOR THRESHOLDS
# ============================================================

SOIL_MOISTURE_THRESHOLD = 30

HEAT_TEMPERATURE_THRESHOLD = 38

LOW_HUMIDITY_THRESHOLD = 35

DISEASE_CONFIDENCE_THRESHOLD = 0.80


# ============================================================
# DECISION ENGINE
# ============================================================

def generate_recommendation(
    temperature,
    soil_moisture,
    humidity,
    disease_status=None,
    disease_confidence=None,
    disease_prediction=None
):

    recommendations = []


    # --------------------------------------------------------
    # 1. SOIL MOISTURE
    # --------------------------------------------------------

    if soil_moisture < SOIL_MOISTURE_THRESHOLD:

        recommendations.append(
            "💧 Irrigation required. "
            f"Soil moisture is {soil_moisture}%. "
            "Consider irrigating the crop."
        )


    else:

        recommendations.append(
            "💧 Soil moisture is adequate. "
            "No immediate irrigation is required."
        )


    # --------------------------------------------------------
    # 2. TEMPERATURE
    # --------------------------------------------------------

    if temperature > HEAT_TEMPERATURE_THRESHOLD:

        recommendations.append(
            "🌡️ Heat stress warning. "
            f"Temperature is {temperature}°C. "
            "Increase irrigation frequency and "
            "avoid pesticide application during peak heat."
        )


    # --------------------------------------------------------
    # 3. HUMIDITY
    # --------------------------------------------------------

    if humidity < LOW_HUMIDITY_THRESHOLD:

        recommendations.append(
            "💨 Low humidity detected. "
            "Monitor the crop for water stress."
        )


    # --------------------------------------------------------
    # 4. DISEASE
    # --------------------------------------------------------

    if (
        disease_status == "DISEASE_DETECTED"
        and disease_confidence is not None
        and disease_confidence >= DISEASE_CONFIDENCE_THRESHOLD
    ):

        recommendations.append(
            "🌿 Possible "
            f"{disease_prediction}. "
            "Monitor affected leaves and "
            "consider appropriate crop protection."
        )


    # --------------------------------------------------------
    # 5. UNCERTAIN AI RESULT
    # --------------------------------------------------------

    elif disease_status == "UNCERTAIN":

        recommendations.append(
            "⚠️ AI result is uncertain. "
            "Take another clear image of the leaf "
            "for better analysis."
        )


    # --------------------------------------------------------
    # 6. HEALTHY CROP
    # --------------------------------------------------------

    elif disease_status == "HEALTHY":

        recommendations.append(
            "✅ No significant disease detected. "
            "Continue regular crop monitoring."
        )


    # --------------------------------------------------------
    # COMBINE ALL RECOMMENDATIONS
    # --------------------------------------------------------

    return "\n\n".join(recommendations)