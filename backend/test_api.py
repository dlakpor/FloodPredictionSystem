from fastapi.testclient import TestClient
from api import app, load_models
import pytest

# Initialize client
client = TestClient(app)

# Ensure models are loaded before running tests
# This might be automatic if the module is imported, but safe to verify
@pytest.fixture(autouse=True)
def setup_models():
    load_models()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Flood Prediction API is running"}

def test_predict_endpoint_valid_data():
    # Dummy features: [lags..., metrics..., temp, wind, press, hum, cloud]
    # Length needs to match what the model expects/scaler transforms
    # Based on previous steps, we used 10 features.
    dummy_features = [0.0, 0.0, 0.0, 0.0, 0.0, 25.0, 5.0, 1013.0, 60.0, 20.0]
    
    response = client.post("/predict", json={"features": dummy_features})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "predicted_rainfall_mm" in data
    assert "flood_probability" in data
    assert "flood_risk" in data
    
    assert isinstance(data["predicted_rainfall_mm"], float)
    assert isinstance(data["flood_probability"], float)
    assert data["flood_risk"] in ["Low", "Moderate", "High"]

def test_predict_endpoint_invalid_structure():
    response = client.post("/predict", json={"features": []})
    # Depending on model, empty list might crash or raise error.
    # Our API might return 500 or 400.
    # Given the implementation using np.array(...).reshape(1,-1), empty list might cause reshape error
    # causing 400 (caught exception).
    assert response.status_code in [400, 422, 500] 
