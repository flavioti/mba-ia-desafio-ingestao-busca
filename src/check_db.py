import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def check_database():
    connection_url = os.getenv("PGVECTOR_URL") or os.getenv("DATABASE_URL")
    collection_name = os.getenv("PG_VECTOR_COLLECTION_NAME", "documents")

    if not connection_url:
        print("❌ Erro: PGVECTOR_URL ou DATABASE_URL não definida no .env")
        return

    print(f"Conectando ao banco de dados...")
    print(f"Coleção alvo: '{collection_name}'\n")

    try:
        engine = create_engine(connection_url)
        with engine.connect() as conn:
            # 1. Verificar se a extensão pgvector está instalada
            ext_result = conn.execute(
                text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
            ).fetchone()

            if ext_result:
                print(f"✅ Extensão vector instalada: versão {ext_result[1]}")
            else:
                print("❌ Extensão vector NÃO está instalada no banco!")

            # 2. Verificar a existência da coleção
            col_result = conn.execute(
                text("SELECT uuid, name FROM langchain_pg_collection WHERE name = :name;"),
                {"name": collection_name}
            ).fetchone()

            if not col_result:
                print(f"⚠️ Coleção '{collection_name}' ainda não existe no banco.")
                return

            collection_uuid = col_result[0]
            print(f"✅ Coleção encontrada (UUID: {collection_uuid})")

            # 3. Contar documentos na coleção
            count_result = conn.execute(
                text("""
                    SELECT count(*)
                    FROM langchain_pg_embedding
                    WHERE collection_id = :uuid;
                """),
                {"uuid": collection_uuid}
            ).scalar()

            print(f"📊 Total de documentos/chunks salvos: {count_result}")

            if count_result > 0:
                # 4. Listar primeiros documentos como amostra
                print("\n--- Amostra dos primeiros 3 documentos ---")
                sample_docs = conn.execute(
                    text("""
                        SELECT id, LEFT(document, 100) AS preview, cmetadata
                        FROM langchain_pg_embedding
                        WHERE collection_id = :uuid
                        ORDER BY id
                        LIMIT 3;
                    """),
                    {"uuid": collection_uuid}
                ).fetchall()

                for row in sample_docs:
                    print(f"  • ID: {row[0]}")
                    print(f"    Conteúdo: {row[1]}...")
                    print(f"    Metadados: {row[2]}\n")

                print("✅ Todos os registros verificados com sucesso no banco!")
            else:
                print("⚠️ A coleção existe, mas nenhum documento foi inserido nela ainda.")

    except Exception as e:
        print(f"❌ Erro ao consultar o banco de dados: {e}")

if __name__ == "__main__":
    check_database()

