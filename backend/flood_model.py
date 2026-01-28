def predict_flood_risk(weather):
    """
    weather: dict containing rainfall, humidity, wind, pressure
    """

    rain = weather.get("rain", 0)
    humidity = weather.get("humidity", 0)
    pressure = weather.get("pressure", 1013)

    # Simple interpretable logic
    if rain > 20 and humidity > 80:
        return "High"
    elif rain > 10:
        return "Medium"
    else:
        return "Low"
