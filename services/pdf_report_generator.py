"""
PDF Report Generator - Create professional compliance reports.

Generates industry-standard PDF reports with:
- Executive summary
- Compliance scores and metrics
- Risk heatmaps and visualizations
- Clause-by-clause analysis
- Recommendations and next steps
"""
import os
import io
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.colors import HexColor

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


class PDFReportGenerator:
    """Generate professional PDF compliance reports."""
    
    # Brand colors (can be customized)
    PRIMARY_COLOR = HexColor('#1E3A8A')      # Navy blue
    SECONDARY_COLOR = HexColor('#3B82F6')    # Blue
    SUCCESS_COLOR = HexColor('#10B981')      # Green
    WARNING_COLOR = HexColor('#F59E0B')      # Orange
    DANGER_COLOR = HexColor('#EF4444')       # Red
    NEUTRAL_COLOR = HexColor('#6B7280')      # Gray
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize PDF report generator.
        
        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
        logger.info("PDF Report Generator initialized")
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderColor=self.PRIMARY_COLOR,
            borderPadding=5
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=13,
            textColor=self.SECONDARY_COLOR,
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Highlight style for important info
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.NEUTRAL_COLOR,
            alignment=TA_CENTER
        ))
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page."""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(self.PRIMARY_COLOR)
        canvas_obj.drawString(inch, letter[1] - 0.5 * inch, "Contract Compliance Report")
        
        # Footer
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(self.NEUTRAL_COLOR)
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        canvas_obj.drawString(inch, 0.5 * inch, footer_text)
        canvas_obj.drawRightString(
            letter[0] - inch, 
            0.5 * inch, 
            f"Page {doc.page}"
        )
        
        canvas_obj.restoreState()
    
    def _create_risk_gauge_chart(
        self,
        compliance_score: float,
        width: int = 400,
        height: int = 250
    ) -> str:
        """
        Create a compliance score gauge chart.
        
        Args:
            compliance_score: Score from 0-100
            width: Chart width in pixels
            height: Chart height in pixels
            
        Returns:
            Path to saved chart image
        """
        fig, ax = plt.subplots(figsize=(width/100, height/100), subplot_kw={'projection': 'polar'})
        
        # Create gauge
        theta = np.linspace(0, np.pi, 100)
        scores = np.linspace(0, 100, 100)
        
        # Color zones
        colors_zones = ['#EF4444', '#F59E0B', '#10B981']  # Red, Orange, Green
        zone_ranges = [(0, 60), (60, 80), (80, 100)]
        
        for color, (start, end) in zip(colors_zones, zone_ranges):
            # Check if score falls in this zone
            if start <= compliance_score <= end:
                ax.fill_between(
                    theta,
                    0, 1,
                    where=(scores >= start) & (scores <= end),
                    color=color,
                    alpha=0.3
                )
        
        # Add score needle
        score_angle = np.pi * (1 - compliance_score / 100)
        ax.plot([score_angle, score_angle], [0, 0.9], 'k-', linewidth=3)
        ax.plot(score_angle, 0.9, 'ko', markersize=10)
        
        # Styling
        ax.set_ylim(0, 1)
        ax.set_xticks([0, np.pi/2, np.pi])
        ax.set_xticklabels(['100', '50', '0'], fontsize=12)
        ax.set_yticks([])
        ax.spines['polar'].set_visible(False)
        
        # Add score text
        ax.text(
            np.pi/2, 0.3, f'{compliance_score:.1f}%',
            ha='center', va='center',
            fontsize=32, fontweight='bold',
            color='#1E3A8A'
        )
        
        ax.set_title('Compliance Score', fontsize=14, fontweight='bold', pad=20)
        
        # Save to temp file
        temp_path = self.output_dir / f"gauge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(temp_path, dpi=100, bbox_inches='tight', transparent=True)
        plt.close()
        
        return str(temp_path)
    
    def _create_risk_distribution_chart(
        self,
        risk_counts: Dict[str, int],
        width: int = 500,
        height: int = 300
    ) -> str:
        """
        Create a bar chart showing risk distribution.
        
        Args:
            risk_counts: Dictionary with risk levels and counts
            width: Chart width in pixels
            height: Chart height in pixels
            
        Returns:
            Path to saved chart image
        """
        fig, ax = plt.subplots(figsize=(width/100, height/100))
        
        risk_levels = ['High', 'Medium', 'Low']
        counts = [risk_counts.get(level.lower(), 0) for level in risk_levels]
        colors_bar = ['#EF4444', '#F59E0B', '#10B981']
        
        bars = ax.bar(risk_levels, counts, color=colors_bar, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height_bar = bar.get_height()
            if height_bar > 0:
                ax.text(
                    bar.get_x() + bar.get_width()/2., height_bar,
                    f'{int(height_bar)}',
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold'
                )
        
        ax.set_ylabel('Number of Issues', fontsize=12, fontweight='bold')
        ax.set_xlabel('Risk Level', fontsize=12, fontweight='bold')
        ax.set_title('Risk Distribution', fontsize=14, fontweight='bold', pad=15)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Save to temp file
        temp_path = self.output_dir / f"risk_dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(temp_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return str(temp_path)
    
    def _create_framework_compliance_chart(
        self,
        framework_scores: Dict[str, float],
        width: int = 500,
        height: int = 300
    ) -> str:
        """
        Create a horizontal bar chart for framework-specific compliance.
        
        Args:
            framework_scores: Dictionary with framework names and scores
            width: Chart width in pixels
            height: Chart height in pixels
            
        Returns:
            Path to saved chart image
        """
        if not framework_scores:
            return None
        
        fig, ax = plt.subplots(figsize=(width/100, height/100))
        
        frameworks = list(framework_scores.keys())
        scores = list(framework_scores.values())
        
        # Color based on score
        bar_colors = [
            '#10B981' if score >= 80 else '#F59E0B' if score >= 60 else '#EF4444'
            for score in scores
        ]
        
        bars = ax.barh(frameworks, scores, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Add value labels
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(
                score + 2, bar.get_y() + bar.get_height()/2,
                f'{score:.1f}%',
                va='center',
                fontsize=11,
                fontweight='bold'
            )
        
        ax.set_xlabel('Compliance Score (%)', fontsize=12, fontweight='bold')
        ax.set_title('Framework Compliance Breakdown', fontsize=14, fontweight='bold', pad=15)
        ax.set_xlim(0, 105)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Save to temp file
        temp_path = self.output_dir / f"framework_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(temp_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return str(temp_path)
    
    def _get_risk_color(self, risk_level: str) -> HexColor:
        """Get color for risk level."""
        risk_colors = {
            'high': self.DANGER_COLOR,
            'critical': self.DANGER_COLOR,
            'medium': self.WARNING_COLOR,
            'low': self.SUCCESS_COLOR,
            'info': self.NEUTRAL_COLOR
        }
        return risk_colors.get(risk_level.lower(), self.NEUTRAL_COLOR)
    
    def _get_score_status(self, score: float) -> tuple[str, HexColor]:
        """Get status text and color based on compliance score."""
        if score >= 90:
            return "Excellent", self.SUCCESS_COLOR
        elif score >= 80:
            return "Good", self.SUCCESS_COLOR
        elif score >= 70:
            return "Fair", self.WARNING_COLOR
        elif score >= 60:
            return "Needs Improvement", self.WARNING_COLOR
        else:
            return "Critical", self.DANGER_COLOR
    
    def generate_compliance_report(
        self,
        analysis_results: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive compliance report PDF.
        
        Args:
            analysis_results: Dictionary containing:
                - contract_name: str
                - compliance_score: float (0-100)
                - framework: str
                - processed_at: str (timestamp)
                - total_clauses: int
                - compliant_clauses: int
                - non_compliant_clauses: int
                - missing_clauses: int
                - risk_distribution: Dict[str, int]
                - clause_analysis: List[Dict] (detailed clause results)
                - recommendations: List[str]
                - executive_summary: str (optional)
            output_filename: Custom filename for the PDF
            
        Returns:
            Path to generated PDF file
        """
        # Generate filename
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            contract_name = analysis_results.get('contract_name', 'contract').replace('.pdf', '')
            output_filename = f"compliance_report_{contract_name}_{timestamp}.pdf"
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Container for PDF elements
        story = []
        
        # ===== COVER PAGE =====
        story.append(Spacer(1, 1.5*inch))
        
        # Title
        title = Paragraph(
            "Contract Compliance Analysis Report",
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Contract name
        contract_name = Paragraph(
            f"<b>{analysis_results.get('contract_name', 'N/A')}</b>",
            self.styles['Heading2']
        )
        story.append(contract_name)
        story.append(Spacer(1, 0.5*inch))
        
        # Key metrics box
        compliance_score = analysis_results.get('compliance_score', 0)
        status, status_color = self._get_score_status(compliance_score)
        
        metrics_data = [
            ['Compliance Score', f'{compliance_score:.1f}%'],
            ['Status', status],
            ['Framework', analysis_results.get('framework', 'N/A')],
            ['Analysis Date', datetime.now().strftime('%B %d, %Y')],
            ['Total Clauses', str(analysis_results.get('total_clauses', 0))],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, self.PRIMARY_COLOR),
            ('BACKGROUND', (1, 1), (1, 1), status_color),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
        ]))
        
        story.append(metrics_table)
        story.append(PageBreak())
        
        # ===== EXECUTIVE SUMMARY =====
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        exec_summary = analysis_results.get('executive_summary', 
            f"This report provides a comprehensive analysis of the contract's compliance with {analysis_results.get('framework', 'regulatory')} requirements. "
            f"The overall compliance score of {compliance_score:.1f}% indicates a {status.lower()} level of compliance."
        )
        
        story.append(Paragraph(exec_summary, self.styles['ReportBody']))
        story.append(Spacer(1, 0.2*inch))
        
        # Compliance Score Gauge
        gauge_path = self._create_risk_gauge_chart(compliance_score)
        if gauge_path and os.path.exists(gauge_path):
            story.append(Image(gauge_path, width=4*inch, height=2.5*inch))
            story.append(Spacer(1, 0.2*inch))
        
        # ===== COMPLIANCE OVERVIEW =====
        story.append(Paragraph("Compliance Overview", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        overview_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Compliant Clauses', 
             str(analysis_results.get('compliant_clauses', 0)),
             f"{(analysis_results.get('compliant_clauses', 0) / max(analysis_results.get('total_clauses', 1), 1) * 100):.1f}%"],
            ['Non-Compliant Clauses',
             str(analysis_results.get('non_compliant_clauses', 0)),
             f"{(analysis_results.get('non_compliant_clauses', 0) / max(analysis_results.get('total_clauses', 1), 1) * 100):.1f}%"],
            ['Missing Clauses',
             str(analysis_results.get('missing_clauses', 0)),
             'N/A'],
        ]
        
        overview_table = Table(overview_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(overview_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Risk Distribution Chart
        risk_distribution = analysis_results.get('risk_distribution', {})
        if risk_distribution:
            risk_chart_path = self._create_risk_distribution_chart(risk_distribution)
            if risk_chart_path and os.path.exists(risk_chart_path):
                story.append(Image(risk_chart_path, width=5*inch, height=3*inch))
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
        
        # ===== DETAILED CLAUSE ANALYSIS =====
        story.append(Paragraph("Detailed Clause Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        clause_analysis = analysis_results.get('clause_analysis', [])
        
        for i, clause in enumerate(clause_analysis[:20], 1):  # Limit to 20 clauses
            clause_elements = []
            
            # Clause header
            risk_level = clause.get('risk_level', 'low')
            clause_header = Paragraph(
                f"<b>Clause {i}: {clause.get('clause_id', f'Clause {i}')}</b> "
                f"<font color='{self._get_risk_color(risk_level)}'>({risk_level.upper()} RISK)</font>",
                self.styles['SubsectionHeader']
            )
            clause_elements.append(clause_header)
            
            # Clause text (truncated if too long)
            clause_text = clause.get('clause_text', 'N/A')
            if len(clause_text) > 300:
                clause_text = clause_text[:297] + "..."
            
            clause_elements.append(Paragraph(
                f"<i>{clause_text}</i>",
                self.styles['ReportBody']
            ))
            clause_elements.append(Spacer(1, 0.1*inch))
            
            # Compliance status
            is_compliant = clause.get('is_compliant', False)
            status_text = "✓ Compliant" if is_compliant else "✗ Non-Compliant"
            status_color = self.SUCCESS_COLOR if is_compliant else self.DANGER_COLOR
            
            clause_elements.append(Paragraph(
                f"<font color='{status_color}'><b>{status_text}</b></font>",
                self.styles['ReportBody']
            ))
            
            # Issues (if any)
            issues = clause.get('issues', [])
            if issues:
                clause_elements.append(Paragraph("<b>Issues Found:</b>", self.styles['ReportBody']))
                for issue in issues[:5]:  # Limit to 5 issues
                    clause_elements.append(Paragraph(
                        f"• {issue}",
                        self.styles['ReportBody']
                    ))
            
            clause_elements.append(Spacer(1, 0.15*inch))
            
            # Add all clause elements as a KeepTogether group
            story.append(KeepTogether(clause_elements))
        
        if len(clause_analysis) > 20:
            story.append(Paragraph(
                f"<i>Note: Showing first 20 of {len(clause_analysis)} clauses analyzed.</i>",
                self.styles['ReportBody']
            ))
        
        story.append(PageBreak())
        
        # ===== RECOMMENDATIONS =====
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        story.append(Spacer(1, 0.1*inch))
        
        recommendations = analysis_results.get('recommendations', [])
        
        if not recommendations:
            # Generate default recommendations based on score
            if compliance_score < 70:
                recommendations = [
                    "Immediate review and revision of non-compliant clauses is required",
                    "Consult with legal counsel to address high-risk compliance gaps",
                    "Implement a compliance monitoring system for ongoing assessment",
                    "Schedule regular compliance audits (quarterly recommended)"
                ]
            elif compliance_score < 85:
                recommendations = [
                    "Address identified compliance gaps in the next contract revision",
                    "Review and update medium-risk clauses",
                    "Consider implementing automated compliance checking",
                    "Schedule semi-annual compliance reviews"
                ]
            else:
                recommendations = [
                    "Maintain current compliance practices",
                    "Monitor regulatory changes for updates",
                    "Consider this contract as a template for future agreements",
                    "Schedule annual compliance reviews"
                ]
        
        for i, rec in enumerate(recommendations, 1):
            story.append(Paragraph(
                f"<b>{i}.</b> {rec}",
                self.styles['ReportBody']
            ))
            story.append(Spacer(1, 0.05*inch))
        
        story.append(Spacer(1, 0.2*inch))
        
        # ===== FOOTER NOTE =====
        footer_note = Paragraph(
            "<i>This report was generated automatically by the AI-Powered Contract Compliance System. "
            "Please consult with legal professionals for final compliance decisions.</i>",
            self.styles['Footer']
        )
        story.append(footer_note)
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        logger.info(f"PDF report generated: {output_path}")
        
        # Cleanup temp chart files
        for temp_file in self.output_dir.glob("gauge_*.png"):
            try:
                temp_file.unlink()
            except:
                pass
        for temp_file in self.output_dir.glob("risk_dist_*.png"):
            try:
                temp_file.unlink()
            except:
                pass
        for temp_file in self.output_dir.glob("framework_*.png"):
            try:
                temp_file.unlink()
            except:
                pass
        
        return str(output_path)


if __name__ == "__main__":
    # Example usage
    generator = PDFReportGenerator()
    
    # Sample analysis results
    sample_results = {
        'contract_name': 'Sample_Contract_2025.pdf',
        'compliance_score': 72.5,
        'framework': 'GDPR',
        'processed_at': datetime.now().isoformat(),
        'total_clauses': 25,
        'compliant_clauses': 18,
        'non_compliant_clauses': 5,
        'missing_clauses': 8,
        'risk_distribution': {
            'high': 3,
            'medium': 5,
            'low': 2
        },
        'clause_analysis': [
            {
                'clause_id': 'Clause 4.2',
                'clause_text': 'Data may be transferred to third countries without adequate safeguards.',
                'is_compliant': False,
                'risk_level': 'high',
                'issues': [
                    'Missing standard contractual clauses',
                    'No adequacy decision mentioned',
                    'Lack of data subject consent provisions'
                ]
            },
            {
                'clause_id': 'Clause 5.1',
                'clause_text': 'Personal data will be retained for the duration of the contract.',
                'is_compliant': True,
                'risk_level': 'low',
                'issues': []
            }
        ],
        'recommendations': [
            'Add standard contractual clauses for international data transfers',
            'Include explicit data subject consent mechanisms',
            'Specify data retention periods in accordance with GDPR Article 5(1)(e)'
        ],
        'executive_summary': 'This contract demonstrates moderate compliance with GDPR requirements, '
                           'achieving a score of 72.5%. Key areas requiring attention include data transfer '
                           'mechanisms and consent provisions.'
    }
    
    pdf_path = generator.generate_compliance_report(sample_results)
    print(f"Sample report generated: {pdf_path}")
