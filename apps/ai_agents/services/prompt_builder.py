from __future__ import annotations

from typing import Any

from apps.common.interfaces import PromptBuilderProtocol


class FgosPromptBuilder(PromptBuilderProtocol):
    def build_structure_prompt(self, discipline: str, direction: str, hours: int) -> str:
        return (
            f"Вы — методист ВУЗа. Разработайте структуру курса '{discipline}' "
            f"для направления '{direction}', объем {hours} ч.\n"
            "Учитывайте ФГОС. Распределите часы по разделам так, чтобы сумма была равна "
            f"{hours}. Сформулируйте цели обучения (objectives) для каждого раздела.\n"
            "Верните ТОЛЬКО валидный JSON вида:\n"
            '{"sections":[{"title":"","description":"","hours":0,"objectives":[""]}]}\n'
            "Без markdown и комментариев."
        )

    def build_content_prompt(self, discipline: str, section_title: str, context: str) -> str:
        return (
            f"Вы — эксперт по дисциплине {discipline}.\n"
            "Используйте ТОЛЬКО факты из материалов ниже. Не добавляйте сведения, "
            "которых нет в <chunks>. Если данных недостаточно, явно напишите об этом в content.\n"
            f"Материалы: <chunks>{context}</chunks>\n"
            f"Сгенерируйте блоки для раздела '{section_title}': "
            "presentation, theory, quiz, test.\n"
            "Каждый блок — объект: "
            '{"block_id":"uuid","type":"presentation|theory|quiz|test",'
            '"content":{},"source_reference":{"filename":"","chunk":""},"version":1}.\n'
            "Верните ТОЛЬКО JSON-массив из 4 блоков. Без markdown."
        )

    def build_regenerate_prompt(
        self,
        *,
        discipline: str,
        section_title: str,
        context: str,
        instruction: str,
        block_id: str,
        block_type: str,
        current_content: dict[str, Any],
        version: int,
    ) -> str:
        return (
            f"Вы — эксперт по {discipline}, раздел '{section_title}'.\n"
            f"Запрос: '{instruction}'.\n"
            f"Тип блока: {block_type}, ID: {block_id}.\n"
            f"Текущее содержимое: {current_content}\n"
            f"Материалы (используйте только информацию из них): <chunks>{context}</chunks>\n"
            "\n"
            "Верните ОДИН JSON-объект со строго следующей структурой:\n"
            "{\n"
            f'  "type": "{block_type}",\n'
            '  "content": {\n'
            '    // обновите содержимое, используя информацию из материалов\n'
            '  },\n'
            f'  "version": {version + 1}\n'
            "}\n"
            "\n"
            "Правила:\n"
            "1. Верните только JSON, без комментариев, пояснений или markdown-разметки.\n"
            "2. Поле content должно иметь ту же структуру (ключи), что и в текущем содержимом, но значения измените согласно материалам.\n"
            "3. Не добавляйте факты, отсутствующие в материалах.\n"
            "4. Убедитесь, что JSON валиден.\n"
            f"5. Установите version={version + 1} в поле version.\n"
        )
