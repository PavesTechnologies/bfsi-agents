import io
import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import efficientnet_b0

class EfficientNetValidator:
    def __init__(self):
        self.model = efficientnet_b0(weights="IMAGENET1K_V1")
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])

    def validate(self, file_bytes: bytes) -> float:
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            tensor = self.transform(image).unsqueeze(0)

            with torch.no_grad():
                logits = self.model(tensor)
                prob = torch.softmax(logits, dim=1).max().item()

            return prob
        except Exception:
            return 0.0
