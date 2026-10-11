"""
Опциональный эксперимент с локальными LLM (Qwen 3.5 2B Q8 + MiniLM) для
извлечения наименования и характеристик.

Основной конвейер API (app/services/product_service.py) его НЕ использует:
генерация на CPU занимала десятки секунд и не укладывалась в требование
"ответ не позднее 5–6 секунд". Модуль сохранён для сравнения и экспериментов.

Модели скачиваются и загружаются только при первом вызове load_models(),
а не при импорте модуля. Зависимости: pip install -r requirements-llm.txt
"""
from rapidfuzz import process

import json
from pathlib import Path

from app.config import project_root
from app.repositories.positions import PositionRepository
from app.repositories.additional_characteristics import CategoryRepository


# --- Configuration ---
QWEN_REPO_ID = "Manojb/Qwen3.5-2B-Q8_0.gguf"
QWEN_FILENAME = "Qwen3.5-2B-Q8_0.gguf"
INSTALL_FOLDER = project_root / "app" / "LLMS"
MINILM_REPO_ID = "second-state/All-MiniLM-L6-v2-Embedding-GGUF"
MINILM_FILENAME = "all-MiniLM-L6-v2-Q4_K_M.gguf"

char_prompt_path = project_root / 'app' / 'LLMS' / 'prompts' / 'prompt chars.txt'
name_prompt_path = project_root / 'app' / 'LLMS' / 'prompts' / 'prompt names.txt'

_models: dict = {}


def load_models() -> dict:
    """Скачивает (при необходимости) и загружает модели; результат кэшируется."""
    if _models:
        return _models
    from huggingface_hub import hf_hub_download
    from llama_cpp import Llama

    INSTALL_FOLDER.mkdir(parents=True, exist_ok=True)
    hf_hub_download(repo_id=QWEN_REPO_ID, filename=QWEN_FILENAME, local_dir=INSTALL_FOLDER)
    hf_hub_download(repo_id=MINILM_REPO_ID, filename=MINILM_FILENAME, local_dir=INSTALL_FOLDER)

    _models['minilm'] = Llama(
        model_path=str(Path(INSTALL_FOLDER, MINILM_FILENAME)),
        embedding=True,
        n_ctx=512,  # Context window size
        verbose=False,
    )
    _models['qwen'] = Llama(
        model_path=str(Path(INSTALL_FOLDER, QWEN_FILENAME)),  # llama-cpp-python wants str
        n_threads=4,
        n_ctx=2048,
        verbose=False,
    )
    _models['char_prompt'] = char_prompt_path.read_text(encoding='utf-8')
    _models['name_prompt'] = name_prompt_path.read_text(encoding='utf-8')
    return _models


async def get_output(user_input):
    models = load_models()
    qwen = models['qwen']
    messages_chars = [
        {"role": "system", "content": models['char_prompt']},
        {"role": "user", "content": user_input}
    ]

    messages_names = [
        {"role": "system", "content": models['name_prompt']},
        {"role": "user", "content": user_input}
    ]
    
    model_output_names = qwen.create_chat_completion(
        messages=messages_names,
        max_tokens=512
    )

    model_output_chars = qwen.create_chat_completion(
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

    top_ktru_ids = [ktru_positions[index][0] for _, _, index in top_ktru_matches]
    top_additional_ids = [additional_categories[index][0] for _, _, index in top_additional_matches]

    return top_ktru_ids, top_additional_ids
