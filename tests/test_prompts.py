"""
Testes automatizados para validação de prompts.

Valida o prompt otimizado em prompts/bug_to_user_story_v2.yml:
- Estrutura (system_prompt presente e preenchido)
- Persona / Role Prompting
- Menção ao formato (Markdown / User Story padrão)
- Exemplos Few-shot
- Ausência de TODOs
- Mínimo de 2 técnicas declaradas nos metadados
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure  # noqa: F401 (disponível para uso opcional)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    """Carrega o prompt otimizado v2 uma única vez por módulo."""
    assert PROMPT_FILE.exists(), f"Arquivo não encontrado: {PROMPT_FILE}"
    return load_prompts(str(PROMPT_FILE))


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente no YAML."
        system_prompt = prompt["system_prompt"]
        assert isinstance(system_prompt, str), "'system_prompt' deve ser uma string."
        assert system_prompt.strip(), "'system_prompt' não pode estar vazio."

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt.get("system_prompt", "").lower()
        # Deve declarar explicitamente uma persona/role para o modelo.
        assert "você é um" in system_prompt or "voce e um" in system_prompt, (
            "O system_prompt deve definir uma persona (ex.: 'Você é um Product Manager...')."
        )
        # E deve mencionar um papel relevante ao domínio.
        assert any(
            role in system_prompt
            for role in ("product manager", "product owner", "engenheiro", "analista")
        ), "A persona deve estar associada a um papel relevante (ex.: Product Manager)."

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt.get("system_prompt", "").lower()
        mentions_markdown = "markdown" in system_prompt
        mentions_user_story_template = (
            "como um" in system_prompt
            and "eu quero" in system_prompt
            and "para que" in system_prompt
        )
        assert mentions_markdown or mentions_user_story_template, (
            "O prompt deve exigir formato Markdown ou o template padrão de User Story "
            "('Como um... eu quero... para que...')."
        )

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt.get("system_prompt", "")
        # Conta marcadores de exemplo (ex.: "EXEMPLO 1", "Exemplo 2").
        example_markers = re.findall(r"exemplo\s*\d", system_prompt, flags=re.IGNORECASE)
        assert len(example_markers) >= 2, (
            "O prompt deve conter pelo menos 2 exemplos de entrada/saída (Few-shot). "
            f"Encontrados: {len(example_markers)}."
        )
        # Os exemplos devem demonstrar par entrada -> saída.
        low = system_prompt.lower()
        assert "relato de bug" in low and "user story" in low, (
            "Os exemplos devem demonstrar a entrada (relato de bug) e a saída (User Story)."
        )

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        # Verifica todos os campos de texto do YAML.
        text_blob = "\n".join(
            str(value) for value in prompt.values() if isinstance(value, str)
        )
        assert "[TODO]" not in text_blob, "Há um marcador [TODO] no prompt."
        assert "TODO" not in text_blob, "Há um marcador TODO no prompt."

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista."
        assert len(techniques) >= 2, (
            f"Pelo menos 2 técnicas devem ser listadas. Encontradas: {len(techniques)}."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
