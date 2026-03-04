import timm
import torch
import torch.nn as nn


class EfficientNetB0(nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()

        self.model = timm.create_model(
            "efficientnet_b0",
            pretrained=True,
            num_classes=num_classes,
        )

    def forward(self, x):
        return self.model(x)
