from fastapi import FastAPI
from resnet_inference import Model_Inference

model_inference = Model_Inference()

app = FastAPI()

@app.get("/predict")
async def predict():
    preprocessed_image = model_inference.preprocess_image('/home/shwifty/SOSE25/cloud_computing/ml_serving/n01608432_kite.JPEG')
    print(preprocessed_image)
    return {'tensor': preprocessed_image}