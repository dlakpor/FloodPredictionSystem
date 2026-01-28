import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import predict, PredictionRequest, load_models

def test_prediction():
    print("Testing API prediction logic...")
    
    # Ensure models are loaded (they typically load on import, but just to be sure)
    # The api.py calls load_models() on import, so we should be good.
    
    # Create dummy features matching what the pipeline produces (10 features)
    # [0, 0, 0, 0, 0, temp, wind, pressure, humidity, clouds]
    dummy_features = [0.0, 0.0, 0.0, 0.0, 0.0, 25.0, 5.0, 1013.0, 60.0, 20.0]
    
    req = PredictionRequest(features=dummy_features)
    
    try:
        result = predict(req)
        print("✅ Prediction successful:")
        print(result)
        
        if "flood_risk" in result and "predicted_rainfall_mm" in result:
             print("✅ Response structure is valid")
        else:
             print("❌ Invalid response structure")
             
    except Exception as e:
        print(f"❌ Prediction failed: {e}")

if __name__ == "__main__":
    test_prediction()
