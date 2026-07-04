"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Nome do prompt a ser puxado do LangSmith Hub.
# O prefixo "./" indica um prompt do seu próprio workspace/tenant.
DEFAULT_PROMPT_REF = "./bug_to_user_story_v1"

# Onde salvar localmente e sob qual chave no YAML.
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"
PROMPT_KEY = "bug_to_user_story_v1"


def extract_prompt_data(prompt_obj) -> dict:
    """
    Extrai system_prompt e user_prompt de um objeto de prompt do LangChain.

    Suporta tanto ChatPromptTemplate (mensagens system/human) quanto
    PromptTemplate simples (template único).

    Args:
        prompt_obj: Objeto retornado por hub.pull()

    Returns:
        Dicionário com system_prompt, user_prompt e input_variables.
    """
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt_obj, "messages", None)

    if messages:
        # ChatPromptTemplate: iterar sobre os message templates.
        for message in messages:
            template = getattr(getattr(message, "prompt", None), "template", None)
            if template is None:
                continue

            role = type(message).__name__.lower()
            if "system" in role:
                system_prompt = template
            elif "human" in role or "user" in role:
                user_prompt = template
            elif not user_prompt:
                # Fallback: primeiro template não-system vira o user_prompt.
                user_prompt = template
    else:
        # PromptTemplate simples: usar o template como user_prompt.
        user_prompt = getattr(prompt_obj, "template", "") or ""

    input_variables = list(getattr(prompt_obj, "input_variables", []) or [])

    return {
        "system_prompt": system_prompt.strip(),
        "user_prompt": user_prompt.strip(),
        "input_variables": input_variables,
    }


def pull_prompts_from_langsmith(
    prompt_ref: str = DEFAULT_PROMPT_REF,
    output_file: str = OUTPUT_FILE,
    prompt_key: str = PROMPT_KEY,
) -> bool:
    """
    Faz pull de um prompt do LangSmith Hub e salva localmente em YAML.

    Args:
        prompt_ref: Referência do prompt no Hub (ex.: "./bug_to_user_story_v1").
        output_file: Caminho do arquivo YAML de saída.
        prompt_key: Chave de topo sob a qual o prompt é salvo no YAML.

    Returns:
        True em caso de sucesso, False caso contrário.
    """
    print(f"Fazendo pull do prompt: {prompt_ref}")

    try:
        prompt_obj = hub.pull(prompt_ref)
    except Exception as e:
        print(f"\n❌ Erro ao fazer pull de '{prompt_ref}': {e}\n")
        print("Verifique:")
        print("  - LANGSMITH_API_KEY está configurada corretamente no .env")
        print("  - O prompt existe no seu workspace do LangSmith Hub")
        print("  - Sua conexão com a internet está funcionando")
        return False

    print("   ✓ Prompt carregado do LangSmith Hub")

    extracted = extract_prompt_data(prompt_obj)

    if not extracted["system_prompt"] and not extracted["user_prompt"]:
        print("   ⚠️  Não foi possível extrair o conteúdo do prompt (system/user vazios).")
        return False

    prompt_data = {
        prompt_key: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": extracted["system_prompt"],
            "user_prompt": extracted["user_prompt"],
            "input_variables": extracted["input_variables"],
            "version": "v1",
            "source": prompt_ref,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if save_yaml(prompt_data, output_file):
        print(f"   ✓ Prompt salvo em: {output_file}")
        print(f"   ✓ Variáveis de entrada: {extracted['input_variables']}")
        return True

    return False


def main():
    """Função principal."""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    prompt_ref = os.getenv("PULL_PROMPT_REF", DEFAULT_PROMPT_REF)

    success = pull_prompts_from_langsmith(prompt_ref=prompt_ref)

    print()
    if success:
        print("✅ Pull concluído com sucesso!")
        print("\nPróximos passos:")
        print("1. Analise o prompt em prompts/bug_to_user_story_v1.yml")
        print("2. Otimize-o em prompts/bug_to_user_story_v2.yml")
        print("3. Faça push: python src/push_prompts.py")
        return 0
    else:
        print("❌ Pull não foi concluído. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
