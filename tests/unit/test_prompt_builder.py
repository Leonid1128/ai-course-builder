from __future__ import annotations

from apps.ai_agents.services.prompt_builder import FgosPromptBuilder


def test_structure_prompt_contains_fgos_and_hours() -> None:
    prompt = FgosPromptBuilder().build_structure_prompt("Математика", "01.03.01", 72)
    assert "Математика" in prompt
    assert "01.03.01" in prompt
    assert "72" in prompt
    assert "ФГОС" in prompt
    assert "JSON" in prompt


def test_content_prompt_forbids_external_facts() -> None:
    prompt = FgosPromptBuilder().build_content_prompt("Физика", "Кинематика", "chunk")
    assert "<chunks>chunk</chunks>" in prompt
    assert "ТОЛЬКО" in prompt
    assert "presentation" in prompt
    assert "test" in prompt


def test_regenerate_prompt_keeps_block_id_and_version() -> None:
    prompt = FgosPromptBuilder().build_regenerate_prompt(
        discipline="Физика",
        section_title="Кинематика",
        context="v=s/t",
        instruction="Добавь пример",
        block_id="11111111-1111-1111-1111-111111111111",
        block_type="theory",
        current_content={"text": "определение"},
        version=3,
    )
    assert "version=4" in prompt
    assert "11111111-1111-1111-1111-111111111111" in prompt
