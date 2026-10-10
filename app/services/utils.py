from pyaspeller import YandexSpeller



def validate_and_fix_typos(text: str) -> dict:
    """
    Проверяет русский и английский текст на опечатки.    
    """

    if not text or not isinstance(text, str):
        return {
            "has_typo": False,
            "suggestion": text,
    }
    
    speller = YandexSpeller()
    fixed_text = speller.spelled(text)
        
    return {
        "has_typo": fixed_text != text,
        "suggestion": fixed_text,
    }
        

