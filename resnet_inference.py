"""
This class is for using PyTorch's API.
The API allows us to use pre-trained models like ResNet-X [X - represents Layers]/
For the cloud computing project we are using ResNet18 for image classification.
"""

from torchvision.io import decode_image
from torchvision.models import resnet18, ResNet18_Weights
from torchvision.transforms import transforms


# Global constant variables for the project
WEIGHTS = ResNet18_Weights.DEFAULT
MODEL = resnet18(weights=WEIGHTS)


class ModelInference:
    def __init__(self):
        self.image = None
        self.weights = WEIGHTS
        self.model = MODEL
    
    def transform_image(self, image):
        self.image = image
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor()
        ])
        tensor = transform(image).unsqueeze(0)  # Returns FloatTensor in [0, 1]
        return tensor

    def predict(self, image_tensor):
        preprocessed_image = image_tensor

        self.model.eval()
        # Use the model and print the predicted category
        prediction = self.model(preprocessed_image).squeeze(0).softmax(0)
        class_id = prediction.argmax().item()
        score = prediction[class_id].item()
        category_name = self.weights.meta["categories"][class_id]
        return f"{category_name}: {100 * score:.1f}%"