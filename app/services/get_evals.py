from pathlib import Path
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

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
qwen_path = hf_hub_download(
    repo_id=QWEN_REPO_ID,
    filename=QWEN_FILENAME,
    local_dir=INSTALL_FOLDER,          # accepts a Path object directly
    local_dir_use_symlinks=False,
)

minilm_path = hf_hub_download(
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
    n_gpu_layers=0,
    n_threads=4,
    n_ctx=2048,
    verbose=False,
)

def parse_string(user_input):

    pass






















# from huggingface_hub import hf_hub_download
# from llama_cpp import Llama
# import re
# import numpy as np
# import json


# # Russian word (including ё) and hyphenated compounds
# WORD_RE = re.compile(r"[а-яё]+(?:-[а-яё]+)*", re.IGNORECASE)

# # Pattern for dimension chains: 67 x 67 x 67 (also handles ×, х cyrillic, * and ,)
# DIM_RE = re.compile(
#     r"(?<!\w)(\d+(?:[.,]\d+)?)"           # first number
#     r"(?:\s*[x×хXХ*]\s*(\d+(?:[.,]\d+)?)){1,}"  # subsequent numbers
# )

# # Match a full dimension chain so we can rewrite it
# DIM_CHAIN_RE = re.compile(
#     r"(?<!\w)\d+(?:[.,]\d+)?(?:\s*[x×хXХ*]\s*\d+(?:[.,]\d+)?)+(?!\w)"
# )

# # Replacement table for bracket-like characters -> ( or )
# BRACKET_MAP = str.maketrans({
#     "[": "(", "]": ")",
#     "{": "(", "}": ")",
# })


# def lowercase_russian(text: str) -> str:
#     """Lowercase only Cyrillic characters; leave Latin and everything else alone."""
#     return re.sub(
#         r"[А-ЯЁ]",
#         lambda m: m.group(0).lower(),
#         text,
#     )


# def _dim_replacer(match: re.Match) -> str:
#     """Rewrite '67 x 67 x 67' (any surrounding whitespace) as '67x67x67'."""
#     chunk = match.group(0)
#     # Split on any separator (x, ×, х, X, Х, *), strip whitespace, rejoin with bare 'x'
#     parts = re.split(r"\s*[x×хXХ*]\s*", chunk)
#     return "x".join(parts)


# def normalize_text(text: str) -> str:
#     if not text:
#         return ""

#     # 1. Lowercase Russian chars only (Latin case preserved)
#     text = lowercase_russian(text)

#     # 2. Unify separators: | ; \t \n -> "," (single pass, no double commas)
#     text = re.sub(r"[|;\t\n\r]+", ",", text)
#     # Collapse ",," or ", ," runs into a single comma
#     text = re.sub(r"\s*,\s*(?:,\s*)+", ", ", text)

#     # 3. Brackets -> round brackets
#     text = text.translate(BRACKET_MAP)

#     # 4. Dimensions: 67 x 67 x 67 -> 67x67x67
#     text = DIM_CHAIN_RE.sub(_dim_replacer, text)

#     # 6. Whitespace / punctuation cleanup
#     text = re.sub(r"[ \t]{2,}", " ", text)
#     text = re.sub(r"\s+([,.!?;:)\]}»])", r"\1", text)
#     text = re.sub(r"([({\[«])\s+", r"\1", text)
#     text = re.sub(r",\s*,", ",", text)
#     text = re.sub(r"\s{2,}", " ", text)

#     return text.strip()
# # Paths to your four Q8 GGUF files
# model_path = "Qwen3.5-2B-Q8_0.gguf"

# # Load model
# model = Llama(
#     model_path=model_path,
#     n_gpu_layers=0,  # Offload all layers to GPU
#     n_threads=4,
#     n_ctx=2048,       # Context window
#     verbose=False
# )

# def get_name_and_chars(model_input):

#     with open('prompts/prompt chars.txt', 'r', encoding='utf-8') as file:
#         char_prompt = file.read()

#     with open('prompts/new prompt.txt', 'r', encoding='utf-8') as file:
#         name_prompt = file.read()

#     messages_chars = [
#         {"role": "system", "content": char_prompt},
#         {"role": "user", "content": model_input}
#     ]

#     messages_names = [
#         {"role": "system", "content": name_prompt},
#         {"role": "user", "content": model_input}
#     ]

#     model_output_chars = model.create_chat_completion(
#         messages=messages_chars,
#         max_tokens=512
#     )

#     model_output_name = model.create_chat_completion(
#         messages=messages_names,
#         max_tokens=512
#     )

#     return(model_output_name['choices'][0]['message']['content'], model_output_chars['choices'][0]['message']['content'])

# def search_candidates(name):
#     print()

# inputs = [normalize_text('Маша и Медведь Рюкзак туристический 31966	Маша и Медведь Рюкзак 31966	Росмэн	РОССИЯ	Бренд Маша и Медведь | Вес 0.00000 кг | Высота упаковки 170 мм | Габаритные размеры 370 х 255 х 160 см | Глубина упаковки 360 мм | Количество внешних карманов 3.00000 шт | Количество внутренних карманов 1.00000 шт | Материал Полиэстер | Особенности Водоотталкивающая пропитка,Ортопедическая спинка,Светоотражающие вставки,Анатомические лямки,Воздухопроницаемая спинка | Персонализация Маша и Медведь | Половая принадлежность Для девочек | Специальные отделения Отделение для бумаг формата А4,Карман с сеткой,Карман для пенала | Тип застежки Комбинированная | Тип сумки Рюкзак | Упаковка Пакет | Цвет красный | Ширина упаковки 250 мм')
# ]

# def cosine_similarity(arr1, arr2):

#     a = np.array(arr1)
#     b = np.array(arr2)
#     similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
#     return similarity

# def to_embed(text):
#     output = miniLM.create_embedding(text)
#     return output["data"][0]["embedding"]

# repo_id = "second-state/All-MiniLM-L6-v2-Embedding-GGUF"
# filename = "all-MiniLM-L6-v2-Q4_K_M.gguf"

# model_path = hf_hub_download(
#     repo_id=repo_id,
#     filename=filename
# )

# miniLM = Llama(
#     model_path=model_path,
#     embedding=True,
#     n_ctx=512,  # Context window size
#     verbose=False
# )


