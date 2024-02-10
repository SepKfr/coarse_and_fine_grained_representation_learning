import torch
from datasets import load_dataset
from sympy.physics.control.control_plots import np
from torch.utils.data import DataLoader
from transformers import AutoProcessor, AutoTokenizer

ds = load_dataset("lambdalabs/pokemon-blip-captions")
ds = ds["train"].train_test_split(test_size=0.1)
train_ds = ds["train"]
test_ds = ds["test"]

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class ImageCaptionData:

    def __init__(self, train, test, val=None, check_point="microsoft/git-base"):

        self.processor = AutoProcessor.from_pretrained(check_point)
        self.tokenizer = AutoTokenizer.from_pretrained(check_point)
        self._train = train
        self._test = test
        self._val = val

    def get_train_loader(self):
        return DataLoader(self._train, batch_size=64, collate_fn=self.collate_fn_train)

    def get_test_loader(self):
        return DataLoader(self._test, batch_size=64, collate_fn=self.collate_fn_test)

    def get_val_loader(self):
        return self._val

    def collate_fn_train(self, batch):
        images = [x["image"] for x in batch]
        captions = [x["text"] for x in batch]
        inputs = self.processor(images=images, text=captions, return_tensors="pt",
                                padding="max_length", truncation=True, max_length=16)
        inputs.to(device)

        padded_sequences = inputs["input_ids"]
        padded_sequences = torch.tensor(padded_sequences, device=device)
        unique_labels = torch.tensor(list(set(label for sublist in padded_sequences for label in sublist))).to(device)
        unique_labels = torch.unique(unique_labels)
        n_unique = len(unique_labels)
        one_hot_encoded = torch.zeros((padded_sequences.shape[0], n_unique), device=device)

        # Iterate through each sample and set the corresponding index to 1
        for i, sample in enumerate(padded_sequences):
            indices = torch.tensor([unique_labels.tolist().index(label) for label in sample]).to(device)
            one_hot_encoded[i].scatter_(0, indices, 1)
        one_hot_encoded = one_hot_encoded.to(torch.long)
        return inputs, one_hot_encoded

    def collate_fn_test(self, batch):
        images = [x["image"] for x in batch]
        captions = [x["text"] for x in batch]
        inputs = self.processor(images=images, text=captions, return_tensors="pt")

        inputs.to(device)

        return inputs, inputs["input_ids"]







