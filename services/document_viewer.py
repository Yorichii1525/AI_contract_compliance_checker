"""
Document viewer service for displaying contracts with visual highlighting.
"""
from typing import List, Dict, Optional, Tuple
from models.clause import Clause
from models.processed_document import ProcessedDocument


class RiskLevel:
    """Risk level constants."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DocumentViewer:
    """
    Service for creating highlighted document views with risk-based color coding.
    """
    
    def __init__(self):
        """Initialize document viewer."""
        self.risk_colors = {
            RiskLevel.HIGH: "#ff6b6b",      # Red
            RiskLevel.MEDIUM: "#ffd166",    # Yellow
            RiskLevel.LOW: "#06d6a0"        # Green
        }
        
        self.risk_text_colors = {
            RiskLevel.HIGH: "#ffffff",      # White text for red background
            RiskLevel.MEDIUM: "#000000",    # Black text for yellow background
            RiskLevel.LOW: "#ffffff"        # White text for green background
        }
    
    def create_highlighted_html(
        self,
        processed_doc: ProcessedDocument,
        clause_risk_map: Dict[str, str],
        clause_details_map: Optional[Dict[str, Dict]] = None
    ) -> str:
        """
        Create HTML with highlighted clauses based on risk levels.
        
        Args:
            processed_doc: The processed document
            clause_risk_map: Dictionary mapping clause_id to risk level (High/Medium/Low)
            clause_details_map: Optional dictionary with clause details for tooltips
                               (compliance_status, issues, etc.)
            
        Returns:
            HTML string with highlighted text
        """
        # Get the original text
        text = processed_doc.extracted_text
        
        # Create list of (position, clause_id, risk_level) tuples
        highlights = []
        for clause in processed_doc.clauses:
            if clause.clause_id in clause_risk_map:
                risk_level = clause_risk_map[clause.clause_id]
                highlights.append((
                    clause.start_position,
                    clause.end_position,
                    clause.clause_id,
                    risk_level
                ))
        
        # Sort by start position
        highlights.sort(key=lambda x: x[0])
        
        # Build HTML with highlights
        html_parts = []
        last_pos = 0
        
        for start_pos, end_pos, clause_id, risk_level in highlights:
            # Add text before highlight
            if start_pos > last_pos:
                html_parts.append(self._escape_html(text[last_pos:start_pos]))
            
            # Add highlighted text
            clause_text = text[start_pos:end_pos]
            bg_color = self.risk_colors.get(risk_level, "#cccccc")
            text_color = self.risk_text_colors.get(risk_level, "#000000")
            
            # Build tooltip content
            tooltip_content = self._build_tooltip_content(
                clause_id, risk_level, clause_details_map
            )
            
            # Get clause details for data attributes
            clause_details = clause_details_map.get(clause_id, {}) if clause_details_map else {}
            compliance_status = clause_details.get('compliance_status', 'Unknown')
            clause_type = clause_details.get('clause_type', 'Unknown')
            
            html_parts.append(
                f'<span class="highlighted-clause tooltip-trigger clickable-clause" '
                f'data-clause-id="{clause_id}" '
                f'data-risk-level="{risk_level}" '
                f'data-compliance-status="{self._escape_html(compliance_status)}" '
                f'data-clause-type="{self._escape_html(clause_type)}" '
                f'style="background-color: {bg_color}; color: {text_color}; '
                f'padding: 2px 4px; border-radius: 3px; cursor: pointer; '
                f'transition: all 0.2s; position: relative;" '
                f'onmouseover="this.style.opacity=\'0.8\'; this.style.transform=\'scale(1.02)\';" '
                f'onmouseout="this.style.opacity=\'1\'; this.style.transform=\'scale(1)\';" '
                f'title="Click to view details">'
                f'{self._escape_html(clause_text)}'
                f'<span class="tooltip-content">{tooltip_content}</span>'
                f'</span>'
            )
            
            last_pos = end_pos
        
        # Add remaining text
        if last_pos < len(text):
            html_parts.append(self._escape_html(text[last_pos:]))
        
        # Wrap in container with styling
        html = f"""
        <div class="document-viewer" style="
            font-family: 'Georgia', serif;
            line-height: 1.8;
            padding: 20px;
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        ">
            {''.join(html_parts)}
        </div>
        """
        
        return html
    
    def create_clause_position_map(
        self,
        processed_doc: ProcessedDocument
    ) -> Dict[str, Tuple[int, int]]:
        """
        Create a mapping of clause IDs to their positions in the document.
        
        Args:
            processed_doc: The processed document
            
        Returns:
            Dictionary mapping clause_id to (start_position, end_position)
        """
        position_map = {}
        for clause in processed_doc.clauses:
            position_map[clause.clause_id] = (
                clause.start_position,
                clause.end_position
            )
        return position_map
    
    def get_css_styles(self) -> str:
        """
        Get CSS styles for the document viewer.
        
        Returns:
            CSS string
        """
        return """
        <style>
            .document-viewer {
                font-family: 'Georgia', serif;
                line-height: 1.8;
                padding: 20px;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                max-height: 600px;
                overflow-y: auto;
            }
            
            .highlighted-clause {
                padding: 2px 4px;
                border-radius: 3px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: inline;
                position: relative;
            }
            
            .highlighted-clause:hover {
                opacity: 0.8;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                transform: scale(1.02);
            }
            
            .highlighted-clause:active {
                transform: scale(0.98);
            }
            
            .clickable-clause {
                text-decoration: underline;
                text-decoration-style: dotted;
                text-decoration-color: rgba(255,255,255,0.5);
            }
            
            .tooltip-trigger {
                position: relative;
            }
            
            .tooltip-content {
                visibility: hidden;
                opacity: 0;
                position: absolute;
                z-index: 1000;
                bottom: 125%;
                left: 50%;
                transform: translateX(-50%);
                background-color: #333;
                color: #fff;
                text-align: left;
                padding: 10px 12px;
                border-radius: 6px;
                font-size: 13px;
                line-height: 1.5;
                white-space: nowrap;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                transition: opacity 0.3s, visibility 0.3s;
                pointer-events: none;
                min-width: 200px;
                max-width: 350px;
                white-space: normal;
            }
            
            .tooltip-content::after {
                content: "";
                position: absolute;
                top: 100%;
                left: 50%;
                transform: translateX(-50%);
                border-width: 6px;
                border-style: solid;
                border-color: #333 transparent transparent transparent;
            }
            
            .tooltip-trigger:hover .tooltip-content {
                visibility: visible;
                opacity: 1;
            }
            
            /* Adjust tooltip position if it would overflow */
            .tooltip-trigger:hover .tooltip-content {
                max-width: min(350px, 90vw);
            }
            
            .risk-high-bg {
                background-color: #ff6b6b;
                color: #ffffff;
            }
            
            .risk-medium-bg {
                background-color: #ffd166;
                color: #000000;
            }
            
            .risk-low-bg {
                background-color: #06d6a0;
                color: #ffffff;
            }
            
            .document-viewer::-webkit-scrollbar {
                width: 8px;
            }
            
            .document-viewer::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }
            
            .document-viewer::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }
            
            .document-viewer::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        </style>
        """
    
    def _build_tooltip_content(
        self,
        clause_id: str,
        risk_level: str,
        clause_details_map: Optional[Dict[str, Dict]]
    ) -> str:
        """
        Build tooltip content for a clause.
        
        Args:
            clause_id: The clause ID
            risk_level: The risk level
            clause_details_map: Optional details map
            
        Returns:
            HTML string for tooltip
        """
        if not clause_details_map or clause_id not in clause_details_map:
            return f"<strong>Risk:</strong> {risk_level}<br><em>Click for details</em>"
        
        details = clause_details_map[clause_id]
        compliance_status = details.get('compliance_status', 'Unknown')
        issues = details.get('issues', [])
        clause_type = details.get('clause_type', 'Unknown')
        
        tooltip_parts = [
            f"<strong>Clause Type:</strong> {self._escape_html(clause_type)}<br>",
            f"<strong>Risk Level:</strong> {risk_level}<br>",
            f"<strong>Status:</strong> {self._escape_html(compliance_status)}<br>"
        ]
        
        if issues:
            issue_text = issues[0] if len(issues) == 1 else f"{len(issues)} issues found"
            tooltip_parts.append(f"<strong>Issue:</strong> {self._escape_html(issue_text)}<br>")
        
        tooltip_parts.append("<em>Click for full details</em>")
        
        return ''.join(tooltip_parts)
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def get_click_handler_javascript(self) -> str:
        """
        Get JavaScript code for handling click events on clauses and missing requirements.
        
        Returns:
            JavaScript code as string
        """
        return """
        <script>
            // Store selected clause ID
            let selectedClauseId = null;
            
            // Function to handle clause click
            function handleClauseClick(clauseId) {
                selectedClauseId = clauseId;
                
                // Switch to clause list view if in document view
                const viewModeRadio = document.querySelector('input[value="Clause List"]');
                if (viewModeRadio) {
                    viewModeRadio.click();
                }
                
                // Wait for view to switch, then scroll
                setTimeout(() => {
                    const clauseElement = document.getElementById('clause-details-' + clauseId);
                    if (clauseElement) {
                        clauseElement.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                        
                        // Highlight the expander briefly
                        const expander = clauseElement.nextElementSibling;
                        if (expander) {
                            expander.style.backgroundColor = '#fff3cd';
                            setTimeout(() => {
                                expander.style.backgroundColor = '';
                            }, 2000);
                        }
                    }
                }, 500);
            }
            
            // Function to handle missing clause click
            function handleMissingClauseClick(reqId) {
                // Scroll to missing requirements section
                const missingSection = document.querySelector('h3:contains("Missing Required Clauses")');
                if (missingSection) {
                    missingSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                
                // Find and expand the corresponding expander
                setTimeout(() => {
                    const expanders = document.querySelectorAll('[data-testid="stExpander"]');
                    expanders.forEach(expander => {
                        const text = expander.textContent;
                        if (text.includes(reqId)) {
                            const button = expander.querySelector('button');
                            if (button && button.getAttribute('aria-expanded') === 'false') {
                                button.click();
                            }
                            expander.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    });
                }, 500);
            }
            
            // Add event listeners when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeClickHandlers);
            } else {
                initializeClickHandlers();
            }
            
            function initializeClickHandlers() {
                // Add click handlers to highlighted clauses
                const clauses = document.querySelectorAll('.clickable-clause');
                clauses.forEach(clause => {
                    clause.addEventListener('click', function(e) {
                        e.preventDefault();
                        const clauseId = this.getAttribute('data-clause-id');
                        
                        // Visual feedback
                        this.style.boxShadow = '0 0 15px rgba(0,0,0,0.5)';
                        setTimeout(() => {
                            this.style.boxShadow = '';
                        }, 300);
                        
                        handleClauseClick(clauseId);
                    });
                });
                
                // Add click handlers to missing clause cards
                const missingCards = document.querySelectorAll('.clickable-missing-clause');
                missingCards.forEach(card => {
                    card.addEventListener('click', function(e) {
                        e.preventDefault();
                        const reqId = this.getAttribute('data-req-id');
                        
                        // Visual feedback
                        this.style.transform = 'scale(0.95)';
                        setTimeout(() => {
                            this.style.transform = '';
                        }, 200);
                        
                        handleMissingClauseClick(reqId);
                    });
                });
            }
            
            // Re-initialize handlers when Streamlit reruns
            const observer = new MutationObserver(function(mutations) {
                initializeClickHandlers();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        </script>
        """
    
    def create_legend_html(self) -> str:
        """
        Create HTML legend for risk levels.
        
        Returns:
            HTML string for legend
        """
        return """
        <div style="display: flex; gap: 20px; margin-bottom: 15px; padding: 10px; 
                    background-color: #f8f9fa; border-radius: 5px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="display: inline-block; width: 20px; height: 20px; 
                             background-color: #ff6b6b; border-radius: 3px;"></span>
                <span style="font-size: 14px; font-weight: 500;">High Risk</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="display: inline-block; width: 20px; height: 20px; 
                             background-color: #ffd166; border-radius: 3px;"></span>
                <span style="font-size: 14px; font-weight: 500;">Medium Risk</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="display: inline-block; width: 20px; height: 20px; 
                             background-color: #06d6a0; border-radius: 3px;"></span>
                <span style="font-size: 14px; font-weight: 500;">Low Risk</span>
            </div>
            <div style="margin-left: auto; font-size: 13px; color: #6c757d; font-style: italic;">
                💡 Click on highlighted clauses or missing items to view details
            </div>
        </div>
        """
    
    def create_missing_clauses_panel(
        self,
        missing_requirements: List,
        recommendations: List
    ) -> str:
        """
        Create HTML for missing clauses side panel.
        
        Args:
            missing_requirements: List of missing regulatory requirements
            recommendations: List of recommendations for missing clauses
            
        Returns:
            HTML string for missing clauses panel
        """
        if not missing_requirements:
            return """
            <div style="padding: 20px; background-color: #d4edda; border: 1px solid #c3e6cb; 
                        border-radius: 8px; color: #155724;">
                <h4 style="margin-top: 0;">✅ All Required Clauses Present</h4>
                <p style="margin-bottom: 0;">No missing clauses detected for the selected frameworks.</p>
            </div>
            """
        
        # Group recommendations by requirement
        rec_by_req = {}
        for rec in recommendations:
            if rec.clause_id is None:  # Missing clause recommendation
                req_id = rec.requirement.requirement_id
                rec_by_req[req_id] = rec
        
        # Build panel HTML
        panel_html = [
            '<div class="missing-clauses-panel" style="background-color: #fff3cd; border: 1px solid #ffc107; '
            'border-radius: 8px; padding: 15px; max-height: 600px; overflow-y: auto;">',
            '<h4 style="margin-top: 0; color: #856404; display: flex; align-items: center; gap: 8px;">',
            '<span style="font-size: 24px;">⚠️</span>',
            f'Missing Clauses ({len(missing_requirements)})',
            '</h4>',
            '<p style="color: #856404; margin-bottom: 15px; font-size: 14px;">',
            'The following required clauses are missing from the contract:',
            '</p>'
        ]
        
        # Sort by priority (if available in recommendations)
        sorted_requirements = sorted(
            missing_requirements,
            key=lambda req: rec_by_req.get(req.requirement_id, type('obj', (), {'priority': 5})).priority
        )
        
        for req in sorted_requirements:
            req_id = req.requirement_id
            rec = rec_by_req.get(req_id)
            
            # Determine priority indicator
            priority = rec.priority if rec else 3
            if priority <= 2:
                priority_badge = '<span style="background-color: #dc3545; color: white; padding: 2px 8px; ' \
                                'border-radius: 12px; font-size: 11px; font-weight: bold;">HIGH PRIORITY</span>'
            elif priority == 3:
                priority_badge = '<span style="background-color: #ffc107; color: black; padding: 2px 8px; ' \
                                'border-radius: 12px; font-size: 11px; font-weight: bold;">MEDIUM</span>'
            else:
                priority_badge = '<span style="background-color: #28a745; color: white; padding: 2px 8px; ' \
                                'border-radius: 12px; font-size: 11px; font-weight: bold;">LOW</span>'
            
            # Build requirement card
            panel_html.append(
                f'<div class="missing-clause-card clickable-missing-clause" data-req-id="{self._escape_html(req_id)}" '
                f'style="background-color: white; border: 1px solid #dee2e6; border-radius: 6px; '
                f'padding: 12px; margin-bottom: 12px; cursor: pointer; '
                f'transition: all 0.2s ease; position: relative;" '
                f'onmouseover="this.style.boxShadow=\'0 4px 12px rgba(0,0,0,0.2)\'; this.style.transform=\'translateY(-2px)\';" '
                f'onmouseout="this.style.boxShadow=\'none\'; this.style.transform=\'translateY(0)\';" '
                f'onclick="handleMissingClauseClick(\'{self._escape_html(req_id)}\')">'
            )
            
            # Header with priority
            panel_html.append(
                f'<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">'
                f'<strong style="color: #495057; font-size: 14px;">{self._escape_html(req.clause_type)}</strong>'
                f'{priority_badge}'
                f'</div>'
            )
            
            # Regulatory reference
            panel_html.append(
                f'<div style="color: #6c757d; font-size: 12px; margin-bottom: 8px;">'
                f'📋 {self._escape_html(req.article_reference)} ({self._escape_html(req.framework)})'
                f'</div>'
            )
            
            # Description
            description = req.description[:100] + "..." if len(req.description) > 100 else req.description
            panel_html.append(
                f'<div style="color: #495057; font-size: 13px; margin-bottom: 8px; line-height: 1.4;">'
                f'{self._escape_html(description)}'
                f'</div>'
            )
            
            # Suggested text preview (if available)
            if rec and rec.suggested_text:
                preview = rec.suggested_text[:80] + "..." if len(rec.suggested_text) > 80 else rec.suggested_text
                panel_html.append(
                    f'<div style="background-color: #f8f9fa; border-left: 3px solid #007bff; '
                    f'padding: 8px; margin-top: 8px; font-size: 12px; font-style: italic; color: #495057;">'
                    f'<strong>Suggested:</strong> {self._escape_html(preview)}'
                    f'</div>'
                )
            
            # Click hint
            panel_html.append(
                '<div style="color: #007bff; font-size: 11px; margin-top: 8px; text-align: right;">'
                '👆 Click to view full recommendation'
                '</div>'
            )
            
            panel_html.append('</div>')
        
        panel_html.append('</div>')
        
        return ''.join(panel_html)
