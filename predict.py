from tqdm import tqdm
import torch.nn as nn
import torch

def predict(tokenized_title_list):
    test_encodings=tokenizer(tokenized_title_list, max_length=32, truncation=True, padding="max_length", return_tensors="pt")
    test_encodings={k: v.to(device) for k, v in test_encodings.items() if k!='token_type_ids'}

    loaded_model.eval()
    with torch.no_grad():
        outputs=loaded_model(**test_encodings)

    predicted_labels_=outputs.squeeze()
    percent=int(predicted_labels_*100)
    predicted_labels=predicted_labels_.round()
    
    return predicted_label, predicted_percent