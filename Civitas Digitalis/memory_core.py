import chromadb
from chromadb.utils import embedding_functions
import os
import uuid
import time

class MemoryCore:
    def __init__(self, agent_id, persistence_path="./chroma_db"):
        self.agent_id = agent_id
        # Inicializa o cliente ChromaDB persistente
        self.client = chromadb.PersistentClient(path=persistence_path)
        
        # Usa o modelo padrão de embedding (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Cria ou obtém a coleção para o agente
        self.collection = self.client.get_or_create_collection(
            name=f"memory_{agent_id}",
            embedding_function=self.embedding_fn
        )

    def store_experience(self, text, type="general", metadata=None):
        """
        Armazena uma nova memória.
        """
        if metadata is None:
            metadata = {}
        
        # Adiciona metadados padrão
        metadata.update({
            "type": type,
            "timestamp": time.time(),
            "agent_id": self.agent_id
        })
        
        # Gera um ID único para a memória
        memory_id = str(uuid.uuid4())
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[memory_id]
        )
        # print(f"💾 Memória armazenada: '{text}' (Tipo: {type})")

    def recall_relevant(self, query, n_results=3):
        """
        Recupera memórias relevantes semanticamente.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Retorna apenas os documentos (textos das memórias)
        if results['documents']:
            return results['documents'][0]
        return []

    def clear_memory(self):
        """
        Limpa todas as memórias do agente (útil para testes).
        """
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=f"memory_{self.agent_id}",
            embedding_function=self.embedding_fn
        )
