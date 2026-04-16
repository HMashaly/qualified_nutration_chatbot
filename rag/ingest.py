"""
RAG Ingestion Pipeline
Run this ONCE to embed knowledge base into ChromaDB:
    python rag/ingest.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

DATA_DIR = Path(__file__).parent.parent / "knowledgebase"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


def ingest():
    print(f"📂 Loading documents from: {DATA_DIR}")

    loader = DirectoryLoader(
        str(DATA_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"✅ Loaded {len(documents)} documents")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=80,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"✂️  Split into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    print("🔄 Embedding and storing in ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="nutribot",
    )

    print(f"✅ Done! Stored {len(chunks)} chunks in {CHROMA_DIR}")
    return vectorstore


def load_vectorstore():
    """Load existing ChromaDB — use this in the app."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="nutribot",
    )


if __name__ == "__main__":
    ingest()