import streamlit as st
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.processing.document_processor import GrantDocumentProcessor
from src.rag.vector_store import GrantVectorStore
from src.discovery.grant_scraper import GrantDiscoveryEngine
from src.generation.application_generator import GrantApplicationGenerator

def initialize_system():
    """Initialize the grant application system"""
    if 'initialized' not in st.session_state:
        with st.spinner("Initializing Grant Assistant..."):
            try:
                st.session_state.doc_processor = GrantDocumentProcessor()
                st.session_state.vector_store = GrantVectorStore()
                st.session_state.discovery_engine = GrantDiscoveryEngine()
                st.session_state.generator = GrantApplicationGenerator(st.session_state.vector_store)
                st.session_state.initialized = True
                st.success("System initialized successfully!")
            except Exception as e:
                st.error(f"Initialization failed: {e}")
                st.stop()

def process_documents():
    """Process and index Cambio Labs grant documents"""
    st.subheader("📄 Document Processing")
    
    if st.button("Process Grant Documents"):
        with st.spinner("Processing documents..."):
            try:
                documents = st.session_state.doc_processor.load_grant_documents()
                st.write(f"Loaded {len(documents)} documents:")
                
                for doc in documents:
                    st.write(f"- {doc['filename']} ({doc['grant_type']})")
                
                chunks = st.session_state.doc_processor.get_chunked_content(documents)
                st.write(f"Created {len(chunks)} text chunks")
                
                index = st.session_state.vector_store.index_documents(chunks)
                st.session_state.documents_processed = True
                
                st.success("Documents processed and indexed successfully!")
                
            except Exception as e:
                st.error(f"Error processing documents: {e}")

def discover_grants():
    """Discover relevant grant opportunities"""
    st.subheader("🔍 Grant Discovery")
    
    keywords = st.text_input("Search Keywords", 
                            value="education technology AI workforce nonprofit")
    
    if st.button("Search for Grants"):
        with st.spinner("Searching for grants..."):
            try:
                keyword_list = keywords.split()
                grants = st.session_state.discovery_engine.search_all_sources(keyword_list)
                
                st.session_state.discovered_grants = grants
                
                st.write(f"Found {len(grants)} relevant grants:")
                
                for i, grant in enumerate(grants[:5]):
                    with st.expander(f"{grant['title']} - {grant['organization']}"):
                        st.write(f"**Amount:** {grant.get('amount', 'Not specified')}")
                        st.write(f"**Deadline:** {grant.get('deadline', 'Not specified')}")
                        st.write(f"**Focus Areas:** {', '.join(grant.get('focus_areas', []))}")
                        st.write(f"**Description:** {grant.get('description', 'No description available')}")
                        
                        if 'relevance_score' in grant:
                            st.write(f"**Relevance Score:** {grant['relevance_score']}")
                
            except Exception as e:
                st.error(f"Error discovering grants: {e}")

def generate_application():
    """Generate grant application draft"""
    st.subheader("✍️ Application Generation")
    
    if 'discovered_grants' not in st.session_state or not st.session_state.discovered_grants:
        st.warning("Please discover grants first before generating applications.")
        return
    
    grant_titles = [grant['title'] for grant in st.session_state.discovered_grants]
    selected_title = st.selectbox("Select Grant Opportunity", grant_titles)
    
    if selected_title:
        selected_grant = next(grant for grant in st.session_state.discovered_grants 
                            if grant['title'] == selected_title)
        
        st.write("**Selected Grant:**")
        st.json(selected_grant)
        
        sections = st.multiselect(
            "Sections to Generate",
            ["project_overview", "organizational_background", "project_description", 
             "intended_outcomes", "implementation_plan", "sustainability_plan"],
            default=["project_overview", "project_description"]
        )
        
        if st.button("Generate Application Draft"):
            if not hasattr(st.session_state, 'documents_processed'):
                st.warning("Please process documents first to provide context for generation.")
                return
                
            with st.spinner("Generating application..."):
                try:
                    application = st.session_state.generator.generate_application(
                        selected_grant, sections
                    )
                    
                    st.session_state.generated_application = application
                    
                    st.success("Application draft generated!")
                    
                    for section, content in application.items():
                        st.subheader(section.replace('_', ' ').title())
                        st.write(content)
                        st.write("---")
                    
                except Exception as e:
                    st.error(f"Error generating application: {e}")

def refine_application():
    """Refine the generated application based on feedback"""
    st.subheader("🔧 Application Refinement")
    
    if 'generated_application' not in st.session_state:
        st.warning("Please generate an application first.")
        return
    
    feedback = st.text_area("Provide feedback for refinement:", 
                           placeholder="e.g., Make the impact metrics more specific, add more details about the Journey platform...")
    
    if st.button("Refine Application") and feedback:
        with st.spinner("Refining application..."):
            try:
                refined_app = st.session_state.generator.refine_application(
                    st.session_state.generated_application, feedback
                )
                
                st.subheader("Refined Application:")
                for section, content in refined_app.items():
                    st.subheader(section.replace('_', ' ').title())
                    st.write(content)
                    st.write("---")
                    
            except Exception as e:
                st.error(f"Error refining application: {e}")

def main():
    st.set_page_config(
        page_title="Cambio Labs Grant Assistant",
        page_icon="📋",
        layout="wide"
    )
    
    st.title("🎓 Cambio Labs Grant Application Assistant")
    st.markdown("AI-powered grant discovery and application generation for nonprofit educational initiatives")
    
    initialize_system()
    
    if not st.session_state.get('initialized', False):
        st.stop()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Process Documents", "🔍 Discover Grants", "✍️ Generate Application", "🔧 Refine Application"])
    
    with tab1:
        process_documents()
    
    with tab2:
        discover_grants()
    
    with tab3:
        generate_application()
        
    with tab4:
        refine_application()
    
    st.sidebar.markdown("### System Status")
    if st.session_state.get('initialized', False):
        st.sidebar.success("✅ System Initialized")
    if st.session_state.get('documents_processed', False):
        st.sidebar.success("✅ Documents Processed")
    if st.session_state.get('discovered_grants', []):
        st.sidebar.success(f"✅ Found {len(st.session_state.discovered_grants)} Grants")
    if st.session_state.get('generated_application', {}):
        st.sidebar.success("✅ Application Generated")

if __name__ == "__main__":
    main()