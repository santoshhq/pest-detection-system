#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import os
import warnings

# suppress non-fatal UserWarnings (e.g., timm mapping deprecated names) so they
# don't appear on stderr and cause the Node server to treat them as an error.
warnings.filterwarnings("ignore", category=UserWarning)

# torch imports
import torch
import timm
from PIL import Image
from torchvision import transforms

# --- Configuration ---
HERE = Path(__file__).parent
ROOT = HERE.parent
MODEL_PATH = Path(r"C:\Users\santo\Downloads\pest_backend\module\convnext_pestopia_LLRD_best.pt")
IMG_SIZE = 224
NUM_CLASSES = 132

# Full class list (provided). Ensure the order matches the model's training labels.
CLASS_NAMES = [
    'Adristyrannus', 'Aleurocanthus spiniferus', 'Ampelophaga', 'Aphis citricola Vander Goot', 'Apolygus lucorum', 'Bactrocera tsuneonis', 'Beet spot flies', 'Black hairy', 'Brevipoalpus lewisi McGregor', 'Ceroplastes rubens', 'Chlumetia transversa', 'Chrysomphalus aonidum', 'Cicadella viridis', 'Cicadellidae', 'Colomerus vitis', 'Dacus dorsalis(Hendel)', 'Dasineura sp', 'Deporaus marginatus Pascoe', 'Erythroneura apicalis', 'Field Cricket', 'Fruit piercing moth', 'Gall fly', 'Icerya purchasi Maskell', 'Indigo caterpillar', 'Jute Stem Weevil', 'Jute aphid', 'Jute hairy', 'Jute red mite', 'Jute semilooper', 'Jute stem girdler', 'Jute stick insect', 'Lawana imitata Melichar', 'Leaf beetle', 'Limacodidae', 'Locust', 'Locustoidea', 'Lycorma delicatula', 'Mango flat beak leafhopper', 'Mealybug', 'Miridae', 'Nipaecoccus vastalor', 'Panonchus citri McGregor', 'Papilio xuthus', 'Parlatoria zizyphus Lucus', 'Phyllocnistis citrella Stainton', 'Phyllocoptes oleiverus ashmead', 'Pieris canidia', 'Pod borer', 'Polyphagotars onemus latus', 'Potosiabre vitarsis', 'Prodenia litura', 'Pseudococcus comstocki Kuwana', 'Rhytidodera bowrinii white', 'Rice Stemfly', 'Salurnis marginella Guerr', 'Scirtothrips dorsalis Hood', 'Spilosoma Obliqua', 'Sternochetus frigidus', 'Termite', 'Termite odontotermes (Rambur)', 'Tetradacus c Bactrocera minax', 'Thrips', 'Toxoptera aurantii', 'Toxoptera citricidus', 'Trialeurodes vaporariorum', 'Unaspis yanonensis', 'Viteus vitifoliae', 'Xylotrechus', 'Yellow Mite', 'alfalfa plant bug', 'alfalfa seed chalcid', 'alfalfa weevil', 'aphids', 'army worm', 'asiatic rice borer', 'beet army worm', 'beet fly', 'beet weevil', 'beetle', 'bird cherry-oataphid', 'black cutworm', 'blister beetle', 'bollworm', 'brown plant hopper', 'cabbage army worm', 'cerodonta denticornis', 'corn borer', 'corn earworm', 'cutworm', 'english grain aphid', 'fall armyworm', 'flax budworm', 'flea beetle', 'grain spreader thrips', 'grasshopper', 'green bug', 'grub', 'large cutworm', 'legume blister beetle', 'longlegged spider mite', 'lytta polita', 'meadow moth', 'mites', 'mole cricket', 'odontothrips loti', 'oides decempunctata', 'paddy stem maggot', 'parathrene regalis', 'peach borer', 'penthaleus major', 'red spider', 'rice gall midge', 'rice leaf caterpillar', 'rice leaf roller', 'rice leafhopper', 'rice shell pest', 'rice water weevil', 'sawfly', 'sericaorient alismots chulsky', 'small brown plant hopper', 'stem borer', 'tarnished plant bug', 'therioaphis maculata Buckton', 'wheat blossom midge', 'wheat phloeothrips', 'wheat sawfly', 'white backed plant hopper', 'white margined moth', 'whitefly', 'wireworm', 'yellow cutworm', 'yellow rice borer'
]

# Lazy-load and reuse model across calls (so repeated calls are fast in same Python process)
_model = None

# Quick test mode: if DUMMY_PREDICT=1 is set in the environment, return a static sample
# prediction and exit. This helps validate the HTTP/file upload flow without loading
# heavy ML dependencies or a model file.
if os.getenv("DUMMY_PREDICT") == "1":
    sample = [
        {"class_name": "aphids", "confidence": 0.85},
        {"class_name": "whitefly", "confidence": 0.08},
        {"class_name": "thrips", "confidence": 0.02}
    ]
    print(json.dumps(sample))
    sys.exit(0)

def load_model():
    global _model
    if _model is not None:
        return _model
    # create model architecture (must match training)
    model = timm.create_model('convnext_tiny_in22k', pretrained=False, num_classes=NUM_CLASSES)
    # load state dict (works if you saved state_dict); if entire model was saved, use torch.load directly
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    state = torch.load(str(MODEL_PATH), map_location=torch.device("cpu"))
    # if saved as state_dict or as full model: try both
    if isinstance(state, dict) and 'state_dict' in state and isinstance(state['state_dict'], dict):
        model.load_state_dict(state['state_dict'])
    else:
        try:
            model.load_state_dict(state)
        except Exception:
            # If the file is a whole model, try direct assignment
            try:
                model = state
            except Exception as e:
                raise e
    model.eval()
    _model = model
    return _model

# image transform (must match training transforms)
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

def predict_image(image_path, topk=1):
    model = load_model()
    img = Image.open(image_path).convert("RGB")
    inp = transform(img).unsqueeze(0)  # batch dim
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
        # write error to stderr so the calling Node process can detect it via stderr
        sys.stderr.write(json.dumps({"error": str(e)}))
        sys.stderr.flush()
        sys.exit(1)
