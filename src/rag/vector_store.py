import os
from typing import List, Dict, Any, Optional
import chromadb
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from config.settings import settings

class GrantVectorStore:
    def __init__(self, persist_dir: str = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.embedding_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model
        )
        
        self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
        
        try:
            self.chroma_collection = self.chroma_client.get_collection("grant_documents")
        except:
            self.chroma_collection = self.chroma_client.create_collection("grant_documents")
        
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        self.node_parser = SentenceSplitter(
            chunk_size=settings.max_chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
    
    def index_documents(self, chunks: List[Dict[str, Any]]) -> VectorStoreIndex:
        documents = []
        
        for chunk in chunks:
            doc = Document(
                text=chunk["text"],
                metadata=chunk["metadata"]
            )
            documents.append(doc)
        
        nodes = self.node_parser.get_nodes_from_documents(documents)
        
        try:
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context,
                embed_model=self.embedding_model
            )
            
            for node in nodes:
                index.insert(node)
        except:
            index = VectorStoreIndex(
                nodes=nodes,
                storage_context=self.storage_context,
                embed_model=self.embedding_model
            )
        
        return index
    
    def get_existing_index(self) -> Optional[VectorStoreIndex]:
        try:
            index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context,
                embed_model=self.embedding_model
            )
            return index
        except:
            return None
    
    def search_similar(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        top_k = top_k or settings.top_k_retrieval
        
        index = self.get_existing_index()
        if not index:
            return []
        
        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        
        results = []
        for node in nodes:
            results.append({
                "text": node.text,
                "metadata": node.metadata,
                "score": node.score if hasattr(node, 'score') else None
            })
        
        return results
    
    def get_organizational_voice_examples(self, voice_type: str = None) -> List[str]:
        if voice_type:
            query = f"organizational voice {voice_type} mission BIPOC underestimated"
        else:
            query = "Cambio Labs mission underestimated BIPOC youth adults Journey platform"
        
        results = self.search_similar(query, top_k=10)
        return [result["text"] for result in results if result["text"]]
    
    def clear_index(self):
        self.chroma_client.delete_collection("grant_documents")
        self.chroma_collection = self.chroma_client.create_collection("grant_documents")
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)