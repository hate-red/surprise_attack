from app.schemas.dto import ParsedProductDTO

class ProductParsingService:
    def __init__(self, llm_client=None, ner_model=None):
        self.llm = llm_client
        self.ner = ner_model

    async def extract_product(self, text: str) -> ParsedProductDTO:
        """
        Здесь живет вся логика парсинга (LLM / NER / Regex).
        Транспортный слой про это ничего не знает.
        """
        # 1. Быстрая проверка (эвристика)
        if len(text) < 3:
            raise ValueError("Слишком короткий текст, не похоже на запрос товара")

        # 2. Основная логика (например, вызов LLM)
        # if self.llm:
        #     result = await self.llm.parse(text)
        #     return self._parse_llm_response(result)
        
        # 3. Пока заглушка — формируем и возвращаем DTO
        return ParsedProductDTO(
            name="ASUS VivoBook 15",
            specs={"ОЗУ": "16 ГБ", "SSD": "512 ГБ"}
        )

    def _parse_llm_response(self, raw_response: str) -> ParsedProductDTO:
        """Вспомогательный метод для парсинга ответа LLM."""
        # Здесь будет логика извлечения JSON из ответа LLM
        pass


# --- Фабрика для Dependency Injection ---
def get_parsing_service() -> ProductParsingService:
    """
    Создаёт и возвращает экземпляр сервиса.
    Здесь можно инициализировать LLM-клиент и NER-модель.
    """
    # TODO: Заменить на реальную инициализацию
    # llm_client = OpenAIClient(api_key="...")
    # ner_model = load_ner_model("path/to/model")
    
    return ProductParsingService(
        llm_client=None,  # Пока заглушка
        ner_model=None    # Пока заглушка
    )