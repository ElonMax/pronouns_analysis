import os
import sys
import wandb
import pandas as pd
import torch
import numpy as np
import logging
import json

from pyhocon import ConfigFactory
from torch import cuda
from torch.utils.data import DataLoader
from transformers import T5Tokenizer, T5ForConditionalGeneration
from datetime import datetime
from nltk.translate.bleu_score import sentence_bleu

from utils import DataSetClass


FORMAT = '[%(asctime)s] - [%(levelname)s] - [%(name)s] - %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__file__)
log.setLevel('INFO')

device = 'cuda' if cuda.is_available() else 'cpu'

config_path = os.path.join(os.environ["CONFIG_PATH"], "train.conf")
config_name = sys.argv[1]
config = ConfigFactory.parse_file(config_path)[config_name]

today = datetime.now()
stamp = today.strftime("[%m-%d-%Y]-[%H:%M:%S]")
filelog_path = os.path.join(config["log_dir"], "train-{}-{}.log".format(config["model_name"], stamp))
filelog = logging.FileHandler(filelog_path, mode='w')
filelog.setFormatter(logging.Formatter(FORMAT))
log.addHandler(filelog)

wandb.init(config=config, project="t5pronouns", name=config_name)

df_path = os.path.join(config['data_dir'], config['data_version'])
df = pd.read_csv(df_path, sep=';')
dataset_table = wandb.Table(data=df)
wandb.log({'dataset_table': dataset_table})


def train(epoch, tokenizer, model, device, loader, optimizer):
    """
    Function to be called for training with the parameters passed from main function

    """

    model.train()
    for step, data in enumerate(loader, 0):
        y = data["target_ids"].to(device, dtype=torch.long)
        y_ids = y[:, :-1].contiguous()
        lm_labels = y[:, 1:].clone().detach()
        lm_labels[y[:, 1:] == tokenizer.pad_token_id] = -100
        ids = data["source_ids"].to(device, dtype=torch.long)
        mask = data["source_mask"].to(device, dtype=torch.long)

        outputs = model(
            input_ids=ids,
            attention_mask=mask,
            decoder_input_ids=y_ids,
            labels=lm_labels,
        )
        loss = outputs[0]

        if step % 10 == 0:
            log.info("epoch: {}, step: {}, loss: {:.2f}".format(epoch, step, loss))
            wandb.log({"Loss/train": loss}, step=step)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()


def validate(epoch, tokenizer, model, device, loader):

    """
    Function to evaluate model for predictions

    """
    model.eval()
    predictions = []
    actuals = []
    bleu = []
    with torch.no_grad():
        for step, data in enumerate(loader, 0):
            y = data['target_ids'].to(device, dtype=torch.long)
            ids = data['source_ids'].to(device, dtype=torch.long)
            mask = data['source_mask'].to(device, dtype=torch.long)

            generated_ids = model.generate(
                input_ids=ids,
                attention_mask=mask,
                max_length=48,
                num_beams=2,
                repetition_penalty=2.5,
                length_penalty=1.0,
                early_stopping=True
                )
            preds = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]
            target = [tokenizer.decode(t, skip_special_tokens=True, clean_up_tokenization_spaces=True)for t in y]

            reference = [target[0].split(" ")]
            candidate = preds[0].split(" ")
            score = sentence_bleu(reference, candidate, weights=[1])
            wandb.log({"BLEU/eval": score}, step=step)

            if step % 100 == 0:
                log.info("Completed: {}".format(step))

            bleu.append(score)
            predictions.extend(preds)
            actuals.extend(target)

    return predictions, actuals, bleu


def T5Trainer(dataframe, source_text, target_text, model_params, output_dir=config["output_dir"]):
    """
    T5 trainer

    """

    output_dir = os.path.join(output_dir, model_params["model_name"])

    # Set random seeds and deterministic pytorch for reproducibility
    torch.manual_seed(model_params["seed"])  # pytorch random seed
    np.random.seed(model_params["seed"])  # numpy random seed
    torch.backends.cudnn.deterministic = True

    # logging
    log.info("Loading model params \n{}".format(json.dumps(model_params, indent=4)))

    # tokenzier for encoding the text
    tokenizer = T5Tokenizer.from_pretrained(model_params["model_dir"])

    # Defining the model. We are using t5-base model and added a Language model layer on top for generation of Summary.
    # Further this model is sent to device (GPU/TPU) for using the hardware.
    model = T5ForConditionalGeneration.from_pretrained(model_params["model_dir"])
    model = model.to(device)

    # Importing the raw dataset
    dataframe = dataframe[[source_text, target_text]]
    log.info("Reading data \n{}".format(dataframe.head(2)))

    # Creation of Dataset and Dataloader
    # Defining the train size. So 80% of the data will be used for training and the rest for validation.
    train_size = model_params["train_size"]
    train_dataset = dataframe.sample(frac=train_size, random_state=model_params["seed"])
    val_dataset = dataframe.drop(train_dataset.index).reset_index(drop=True)
    train_dataset = train_dataset.reset_index(drop=True)

    log.info("Dataset shape: {}".format(dataframe.shape))
    log.info("Train dataset shape: {}".format(train_dataset.shape))
    log.info("Test dataset shape: {}".format(val_dataset.shape))

    # Creating the Training and Validation dataset for further creation of Dataloader
    training_set = DataSetClass(
        train_dataset,
        tokenizer,
        model_params["max_source_text_length"],
        model_params["max_target_text_length"],
        source_text,
        target_text,
    )
    val_set = DataSetClass(
        val_dataset,
        tokenizer,
        model_params["max_source_text_length"],
        model_params["max_target_text_length"],
        source_text,
        target_text,
    )

    # Defining the parameters for creation of dataloaders
    train_params = {
        "batch_size": model_params["train_batch_size"],
        "shuffle": True,
        "num_workers": model_params["num_workers"],
    }

    val_params = {
        "batch_size": model_params["valid_batch_size"],
        "shuffle": False,
        "num_workers": model_params["num_workers"],
    }

    # Creation of Dataloaders for testing and validation. This will be used down for training and validation stage for the model.
    training_loader = DataLoader(training_set, **train_params)
    val_loader = DataLoader(val_set, **val_params)

    # Defining the optimizer that will be used to tune the weights of the network in the training session.
    optimizer = torch.optim.Adam(
        params=model.parameters(), lr=model_params["learning_rate"]
    )

    # Training loop
    log.info("Initiating Fine Tuning")
    for epoch in range(model_params["train_epochs"]):
        train(epoch, tokenizer, model, device, training_loader, optimizer)

    log.info("Saving model")
    # Saving the model after training
    path = os.path.join(output_dir, "model_files")
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)

    # evaluating test dataset
    log.info("Initiating Validation")
    for epoch in range(model_params["valid_epochs"]):
        predictions, actuals, bleu = validate(epoch, tokenizer, model, device, val_loader)
        final_df = pd.DataFrame({"Generated Text": predictions, "Actual Text": actuals})
        final_df["bleu_score"] = bleu
        final_table = wandb.Table(data=final_df)
        wandb.log({"eval_table": final_table})
        final_df.to_csv(os.path.join(output_dir, "predictions.csv"))

    log.info("Validation completed")
    log.info("Model saved {}".format(os.path.join(output_dir, "model_files")))
    log.info("Generation on validation data saved {}".format(os.path.join(output_dir, "predictions.csv")))


if __name__ == '__main__':
    T5Trainer(
        dataframe=df,
        source_text="in",
        target_text="out",
        model_params=config,
    )
