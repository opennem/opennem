"""
Generates training model for OpenAI

This script will read train.txt and generate a jsonl file with each line of the format
{"prompt": "<prompt>", "completion": "<completion>"}
"""

import json
import logging
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from opennem.utils.encoder import EnhancedJSONEncoder

logger = logging.getLogger("opennem.recordreactor.ai.train")


@dataclass
class PromptCompletion:
    prompt: str
    completion: str


def strip_prompt(prompt: str) -> str:
    """Strips prompt of certain characters from response"""
    STRIP_CHARS = ["\n", "\t", "#", ">"]

    for char in STRIP_CHARS:
        prompt = prompt.replace(char, "")

    return prompt.strip()


def get_training_version() -> str:
    """returns current timestamp as training version"""
    return "opennem-" + datetime.now().strftime("%Y%m%d-%H%M")


def split_prompt(prompt_block: str) -> PromptCompletion:
    """Takes a prompt text and splits it"""
    prompt = ""
    completion = ""

    for line in prompt_block.splitlines():
        if line.startswith(">"):
            prompt = (prompt + line[1:]).strip().lower()
        else:
            completion += line.strip() + "\n"

    return PromptCompletion(prompt, completion=completion)


def generate_training_set(
    training_file: Path,
) -> Iterable[PromptCompletion]:
    """Function that generates a list of training examples"""
    with training_file.open() as fh:
        lines = fh.readlines()

    # filter comments lines
    lines = [line for line in lines if not line.startswith("#")]

    # split into competions marked by ---
    prompts = "".join(lines).split("---")

    for prompt in prompts:
        if prompt:
            prompt_completion = split_prompt(prompt)

            if prompt_completion.prompt and prompt_completion.completion:
                yield prompt_completion
            else:
                logger.warning(
                    "prompt or completion is empty: %s",
                    prompt_completion,
                )

    return lines


def write_training_set(training_set: Path) -> Path:
    """Function that writes the training set to a file"""
    training_file = Path(__file__).parent / "train" / "train.jsonl"

    prompts: list[PromptCompletion] = list(generate_training_set(training_set))

    with training_file.open("w") as fh:
        for prompt in prompts:
            fh.write(json.dumps(prompt, cls=EnhancedJSONEncoder) + "\n")

    return training_file


def submit_new_finetune(training_file: Path, model: str = "davinci") -> str:
    """runs the openai process to submit new finetune"""
    ## Start fine-tuning
    version: str = get_training_version()
    command: list[str] = (
        f"openai api fine_tunes.create --training_file {training_file} --model {model} --suffix {version}".split()
    )
    subprocess.run(command)

    return version


def generate_prompt_set(prompt_file: Path) -> list[dict[str, str]]:
    """Function that generates a prompt set from the prompt file"""

    prompt_completions: list[PromptCompletion] = list(generate_training_set(prompt_file))

    prompts: list[dict[str, str]] = []

    for prompt in prompt_completions:
        if not prompt.prompt or not prompt.completion:
            logger.warning(
                "prompt or completion is empty: %s",
                prompt,
            )
        prompts.append({"role": "user", "content": prompt.prompt})
        prompts.append({"role": "assistant", "content": prompt.completion})

    return prompts


if __name__ == "__main__":
    logger.info("started")

    train_examples = Path(__file__).parent / "data" / "train.txt"
    training_set_path = write_training_set(train_examples)
    version = submit_new_finetune(training_set_path, model="gpt-4-1106-preview")
    logger.info(f"submitted version: {version}")
