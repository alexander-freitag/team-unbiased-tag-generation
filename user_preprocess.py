# This file will be called once the setup is complete. 
# It should perform all the preprocessing steps that are necessary to run the project. 
# All important arguments will be passed via the command line.
# The input files will adhere to the format specified in datastructure/input-file.json

import json
from os.path import join, split as split_path
import requests as r
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

# Load the fine-tuned models and tokenizers
model_de = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-de-en")
tokenizer_de = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-de-en")
model_bg = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-bg-en")
tokenizer_bg = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-bg-en")

# Create translation pipelines
translation_pipeline_de_en = pipeline("translation_de_to_en", model=model_de, tokenizer=tokenizer_de)
translation_pipeline_bg_en = pipeline("translation_bg_to_en", model=model_bg, tokenizer=tokenizer_bg)


# Function to translate German text to English
def translate_german_to_english(german_text):
    translated_text = translation_pipeline_de_en(german_text)
    return translated_text[0]['translation_text']


# Function to translate Bulgarian text to English
def translate_bulgarian_to_english(bulgarian_text):
    translated_text = translation_pipeline_bg_en(bulgarian_text)
    return translated_text[0]['translation_text']


# TODO Implement the preprocessing steps here
def handle_input_file(file_location, output_path):
    with open(file_location, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Detect the language and translate the content to English if necessary
    content = "\n".join(data["content"])
    language = data.get("language", "en")

    if language == "de":
        content = translate_german_to_english(content)
    elif language == "bg":
        content = translate_bulgarian_to_english(content)

    # Call to local ollama
    call_data = {
        "model": "llama3",
        "prompt": content,
        "system": "You are a helpful assistant working at the EU. It is your job to give users unbiased article recommendations. To do so, you always provide a list of tags, whenever you are prompted with an article. The tags should represent the core ideas of the article, and always be unbiased and in English. Response with the tags only, separated by commas.",
        "stream": False
    }
    response = r.post("http://localhost:11434/api/generate", json=call_data)
    response = response.json()
    response_text = response["response"]
    response_text = response_text.replace("Tags:", "")
    tags = response_text.split(",")
    tags = list(map(lambda x: x.strip().lower(), tags))

    file_name = split_path(file_location)[-1]
    with open(join(output_path, file_name), "w") as f:
        json.dump({
            "transformed_representation": tags
        }, f)


# This is a useful argparse-setup, you probably want to use in your project:
import argparse

parser = argparse.ArgumentParser(description='Preprocess the data.')
parser.add_argument('--input', type=str, help='Path to the input data.', required=True, action="append")
parser.add_argument('--output', type=str, help='Path to the output directory.', required=True)

if __name__ == "__main__":
    args = parser.parse_args()
    files_inp = args.input
    files_out = args.output

    for file_location in files_inp:
        handle_input_file(file_location, files_out)


 