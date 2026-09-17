import os
import sys
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()


PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""


def get_vector_store():
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    return PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME", "documents"),
        connection=os.getenv("PGVECTOR_URL") or os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )


def search_prompt(question=None, verbose=True):
    if not question:
        try:
            question = input("PERGUNTA: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return None

    if not question:
        print("Nenhuma pergunta informada.")
        return None

    store = get_vector_store()
    results = store.similarity_search_with_score(question, k=10)

    if verbose:
        for i, (doc, score) in enumerate(results, start=1):
            print(f"Documento {i}:")
            print(f"Score: {score}")
            print(f"Conteúdo: {doc.page_content}\n")

    contexto = "\n\n".join([doc.page_content for doc, _ in results])
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pergunta=question)
    return prompt


def get_llm():
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            temperature=0,
        )
    elif os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_CHAT_MODEL", "gemini-1.5-flash"),
            temperature=0,
        )
    raise ValueError("Nenhuma chave de API configurada para o modelo LLM.")


def answer_question(question: str, verbose: bool = False) -> str:
    prompt = search_prompt(question, verbose=verbose)
    if not prompt:
        return ""
    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content


if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
    else:
        try:
            question = input("PERGUNTA: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            sys.exit(0)

    if question:
        prompt = search_prompt(question, verbose=True)
        if prompt:
            print("\nGerando resposta com a LLM...")
            resposta = answer_question(question, verbose=False)
            print(f"\nRESPOSTA: {resposta.strip()}")