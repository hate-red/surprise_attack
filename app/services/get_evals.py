from rapidfuzz import process

import asyncio

import json
from pathlib import Path
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

from app.config import project_root
from app.repositories.positions import PositionRepository
from app.repositories.additional_characteristics import CategoryRepository


# --- Configuration ---
PROMPTS_FLODER = "./LLMS/prompts"
QWEN_REPO_ID = "Manojb/Qwen3.5-2B-Q8_0.gguf"
QWEN_FILENAME = "Qwen3.5-2B-Q8_0.gguf"
INSTALL_FOLDER = Path("./app/LLMS")
MINILM_REPO_ID = "second-state/All-MiniLM-L6-v2-Embedding-GGUF"
MINILM_FILENAME = "all-MiniLM-L6-v2-Q4_K_M.gguf"

# --- 1. Ensure the installation folder exists ---
INSTALL_FOLDER.mkdir(parents=True, exist_ok=True)

# --- 2. Download the model file to the specific folder ---
qwen_path = hf_hub_download( # type: ignore
    repo_id=QWEN_REPO_ID,
    filename=QWEN_FILENAME,
    local_dir=INSTALL_FOLDER,          # accepts a Path object directly
    local_dir_use_symlinks=False,
)

minilm_path = hf_hub_download( # type: ignore
    repo_id=MINILM_REPO_ID,
    filename=MINILM_FILENAME,
    local_dir=INSTALL_FOLDER,          # accepts a Path object directly
    local_dir_use_symlinks=False,
)

# --- 3. Verify and load ---
qwen_path = Path(INSTALL_FOLDER, QWEN_FILENAME)
minilm_path = Path(INSTALL_FOLDER, MINILM_FILENAME)

MiniLM = Llama(
    model_path=str(minilm_path),
    embedding=True,
    n_ctx=512,  # Context window size
    verbose=False
)

Qwen = Llama(
    model_path=str(qwen_path),        # llama-cpp-python wants str
    n_threads=4,
    n_ctx=2048,
    verbose=False,
)

char_prompt_path = project_root / 'app' / 'LLMS' / 'prompts' / 'prompt chars.txt'
name_prompt_path = project_root / 'app' / 'LLMS' / 'prompts' / 'prompt names.txt'

char_prompt = char_prompt_path.read_text()
name_prompt = name_prompt_path.read_text()


async def get_output(user_input):
    messages_chars = [
        {"role": "system", "content": char_prompt},
        {"role": "user", "content": user_input}
    ]

    messages_names = [
        {"role": "system", "content": name_prompt},
        {"role": "user", "content": user_input}
    ]
    
    model_output_names = Qwen.create_chat_completion(
        messages=messages_names,
        max_tokens=512
    )

    model_output_chars = Qwen.create_chat_completion(
        messages=messages_chars,
        max_tokens=512
    )

    return (
        model_output_names["choices"][0]["message"]["content"], # type: ignore
        model_output_chars["choices"][0]["message"]["content"] # type: ignore
    )



async def get_best_candidates_ids(user_input: str):
    ktru_positions = await PositionRepository.get_all_ids_and_names() # type: ignore
    additional_categories = await CategoryRepository.get_all_ids_and_names() # type: ignore

    name_str, chars_str = await get_output(user_input)
    
    name = json.loads(name_str)['name'] # type: ignore
    # keys only
    chars = [_ for _ in json.loads(chars_str)] # type: ignore

    top_ktru_matches = process.extract(
        query=name, 
        choices=[name for _, name in ktru_positions],
        limit=5,
        score_cutoff=50
    )
    top_additional_matches = process.extract(
        query=name, 
        choices=[name for _, name in additional_categories],
        limit=5,
        score_cutoff=50
    )

    top_ktru_ids = []
    top_additional_ids = []

    for choice, similarity, index in top_ktru_matches:
        print(choice, similarity)
        top_ktru_ids.append(ktru_positions[index][0])

    for choice, similarity, index in top_ktru_matches:
        print(choice, similarity)
        top_additional_ids.append(ktru_positions[index][0])

    return top_ktru_ids, top_ktru_ids
