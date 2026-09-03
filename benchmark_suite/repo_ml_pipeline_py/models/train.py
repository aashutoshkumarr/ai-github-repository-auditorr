import os
import torch
import torch.nn as nn

class ClassifierModel(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

def train_epoch(model: nn.Module, dataloader, optimizer, criterion):
    """Executes single training epoch across mini-batches."""
    model.train()
    total_loss = 0.0
    for batch_x, batch_y in dataloader:
        optimizer.zero_grad()
        preds = model(batch_x)
        loss = criterion(preds, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss
