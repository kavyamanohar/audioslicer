from datasets import load_dataset

dataset = load_dataset("audiofolder", data_dir="./data/processed/corpus")
# You should have your username and associated token saved locally
dataset.push_to_hub("kavyamanohar/sc-hearings")
