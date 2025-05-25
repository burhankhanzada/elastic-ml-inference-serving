from fastapi import FastAPI, UploadFile
from resnet_inference import ModelInference
from dispatcher.dispatcher import Dispatcher
from PIL import Image
import io



# Object of ModelInference class
model_inference = ModelInference()

app = FastAPI()


@app.get("/")
async def home():
    return {'message': 'hello'}


@app.post("/request_queue")
async def request_queue():
    """
    for request in queue:
        - post request to the /predict endpoint
        - get result = {prediction:class + confidence}
    """
    dispatcher = Dispatcher()
    
    
    pass



@app.post("/predict")
async def predict(image:UploadFile):
    """
    This is a post request async function for model inferencing.

    """
    try:
        contents = await image.read() # This line reads the uploaded image
        image = Image.open(io.BytesIO(contents)) # contents from uploaded file (bytes) turned to an Image

        preprocessed_image = model_inference.transform_image(image) # transform this image
        prediction = model_inference.predict(preprocessed_image)
    
        return {'prediction': prediction}
    
    except Exception as e:
        return {'Error': e}
    