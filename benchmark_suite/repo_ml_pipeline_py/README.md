# 🧠 Deep Learning Predictive Pipeline

Automated machine learning training and inference pipeline using PyTorch, Scikit-Learn, and FastAPI.

## Architecture
- `data/preprocess.py`: Feature engineering, categorical encoding, and tensor scaling.
- `models/train.py`: Distributed multi-GPU model training with early stopping.

## Installation
```bash
pip install -r requirements.txt
python -m models.train
```

## License
MIT
