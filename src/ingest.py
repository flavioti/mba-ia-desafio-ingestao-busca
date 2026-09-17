import os
from anyio import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_core.documents import Document
from sqlalchemy import text

load_dotenv()

def ingest_pdf(PDF_PATH):
  '''
  Ingests a PDF file, splits it into chunks, and prints the number of chunks created.
  '''
  loader = PyPDFLoader(PDF_PATH)
  docs = loader.load()

  splitter = RecursiveCharacterTextSplitter(
     chunk_size=1000, 
     chunk_overlap=150, 
     add_start_index=False # False because we don't need to keep track of the start index of each chunk in this case
    )

  chunks = splitter.split_documents(docs)

  print(f"Chunks criados: {len(chunks)}")

  enriched = [
     Document(
        page_content=d.page_content,
        metadata={k: v for k, v in d.metadata.items() if v not in ("", None)} 
     )
     for d in chunks
  ]

  ids = [f"doc-{i}" for i in range(len(enriched))]

  embeddings = OpenAIEmbeddings(
     model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
  )

  store = PGVector(
     embeddings=embeddings,
     collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME", "documents"),
     connection=os.getenv("PGVECTOR_URL") or os.getenv("DATABASE_URL"),
     use_jsonb=True,
  )

  store.add_documents(enriched, ids=ids)

if __name__ == "__main__":
    ingest_pdf('document.pdf')
