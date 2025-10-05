#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import os
import warnings

# suppress non-fatal UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

# torch imports
import torch
import timm
from PIL import Image
from torchvision import transforms

# --- New dependency for Google Drive download ---
try:
    import gdown
except ImportError:
    os.system("pip install gdown")
    import gdown

# --- Configuration ---
HERE = Path(__file__).parent
ROOT = HERE.parent
MODEL_DIR = ROOT / "model"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "convnext_pestopia_LLRD_best.pt"
IMG_SIZE = 224
NUM_CLASSES = 132

# Google Drive direct download link
GDRIVE_FILE_ID = "1_f2RHYwA9zA6RzUoHR5Ir3_P5pO3eMy5"
GDRIVE_URL = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"

# Full class list (simplified for brevity)
CLASS_NAMES = [
    'Adristyrannus', 'Aleurocanthus spiniferus', 'Ampelophaga', 'Aphis citricola Vander Goot',
    'Apolygus lucorum', 'Bactrocera tsuneonis', 'Beet spot flies', 'Black hairy',
    'Brevipoalpus lewisi McGregor', 'Ceroplastes rubens', 'Chlumetia transversa',
    'Chrysomphalus aonidum', 'Cicadella viridis', 'Cicadellidae', 'Colomerus vitis',
    'Dacus dorsalis(Hendel)', 'Dasineura sp', 'Deporaus marginatus Pascoe',
    'Erythroneura apicalis', 'Field Cricket', 'Fruit piercing moth', 'Gall fly',
    'Icerya purchasi Maskell', 'Indigo caterpillar', 'Jute Stem Weevil', 'Jute aphid',
    'Jute hairy', 'Jute red mite', 'Jute semilooper', 'Jute stem girdler', 'Jute stick insect',
    'Lawana imitata Melichar', 'Leaf beetle', 'Limacodidae', 'Locust', 'Locustoidea',
    'Lycorma delicatula', 'Mango flat beak leafhopper', 'Mealybug', 'Miridae',
    'Nipaecoccus vastalor', 'Panonchus citri McGregor', 'Papilio xuthus',
    'Parlatoria zizyphus Lucus', 'Phyllocnistis citrella Stainton', 'Phyllocoptes oleiverus ashmead',
    'Pieris canidia', 'Pod borer', 'Polyphagotars onemus latus', 'Potosiabre vitarsis',
    'Prodenia litura', 'Pseudococcus comstocki Kuwana', 'Rhytidodera bowrinii white',
    'Rice Stemfly', 'Salurnis marginella Guerr', 'Scirtothrips dorsalis Hood',
    'Spilosoma Obliqua', 'Sternochetus frigidus', 'Termite', 'Termite odontotermes (Rambur)',
    'Tetradacus c Bactrocera minax', 'Thrips', 'Toxoptera aurantii', 'Toxoptera citricidus',
    'Trialeurodes vaporariorum', 'Unaspis yanonensis', 'Viteus vitifoliae', 'Xylotrechus',
    'Yellow Mite', 'alfalfa plant bug', 'alfalfa seed chalcid', 'alfalfa weevil', 'aphids',
    'army worm', 'asiatic rice borer', 'beet army worm', 'beet fly', 'beet weevil', 'beetle',
    'bird cherry-oataphid', 'black cutworm', 'blister beetle', 'bollworm', 'brown plant hopper',
    'cabbage army worm', 'cerodonta denticornis', 'corn borer', 'corn earworm', 'cutworm',
    'english grain aphid', 'fall armyworm', 'flax budworm', 'flea beetle', 'grain spreader thrips',
    'grasshopper', 'green bug', 'grub', 'large cutworm', 'legume blister beetle',
    'longlegged spider mite', 'lytta polita', 'meadow moth', 'mites', 'mole cricket',
    'odontothrips loti', 'oides decempunctata', 'paddy stem maggot', 'parathrene regalis',
    'peach borer', 'penthaleus major', 'red spider', 'rice gall midge', 'rice leaf caterpillar',
    'rice leaf roller', 'rice leafhopper', 'rice shell pest', 'rice water weevil', 'sawfly',
    'sericaorient alismots chulsky', 'small brown plant hopper', 'stem borer',
    'tarnished plant bug', 'therioaphis maculata Buckton', 'wheat blossom midge',
    'wheat phloeothrips', 'wheat sawfly', 'white backed plant hopper', 'white margined moth',
    'whitefly', 'wireworm', 'yellow cutworm', 'yellow rice borer'
]

# Lazy-load model
_model = None

# Quick test mode
if os.getenv("DUMMY_PREDICT") == "1":
    sample = [
        {"class_name": "aphids", "confidence": 0.85},
        {"class_name": "whitefly", "confidence": 0.08},
        {"class_name": "thrips", "confidence": 0.02}
    ]
    print(json.dumps(sample))
    sys.exit(0)

def download_model():
    """Download model from Google Drive using gdown."""
    if MODEL_PATH.exists():
        return
    print("Downloading model from Google Drive using gdown...")
    gdown.download(GDRIVE_URL, str(MODEL_PATH), quiet=False)
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model download failed!")
    print("Model downloaded successfully!")

def load_model():
    global _model
    if _model is not None:
        return _model
    download_model()
    model = timm.create_model('convnext_tiny_in22k', pretrained=False, num_classes=NUM_CLASSES)
    state = torch.load(str(MODEL_PATH), map_location=torch.device("cpu"))
    if isinstance(state, dict) and 'state_dict' in state and isinstance(state['state_dict'], dict):
        model.load_state_dict(state['state_dict'])
    else:
        try:
            model.load_state_dict(state)
        except Exception:
            model = state
    model.eval()
    _model = model
    return _model

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def predict_image(image_path, topk=1):
    model = load_model()
    img = Image.open(image_path).convert("RGB")
    inp = transform(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(inp)
        probs = torch.nn.functional.softmax(outputs[0], dim=0)
        topk_vals, topk_idxs = torch.topk(probs, topk)
        preds = []
        for val, idx in zip(topk_vals, topk_idxs):
            idx_int = int(idx.item())
            cls_name = CLASS_NAMES[idx_int] if idx_int < len(CLASS_NAMES) else f"class_{idx_int}"
            preds.append({"class_name": cls_name, "confidence": round(float(val.item()), 4)})
        return preds

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps([]))
        sys.exit(0)
    image_path = sys.argv[1]
    try:
        results = predict_image(image_path)
        print(json.dumps(results))
    except Exception as e:
        sys.stderr.write(json.dumps({"error": str(e)}))
        sys.stderr.flush()
        sys.exit(1)
