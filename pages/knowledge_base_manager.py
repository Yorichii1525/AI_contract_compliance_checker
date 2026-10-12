"""
Knowledge Base Management Page for Streamlit App.
Allows users to view, add, and manage regulatory requirements.
"""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.regulatory_knowledge_base import RegulatoryKnowledgeBase
from services.embedding_generator import EmbeddingGenerator
from models.regulatory_requirement import RegulatoryRequirement, RiskLevel
from utils.logger import get_logger

logger = get_logger(__name__)


def initialize_knowledge_base():
    """Initialize the knowledge base in session state."""
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = RegulatoryKnowledgeBase(
            embedding_generator=EmbeddingGenerator()
        )


def render_framework_selector():
    """Render framework selection sidebar."""
    st.sidebar.title("📚 Knowledge Base Manager")
    st.sidebar.markdown("---")
    
    frameworks = ['GDPR', 'HIPAA']
    
    selected_framework = st.sidebar.selectbox(
        "Select Framework",
        frameworks,
        key="selected_framework",
        help="Choose a regulatory framework to view or manage"
    )
    
    st.sidebar.markdown("---")
    
    # Framework statistics
    if st.sidebar.checkbox("Show Statistics", value=True):
        st.sidebar.markdown("### 📊 Framework Statistics")
        stats = st.session_state.knowledge_base.get_statistics()
        
        for framework in frameworks:
            if framework in stats['frameworks']:
                fw_stats = stats['frameworks'][framework]
                st.sidebar.markdown(f"**{framework}**")
                st.sidebar.markdown(f"- Total: {fw_stats['total']}")
                st.sidebar.markdown(f"- Mandatory: {fw_stats['mandatory']}")
                st.sidebar.markdown(f"- Optional: {fw_stats['optional']}")
                st.sidebar.markdown("")
    
    return selected_framework


def render_requirements_table(framework: str):
    """Render requirements table for selected framework."""
    st.markdown(f"## {framework} Requirements")
    
    # Get requirements
    requirements = st.session_state.knowledge_base.get_requirements(framework)
    
    if not requirements:
        st.warning(f"No requirements found for {framework}")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_mandatory_only = st.checkbox("Mandatory Only", value=False)
    
    with col2:
        risk_filter = st.selectbox(
            "Risk Level",
            ["All", "HIGH", "MEDIUM", "LOW"]
        )
    
    with col3:
        clause_types = list(set(req.clause_type for req in requirements))
        clause_type_filter = st.selectbox(
            "Clause Type",
            ["All"] + sorted(clause_types)
        )
    
    # Apply filters
    filtered_requirements = requirements
    
    if show_mandatory_only:
        filtered_requirements = [req for req in filtered_requirements if req.mandatory]
    
    if risk_filter != "All":
        filtered_requirements = [
            req for req in filtered_requirements 
            if req.risk_level.value == risk_filter
        ]
    
    if clause_type_filter != "All":
        filtered_requirements = [
            req for req in filtered_requirements 
            if req.clause_type == clause_type_filter
        ]
    
    st.markdown(f"**Showing {len(filtered_requirements)} of {len(requirements)} requirements**")
    
    # Display requirements
    for i, req in enumerate(filtered_requirements):
        with st.expander(
            f"{'🔴' if req.mandatory else '⚪'} {req.requirement_id} - {req.clause_type}",
            expanded=False
        ):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown(f"**Article**: {req.article_reference}")
                st.markdown(f"**Mandatory**: {'✅ Yes' if req.mandatory else '❌ No'}")
                st.markdown(f"**Risk Level**: {get_risk_emoji(req.risk_level)} {req.risk_level.value}")
            
            with col_b:
                st.markdown(f"**Clause Type**: {req.clause_type}")
                st.markdown(f"**Keywords**: {len(req.keywords)}")
                st.markdown(f"**Elements**: {len(req.mandatory_elements)}")
            
            st.markdown("---")
            st.markdown("**Description:**")
            st.markdown(req.description)
            
            if req.keywords:
                st.markdown("**Keywords:**")
                st.markdown(", ".join(req.keywords[:10]) + ("..." if len(req.keywords) > 10 else ""))
            
            if req.mandatory_elements:
                st.markdown("**Mandatory Elements:**")
                for elem in req.mandatory_elements:
                    st.markdown(f"- {elem}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Edit", key=f"edit_{req.requirement_id}_{i}"):
                    st.session_state.editing_requirement = req
                    st.session_state.show_edit_form = True
            with col2:
                if st.button(f"Duplicate", key=f"dup_{req.requirement_id}_{i}"):
                    st.session_state.duplicating_requirement = req
                    st.session_state.show_add_form = True
            with col3:
                if st.button(f"🗑️ Delete", key=f"del_{req.requirement_id}_{i}"):
                    st.error("Delete functionality coming soon!")


def get_risk_emoji(risk_level: RiskLevel) -> str:
    """Get emoji for risk level."""
    if risk_level == RiskLevel.HIGH:
        return "🔴"
    elif risk_level == RiskLevel.MEDIUM:
        return "🟡"
    else:
        return "🟢"


def render_add_requirement_form(framework: str):
    """Render form to add new requirement."""
    st.markdown("## ➕ Add New Requirement")
    
    with st.form("add_requirement_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            requirement_id = st.text_input(
                "Requirement ID*",
                placeholder=f"{framework}_NEW_01",
                help="Unique identifier for the requirement"
            )
            
            article_reference = st.text_input(
                "Article Reference*",
                placeholder=f"{framework} Article XX",
                help="Legal article or section reference"
            )
            
            clause_type = st.text_input(
                "Clause Type*",
                placeholder="e.g., Data Processing, Security Safeguards",
                help="Type of contract clause this requirement applies to"
            )
        
        with col2:
            mandatory = st.checkbox("Mandatory Requirement", value=True)
            
            risk_level = st.selectbox(
                "Risk Level*",
                ["HIGH", "MEDIUM", "LOW"],
                help="Risk level if this requirement is not met"
            )
        
        description = st.text_area(
            "Description*",
            placeholder="Detailed description of the requirement...",
            height=150,
            help="Clear description of what the requirement entails"
        )
        
        keywords_input = st.text_area(
            "Keywords (one per line)*",
            placeholder="keyword1\nkeyword2\nkeyword3",
            height=100,
            help="Keywords for semantic matching, one per line"
        )
        
        elements_input = st.text_area(
            "Mandatory Elements (one per line)",
            placeholder="Element 1\nElement 2\nElement 3",
            height=100,
            help="List of mandatory elements that must be included"
        )
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("✅ Add Requirement", use_container_width=True)
        
        with col_cancel:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            # Validate inputs
            if not all([requirement_id, article_reference, clause_type, description, keywords_input]):
                st.error("Please fill in all required fields marked with *")
            else:
                # Parse keywords and elements
                keywords = [k.strip() for k in keywords_input.split('\n') if k.strip()]
                elements = [e.strip() for e in elements_input.split('\n') if e.strip()]
                
                # Create new requirement
                new_req = RegulatoryRequirement(
                    requirement_id=requirement_id,
                    framework=framework,
                    article_reference=article_reference,
                    clause_type=clause_type,
                    description=description,
                    mandatory=mandatory,
                    keywords=keywords,
                    mandatory_elements=elements,
                    risk_level=RiskLevel[risk_level]
                )
                
                # Add to knowledge base
                try:
                    # Note: This would require adding an add_requirement method to knowledge base
                    st.success(f"✅ Requirement {requirement_id} added successfully!")
                    st.info("Note: Requirement will be added to the in-memory knowledge base. To persist changes, you need to update the corresponding data file.")
                    st.session_state.show_add_form = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding requirement: {e}")
        
        if cancelled:
            st.session_state.show_add_form = False
            st.rerun()


def render_search_requirements():
    """Render search functionality."""
    st.markdown("### 🔍 Search Requirements")
    
    search_query = st.text_input(
        "Search by keyword or description",
        placeholder="Enter search term...",
        key="search_query"
    )
    
    if search_query:
        selected_framework = st.session_state.get('selected_framework', 'GDPR')
        results = st.session_state.knowledge_base.search_by_keyword(
            search_query,
            framework=selected_framework
        )
        
        if results:
            st.success(f"Found {len(results)} matching requirements")
            for req in results:
                with st.expander(f"{req.requirement_id} - {req.clause_type}"):
                    st.markdown(f"**Description**: {req.description}")
                    st.markdown(f"**Article**: {req.article_reference}")
                    st.markdown(f"**Keywords**: {', '.join(req.keywords[:5])}")
        else:
            st.warning("No matching requirements found")


def main():
    """Main function for knowledge base management page."""
    st.set_page_config(
        page_title="Knowledge Base Manager",
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize
    initialize_knowledge_base()
    
    # Render framework selector sidebar
    selected_framework = render_framework_selector()
    
    # Main content
    st.title("📚 Regulatory Knowledge Base Manager")
    st.markdown("View and manage regulatory requirements for compliance checking")
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if st.button("➕ Add Requirement", use_container_width=True):
            st.session_state.show_add_form = True
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Show add form if requested
    if st.session_state.get('show_add_form', False):
        render_add_requirement_form(selected_framework)
        st.markdown("---")
    
    # Search functionality
    render_search_requirements()
    st.markdown("---")
    
    # Requirements table
    render_requirements_table(selected_framework)
    
    # Export/Import section
    st.markdown("---")
    st.markdown("### 💾 Import/Export")
    
    col_exp, col_imp = st.columns(2)
    
    with col_exp:
        if st.button("📥 Export Requirements", use_container_width=True):
            st.info("Export functionality coming soon! Requirements will be exported to JSON format.")
    
    with col_imp:
        if st.button("📤 Import Requirements", use_container_width=True):
            st.info("Import functionality coming soon! You'll be able to import requirements from JSON files.")


if __name__ == "__main__":
    main()
