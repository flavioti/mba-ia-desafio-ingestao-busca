import sys
from search import answer_question


def main():
    print("Faça sua pergunta:")
    print("(Digite 'sair', 'exit' ou 'quit' para encerrar)\n")

    # Se uma pergunta for passada diretamente como argumento na linha de comando
    if len(sys.argv) > 1:
        pergunta = " ".join(sys.argv[1:]).strip()
        print(f"PERGUNTA: {pergunta}")
        try:
            resposta = answer_question(pergunta, verbose=False)
            print(f"RESPOSTA: {resposta.strip()}")
        except Exception as e:
            print(f"Erro ao processar a pergunta: {e}")
        return

    while True:
        try:
            pergunta = input("PERGUNTA: ").strip()
            if not pergunta:
                continue

            if pergunta.lower() in ["sair", "exit", "quit"]:
                print("Encerrando o chat.")
                break

            resposta = answer_question(pergunta, verbose=False)
            print(f"RESPOSTA: {resposta.strip()}")
            print("\n---")

        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando o chat.")
            break
        except Exception as e:
            print(f"Erro ao processar a pergunta: {e}")


if __name__ == "__main__":
    main()