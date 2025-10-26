#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.processing.document_processor import GrantDocumentProcessor
from src.rag.vector_store import GrantVectorStore
from src.discovery.grant_scraper import GrantDiscoveryEngine
from src.generation.application_generator import GrantApplicationGenerator

def test_document_processing():
    print(" Testing Document Processing...")
    
    processor = GrantDocumentProcessor()
    documents = processor.load_grant_documents()
    
    print(f" Loaded {len(documents)} documents:")
    for doc in documents:
        print(f"   - {doc['filename']} ({doc['grant_type']})")
        print(f"     Sections: {len(doc['sections'])}")
        print(f"     Voice elements: {len(doc['organizational_voice'])}")
    
    chunks = processor.get_chunked_content(documents)
    print(f" Created {len(chunks)} text chunks")
    
    return documents, chunks

def test_vector_store(chunks):
    print("\n Testing Vector Store...")
    
    vector_store = GrantVectorStore()
    
    print("   Creating embeddings and indexing documents...")
    index = vector_store.index_documents(chunks)
    print(" Documents indexed successfully")
    
    print("   Testing similarity search...")
    results = vector_store.search_similar("AI education technology workforce", top_k=3)
    print(f" Found {len(results)} similar documents")
    
    for i, result in enumerate(results):
        print(f"   Result {i+1}: {result['text'][:100]}...")
    
    return vector_store

def test_grant_discovery():
    print("\n Testing Grant Discovery...")
    
    discovery = GrantDiscoveryEngine()
    
    print("   Getting sample opportunities...")
    grants = discovery.get_sample_opportunities()
    print(f" Found {len(grants)} sample grants:")
    
    for grant in grants:
        print(f"   - {grant['title']} ({grant['organization']})")
        print(f"     Amount: {grant['amount']}")
        print(f"     Focus: {', '.join(grant['focus_areas'])}")
    
    return grants

def test_application_generation(vector_store, grants):
    print("\n Testing Application Generation...")
    
    generator = GrantApplicationGenerator(vector_store)
    
    test_grant = grants[0] if grants else {
        "title": "Test Grant",
        "organization": "Test Foundation",
        "amount": "$100,000",
        "focus_areas": ["education", "technology"],
        "description": "Test grant for educational technology",
        "requirements": ["Serve underrepresented communities"]
    }
    
    print(f"   Generating application for: {test_grant['title']}")
    
    try:
        application = generator.generate_application(
            test_grant, 
            sections_needed=["project_overview", "project_description"]
        )
        
        print(" Application generated successfully!")
        
        for section, content in application.items():
            print(f"\n {section.replace('_', ' ').title()}:")
            print(content[:200] + "..." if len(content) > 200 else content)
        
        return application
        
    except Exception as e:
        print(f" Error generating application: {e}")
        return None

def run_full_test():
    print(" Starting Cambio Labs Grant Assistant System Test\n")
    
    try:
        documents, chunks = test_document_processing()
        
        vector_store = test_vector_store(chunks)
        
        grants = test_grant_discovery()
        
        application = test_application_generation(vector_store, grants)
        
        if application:
            print("\n All tests passed successfully!")
            print("\nNext steps:")
            print("1. Install Ollama: https://ollama.ai/download")
            print("2. Pull Llama 3.1 8B: ollama pull llama3.1:8b") 
            print("3. Copy .env.example to .env")
            print("4. Install requirements: pip install -r requirements.txt")
            print("5. Run the app: streamlit run app.py")
        else:
            print("\n  Some tests failed - check Ollama setup")
            
    except Exception as e:
        print(f"\n Test failed: {e}")
        print("\nTroubleshooting:")
        print("- Make sure all dependencies are installed")
        print("- Check that example grant documents exist")
        print("- Verify Ollama is running (if testing generation)")

if __name__ == "__main__":
    run_full_test()