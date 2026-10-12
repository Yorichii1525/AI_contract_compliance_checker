"""
User feedback utilities for displaying messages, progress, and guidance.
"""
import streamlit as st
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageType(Enum):
    """Types of user messages."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class UserFeedback:
    """Centralized user feedback management for Streamlit UI."""
    
    @staticmethod
    def show_success(message: str, details: Optional[str] = None):
        """
        Display success message.
        
        Args:
            message: Main success message
            details: Optional additional details
        """
        st.success(f"✅ {message}")
        if details:
            with st.expander("Details"):
                st.info(details)
    
    @staticmethod
    def show_error(
        message: str,
        error: Optional[Exception] = None,
        troubleshooting_tips: Optional[List[str]] = None
    ):
        """
        Display error message with troubleshooting tips.
        
        Args:
            message: Main error message
            error: Optional exception object
            troubleshooting_tips: Optional list of troubleshooting tips
        """
        st.error(f"❌ {message}")
        
        if troubleshooting_tips:
            with st.expander("💡 Troubleshooting Tips"):
                for i, tip in enumerate(troubleshooting_tips, 1):
                    st.markdown(f"{i}. {tip}")
        
        if error and hasattr(error, 'details'):
            with st.expander("🔍 Technical Details"):
                st.json(error.details)
    
    @staticmethod
    def show_warning(message: str, action: Optional[str] = None):
        """
        Display warning message.
        
        Args:
            message: Warning message
            action: Optional recommended action
        """
        st.warning(f"⚠️ {message}")
        if action:
            st.info(f"**Recommended Action:** {action}")
    
    @staticmethod
    def show_info(message: str, icon: str = "ℹ️"):
        """
        Display info message.
        
        Args:
            message: Info message
            icon: Optional icon
        """
        st.info(f"{icon} {message}")
    
    @staticmethod
    def show_validation_error(field: str, message: str):
        """
        Display validation error for a specific field.
        
        Args:
            field: Field name
            message: Validation error message
        """
        st.error(f"❌ **{field}:** {message}")
    
    @staticmethod
    def show_progress(
        message: str,
        progress: Optional[float] = None,
        status: Optional[str] = None
    ):
        """
        Display progress indicator.
        
        Args:
            message: Progress message
            progress: Optional progress value (0.0 to 1.0)
            status: Optional status text
        """
        if progress is not None:
            st.progress(progress, text=message)
        else:
            with st.spinner(message):
                pass
        
        if status:
            st.caption(status)
    
    @staticmethod
    def show_processing_steps(steps: List[Dict[str, Any]]):
        """
        Display multi-step processing progress.
        
        Args:
            steps: List of step dictionaries with 'name', 'status', 'message'
        """
        for step in steps:
            name = step.get('name', 'Step')
            status = step.get('status', 'pending')
            message = step.get('message', '')
            
            if status == 'completed':
                st.success(f"✅ {name}: {message}")
            elif status == 'in_progress':
                st.info(f"🔄 {name}: {message}")
            elif status == 'failed':
                st.error(f"❌ {name}: {message}")
            else:
                st.text(f"⏳ {name}")
    
    @staticmethod
    def show_file_validation_result(
        filename: str,
        is_valid: bool,
        issues: Optional[List[str]] = None
    ):
        """
        Display file validation result.
        
        Args:
            filename: Name of the file
            is_valid: Whether file is valid
            issues: Optional list of validation issues
        """
        if is_valid:
            st.success(f"✅ **{filename}** is valid and ready for processing")
        else:
            st.error(f"❌ **{filename}** has validation issues:")
            if issues:
                for issue in issues:
                    st.markdown(f"- {issue}")
    
    @staticmethod
    def show_analysis_summary(
        total_clauses: int,
        processing_time: float,
        confidence_avg: Optional[float] = None
    ):
        """
        Display analysis summary.
        
        Args:
            total_clauses: Number of clauses analyzed
            processing_time: Processing time in seconds
            confidence_avg: Optional average confidence score
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Clauses Analyzed", total_clauses)
        
        with col2:
            st.metric("Processing Time", f"{processing_time:.2f}s")
        
        with col3:
            if confidence_avg is not None:
                st.metric("Avg Confidence", f"{confidence_avg:.1%}")
    
    @staticmethod
    def show_compliance_alert(
        score: float,
        high_risk_count: int,
        missing_count: int
    ):
        """
        Display compliance alert based on score.
        
        Args:
            score: Compliance score (0-100)
            high_risk_count: Number of high-risk items
            missing_count: Number of missing requirements
        """
        if score >= 90:
            st.success(
                f"🎉 Excellent compliance! Score: {score:.0f}%"
            )
        elif score >= 75:
            st.info(
                f"✅ Good compliance. Score: {score:.0f}%. "
                f"Review {high_risk_count} high-risk items."
            )
        elif score >= 50:
            st.warning(
                f"⚠️ Moderate compliance. Score: {score:.0f}%. "
                f"{high_risk_count} high-risk items and {missing_count} missing requirements need attention."
            )
        else:
            st.error(
                f"❌ Low compliance. Score: {score:.0f}%. "
                f"Immediate action required: {high_risk_count} high-risk items, {missing_count} missing requirements."
            )
    
    @staticmethod
    def show_model_status(
        model_name: str,
        is_loaded: bool,
        error_message: Optional[str] = None
    ):
        """
        Display model loading status.
        
        Args:
            model_name: Name of the model
            is_loaded: Whether model is loaded successfully
            error_message: Optional error message
        """
        if is_loaded:
            st.success(f"✅ {model_name} loaded successfully")
        else:
            st.error(f"❌ Failed to load {model_name}")
            if error_message:
                st.caption(error_message)
    
    @staticmethod
    def show_empty_state(
        title: str,
        message: str,
        action_text: Optional[str] = None
    ):
        """
        Display empty state message.
        
        Args:
            title: Empty state title
            message: Empty state message
            action_text: Optional action guidance
        """
        st.info(f"**{title}**")
        st.write(message)
        if action_text:
            st.caption(f"👉 {action_text}")
    
    @staticmethod
    def show_feature_unavailable(
        feature_name: str,
        reason: str,
        workaround: Optional[str] = None
    ):
        """
        Display feature unavailable message.
        
        Args:
            feature_name: Name of the feature
            reason: Reason why feature is unavailable
            workaround: Optional workaround suggestion
        """
        st.warning(f"⚠️ **{feature_name}** is currently unavailable")
        st.caption(f"Reason: {reason}")
        if workaround:
            st.info(f"💡 Workaround: {workaround}")
    
    @staticmethod
    def show_confirmation_needed(message: str) -> bool:
        """
        Display confirmation dialog.
        
        Args:
            message: Confirmation message
            
        Returns:
            True if user confirms
        """
        return st.checkbox(message, value=False)
    
    @staticmethod
    def show_help_text(topic: str, content: str):
        """
        Display help text in an expander.
        
        Args:
            topic: Help topic
            content: Help content
        """
        with st.expander(f"❓ Help: {topic}"):
            st.markdown(content)
    
    @staticmethod
    def show_quick_tips(tips: List[str]):
        """
        Display quick tips.
        
        Args:
            tips: List of tips
        """
        with st.expander("💡 Quick Tips"):
            for tip in tips:
                st.markdown(f"- {tip}")
    
    @staticmethod
    def show_system_status(
        services: Dict[str, bool],
        overall_status: str = "operational"
    ):
        """
        Display system status.
        
        Args:
            services: Dictionary of service names and their status
            overall_status: Overall system status
        """
        if overall_status == "operational":
            st.success("✅ All systems operational")
        elif overall_status == "degraded":
            st.warning("⚠️ Some services are experiencing issues")
        else:
            st.error("❌ System issues detected")
        
        with st.expander("Service Status"):
            for service, is_up in services.items():
                status_icon = "✅" if is_up else "❌"
                st.text(f"{status_icon} {service}")
    
    @staticmethod
    def show_data_quality_warning(
        issue: str,
        impact: str,
        recommendation: str
    ):
        """
        Display data quality warning.
        
        Args:
            issue: Data quality issue
            impact: Impact of the issue
            recommendation: Recommended action
        """
        st.warning(f"⚠️ **Data Quality Issue:** {issue}")
        st.caption(f"**Impact:** {impact}")
        st.info(f"**Recommendation:** {recommendation}")
    
    @staticmethod
    def show_low_confidence_warning(
        clause_count: int,
        threshold: float
    ):
        """
        Display warning for low confidence predictions.
        
        Args:
            clause_count: Number of low confidence clauses
            threshold: Confidence threshold
        """
        if clause_count > 0:
            st.warning(
                f"⚠️ {clause_count} clause(s) have confidence below {threshold:.0%}. "
                "Manual review is recommended for accurate results."
            )
            with st.expander("Why is confidence low?"):
                st.markdown("""
                Low confidence can occur when:
                - The clause text is ambiguous or unclear
                - The clause doesn't match typical patterns
                - The document quality is poor (e.g., OCR errors)
                - The clause type is uncommon or complex
                
                **Recommendation:** Review these clauses manually to ensure accuracy.
                """)
    
    @staticmethod
    def show_export_options(
        formats: List[str],
        on_export: callable
    ):
        """
        Display export options.
        
        Args:
            formats: List of available export formats
            on_export: Callback function for export action
        """
        st.subheader("📥 Export Results")
        
        selected_format = st.selectbox(
            "Select export format:",
            formats,
            help="Choose the format for exporting analysis results"
        )
        
        if st.button("Export", use_container_width=True):
            on_export(selected_format)
    
    @staticmethod
    def show_rate_limit_warning(
        requests_remaining: int,
        reset_time: str
    ):
        """
        Display rate limit warning.
        
        Args:
            requests_remaining: Number of requests remaining
            reset_time: Time when limit resets
        """
        if requests_remaining < 10:
            st.warning(
                f"⚠️ You have {requests_remaining} requests remaining. "
                f"Limit resets at {reset_time}."
            )
    
    @staticmethod
    def show_maintenance_notice(
        message: str,
        scheduled_time: Optional[str] = None
    ):
        """
        Display maintenance notice.
        
        Args:
            message: Maintenance message
            scheduled_time: Optional scheduled maintenance time
        """
        st.info(f"🔧 **Maintenance Notice:** {message}")
        if scheduled_time:
            st.caption(f"Scheduled for: {scheduled_time}")


class ProgressTracker:
    """Track and display progress for long-running operations."""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of steps
            description: Description of the operation
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.progress_bar = st.progress(0, text=f"{description}...")
        self.status_text = st.empty()
    
    def update(self, step: int, message: str = ""):
        """
        Update progress.
        
        Args:
            step: Current step number
            message: Optional status message
        """
        self.current_step = step
        progress = step / self.total_steps
        
        self.progress_bar.progress(
            progress,
            text=f"{self.description}: Step {step}/{self.total_steps}"
        )
        
        if message:
            self.status_text.caption(message)
    
    def complete(self, message: str = "Complete!"):
        """
        Mark progress as complete.
        
        Args:
            message: Completion message
        """
        self.progress_bar.progress(1.0, text=message)
        self.status_text.success(f"✅ {message}")
    
    def error(self, message: str):
        """
        Mark progress as failed.
        
        Args:
            message: Error message
        """
        self.status_text.error(f"❌ {message}")


class ValidationFeedback:
    """Provide validation feedback for forms and inputs."""
    
    @staticmethod
    def validate_and_show(
        value: Any,
        validator: callable,
        field_name: str
    ) -> bool:
        """
        Validate input and show feedback.
        
        Args:
            value: Value to validate
            validator: Validation function
            field_name: Name of the field
            
        Returns:
            True if valid
        """
        try:
            validator(value)
            return True
        except Exception as e:
            UserFeedback.show_validation_error(field_name, str(e))
            return False
    
    @staticmethod
    def show_field_requirements(field_name: str, requirements: List[str]):
        """
        Show requirements for a field.
        
        Args:
            field_name: Name of the field
            requirements: List of requirements
        """
        with st.expander(f"ℹ️ {field_name} Requirements"):
            for req in requirements:
                st.markdown(f"- {req}")
