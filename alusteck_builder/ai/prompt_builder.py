"""Prompt construction helpers."""


def build_prompt(structure_request: str, context: dict) -> str:
    return f"Build structure: {structure_request}\nContext: {context}"
