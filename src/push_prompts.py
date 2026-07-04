"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

# Arquivo local com o prompt otimizado e nome curto do repositório no Hub.
V2_FILE = "prompts/bug_to_user_story_v2.yml"
REPO_SHORT_NAME = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Conteúdo do YAML inválido: esperado um objeto/dicionário."]

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    user_prompt = (prompt_data.get("user_prompt") or "").strip()

    if not system_prompt:
        errors.append("system_prompt está vazio ou ausente.")

    if not user_prompt:
        errors.append("user_prompt está vazio ou ausente.")

    # Não pode restar marcadores de tarefa não concluída.
    for field_name, text in (("system_prompt", system_prompt), ("user_prompt", user_prompt)):
        if "TODO" in text:
            errors.append(f"{field_name} ainda contém 'TODO'.")

    # A variável dinâmica {bug_report} precisa existir em algum dos prompts.
    if "{bug_report}" not in system_prompt and "{bug_report}" not in user_prompt:
        errors.append("A variável de template {bug_report} não foi encontrada no prompt.")

    # Mínimo de 2 técnicas aplicadas.
    techniques = prompt_data.get("techniques_applied", []) or []
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}.")

    return (len(errors) == 0, errors)


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """
    Monta um ChatPromptTemplate a partir dos dados do YAML.

    Usa separação System vs User: instruções no system, a variável
    {bug_report} no user.

    Args:
        prompt_data: Dados do prompt otimizado

    Returns:
        ChatPromptTemplate pronto para push.
    """
    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt") or "{bug_report}"

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (formato {username}/{repo})
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"\nFazendo push do prompt: {prompt_name}")

    try:
        chat_prompt = build_chat_prompt(prompt_data)
    except Exception as e:
        print(f"   ❌ Erro ao montar o ChatPromptTemplate: {e}")
        return False

    techniques = prompt_data.get("techniques_applied", []) or []
    description = prompt_data.get("description", "Bug report para User Story (otimizado)")
    tags = prompt_data.get("tags", []) or []

    readme = (
        f"# {prompt_name}\n\n"
        f"{description}\n\n"
        f"## Técnicas de Prompt Engineering aplicadas\n"
        + "".join(f"- {t}\n" for t in techniques)
        + "\nEntrada: `bug_report`. Saída: User Story em Markdown com Critérios de Aceitação."
    )

    try:
        url = hub.push(
            prompt_name,
            chat_prompt,
            new_repo_is_public=True,
            new_repo_description=description,
            readme=readme,
            tags=tags,
        )
        print(f"   ✓ Push realizado com sucesso (PÚBLICO)")
        print(f"   ✓ URL: {url}")
        print(f"   ✓ Técnicas: {', '.join(techniques)}")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao fazer push: {e}")
        print("\nVerifique:")
        print("  - LANGSMITH_API_KEY está configurada corretamente no .env")
        print("  - USERNAME_LANGSMITH_HUB corresponde ao seu handle no Hub")
        print("  - Sua conexão com a internet está funcionando")
        return False


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")

    print(f"Lendo prompt otimizado de: {V2_FILE}")
    prompt_data = load_yaml(V2_FILE)

    if not prompt_data:
        print(f"❌ Não foi possível carregar {V2_FILE}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("\n❌ Prompt inválido. Corrija os problemas abaixo antes do push:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("   ✓ Prompt validado com sucesso")

    prompt_name = f"{username}/{REPO_SHORT_NAME}"

    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    print()
    print("✅ Push concluído com sucesso!")
    print("\nPróximos passos:")
    print("1. Confira o prompt publicado em: https://smith.langchain.com/prompts")
    print("2. Confirme que o prompt está PÚBLICO")
    print("3. Execute a avaliação: python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
