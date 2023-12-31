from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import datasets
import argparse
from tqdm import tqdm
import logging
logging.disable(logging.WARNING)

BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"

def build_masked_func(masked_func: str):
    masked_func = masked_func.replace('<FILL_FUNCTION_BODY>', FILL_TOKEN)
    return BEGIN_TOKEN + masked_func + END_TOKEN

def split_batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'a') as fout:
        fout.write(string)

def run(args):

    dataset_id = args.dataset_id
    model_id = args.model_id

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
    if args.load_in_8bit:
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map='auto', load_in_8bit=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map='auto').cuda()

    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right" # Fix weird overflow issue with fp16 training

    dataset = datasets.load_dataset(dataset_id, split='test')

    # train_dataset = raw_train_datasets.map(
    #     train_tokenize_function,
    #     batched=True,
    #     batch_size=3000,
    #     num_proc=32,
    #     remove_columns=raw_train_datasets.column_names

    sources = [
        build_masked_func(masked_contract)
        for masked_contract in dataset['masked_contract']
    ]

    batch_list = split_batch(sources, args.batch_size)
    len_batch = len(sources) // args.batch_size
    with tqdm(total=len_batch, desc="gen") as pbar:
        for batch in batch_list:
            model_inputs = tokenizer(batch, return_tensors="pt", padding=True, max_length=2048, truncation=True).to("cuda")

            generated_ids = model.generate(**model_inputs, max_new_tokens=500, pad_token_id=tokenizer.eos_token_id)

            output = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

            for idx, source in enumerate(batch):
                # print(idx, source)
                write_string_to_file(args.output_file, output[idx][len(source):] + '\n')
                
                # print(output[0][len(sources[0]):], output[1][len(sources[1]):])
            pbar.update(1)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch_size", default=2, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_id", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--dataset_id", type=str, default='zhaospei/smart-contract-gen')
    parser.add_argument("--output_file", type=str, default="gen.output")
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()