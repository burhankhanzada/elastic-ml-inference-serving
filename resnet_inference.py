import torch
from torchvision.io import decode_image
from torchvision.models import resnet18, ResNet18_Weights



WEIGHTS = ResNet18_Weights.DEFAULT
MODEL = resnet18(weights=WEIGHTS)


class Model_Inference:
    def __init__(self):
        self.img_path = None
        self.weights = WEIGHTS
        self.model = MODEL
    
    def preprocess_image(self, img_path:str) -> torch.Tensor:
        # decode uploaded_image
        self.img_path = img_path
        self.decoded_image = decode_image(self.img_path)

        # Step 2: Initialize the inference transforms
        preprocess = self.weights.transforms()

        # Step 3: Apply inference preprocessing transforms
        batch = preprocess(self.decoded_image).unsqueeze(0)
        
        return batch

    def predict(self, image_tensor):
        preprocessed_image = image_tensor

        self.model.eval()
        # Step 4: Use the model and print the predicted category
        prediction = self.model(preprocessed_image).squeeze(0).softmax(0)
        class_id = prediction.argmax().item()
        score = prediction[class_id].item()
        category_name = self.weights.meta["categories"][class_id]
        return f"{category_name}: {100 * score:.1f}%"


model = Model_Inference()
image = model.preprocess_image("/home/shwifty/SOSE25/cloud_computing/ml_serving/n10565667_scuba_diver.JPEG")
print(model.predict(image))