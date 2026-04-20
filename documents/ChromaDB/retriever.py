"""
RAG Retriever — wraps ChromaDB as a LangChain Tool
"""

from langchain.tools import tool
from langchain_core.documents import Document
from typing import List


def get_rag_tool(vectorstore):
    """
    Factory: returns a LangChain tool bound to the given vectorstore.
    Call this once at startup, pass to create_agent.
    """

    @tool
    def search_nutrition_knowledge(query: str) -> str:
        """
        Search the qualified_nutration_chatbot knowledge base for nutrition information.
        Use this for questions about healthy eating, weight loss, dietary guidelines,
        vegan/vegetarian nutrition, halal food rules, food allergies, meal planning,
        macronutrients, vitamins, and general diet advice.
        Always use this tool before answering nutrition questions.
        """
        docs: List[Document] = vectorstore.similarity_search(query, k=4)
        if not docs:
            return "No relevant information found in the knowledge base."

        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            # Clean up the source path to just the filename
            source_name = source.split("/")[-1].replace(".md", "").replace("_", " ").title()
            results.append(f"[Source: {source_name}]\n{doc.page_content.strip()}")

        return "\n\n---\n\n".join(results)

    return search_nutrition_knowledge


def get_retrieved_docs(vectorstore, query: str, k: int = 4) -> List[Document]:
    """Direct retrieval for displaying sources in the UI."""
    return vectorstore.similarity_search(query, k=k)
