"""
Export Service for compliance reports.
Handles exporting compliance reports in various formats (JSON, CSV, PDF).
"""
import json
import csv
import io
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, 
        Spacer, PageBreak, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from models.regulatory_requirement import ComplianceReport
from models.recommendation import Recommendation
from utils.logger import get_logger

logger = get_logger(__name__)


class ExportService:
    """
    Service for exporting compliance analysis results in various formats.
    """
    
    def __init__(self):
        """Initialize Export Service."""
        logger.info("Initializing Export Service...")
    
    def export_to_json(
        self,
        report: ComplianceReport,
        recommendations: Optional[List[Recommendation]] = None,
        include_metadata: bool = True
    ) -> str:
        """
        Export compliance report to JSON format.
        
        Args:
            report: ComplianceReport to export
            recommendations: Optional list of recommendations
            include_metadata: Whether to include export metadata
            
        Returns:
            JSON string representation of the report
        """
        logger.info(f"Exporting report {report.document_id} to JSON...")
        
        try:
            # Build export data structure
            export_data = {
                'report': report.to_dict(),
                'recommendations': [
                    rec.to_dict() for rec in recommendations
                ] if recommendations else []
            }
            
            # Add metadata if requested
            if include_metadata:
                export_data['metadata'] = {
                    'export_date': datetime.now().isoformat(),
                    'export_format': 'JSON',
                    'version': '1.0'
                }
            
            # Convert to JSON with pretty printing
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            logger.info(
                f"Successfully exported report to JSON "
                f"({len(json_str)} characters)"
            )
            
            return json_str
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}", exc_info=True)
            raise ExportError(f"Failed to export to JSON: {e}")
    
    def get_json_filename(self, report: ComplianceReport) -> str:
        """
        Generate a filename for JSON export.
        
        Args:
            report: ComplianceReport
            
        Returns:
            Suggested filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"compliance_report_{report.document_id}_{timestamp}.json"
    
    def export_to_csv(
        self,
        report: ComplianceReport,
        recommendations: Optional[List[Recommendation]] = None
    ) -> str:
        """
        Export compliance report to CSV format.
        Creates a tabular format with clause-level data.
        
        Args:
            report: ComplianceReport to export
            recommendations: Optional list of recommendations
            
        Returns:
            CSV string representation of the report
        """
        logger.info(f"Exporting report {report.document_id} to CSV...")
        
        try:
            # Create in-memory string buffer
            output = io.StringIO()
            
            # Define CSV columns
            fieldnames = [
                'Clause ID',
                'Clause Type',
                'Framework',
                'Compliance Status',
                'Risk Level',
                'Confidence',
                'Issues',
                'Matched Requirements',
                'Clause Text (Preview)'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write clause results
            for result in report.clause_results:
                # Prepare issues string
                issues_str = '; '.join(result.issues) if result.issues else 'None'
                
                # Prepare matched requirements string
                req_str = '; '.join([
                    f"{req.article_reference}"
                    for req in result.matched_requirements
                ]) if result.matched_requirements else 'None'
                
                # Truncate clause text for preview
                clause_preview = (
                    result.clause_text[:100] + '...'
                    if len(result.clause_text) > 100
                    else result.clause_text
                )
                
                writer.writerow({
                    'Clause ID': result.clause_id,
                    'Clause Type': result.clause_type,
                    'Framework': result.framework,
                    'Compliance Status': result.compliance_status.value,
                    'Risk Level': result.risk_level.value,
                    'Confidence': f"{result.confidence * 100:.1f}%",
                    'Issues': issues_str,
                    'Matched Requirements': req_str,
                    'Clause Text (Preview)': clause_preview
                })
            
            # Add summary section
            output.write('\n')
            output.write('SUMMARY\n')
            output.write(f'Document ID,{report.document_id}\n')
            output.write(f'Overall Score,{report.overall_score:.1f}%\n')
            output.write(f'Frameworks Checked,{"; ".join(report.frameworks_checked)}\n')
            
            if report.summary:
                output.write(f'Total Clauses,{report.summary.total_clauses}\n')
                output.write(f'Compliant Clauses,{report.summary.compliant_clauses}\n')
                output.write(f'Non-Compliant Clauses,{report.summary.non_compliant_clauses}\n')
                output.write(f'Partial Clauses,{report.summary.partial_clauses}\n')
                output.write(f'High Risk Count,{report.summary.high_risk_count}\n')
                output.write(f'Medium Risk Count,{report.summary.medium_risk_count}\n')
                output.write(f'Low Risk Count,{report.summary.low_risk_count}\n')
            
            # Add missing requirements section
            if report.missing_requirements:
                output.write('\n')
                output.write('MISSING REQUIREMENTS\n')
                output.write('Framework,Article Reference,Clause Type,Description\n')
                
                for req in report.missing_requirements:
                    # Escape description for CSV
                    desc = req.description.replace('"', '""')
                    output.write(
                        f'{req.framework},{req.article_reference},'
                        f'{req.clause_type},"{desc}"\n'
                    )
            
            # Add recommendations section if provided
            if recommendations:
                output.write('\n')
                output.write('RECOMMENDATIONS\n')
                output.write('Priority,Action Type,Clause ID,Description,Regulatory Reference\n')
                
                for rec in recommendations:
                    desc = rec.description.replace('"', '""')
                    output.write(
                        f'{rec.get_priority_label()},{rec.action_type.value},'
                        f'{rec.clause_id or "N/A"},"{desc}",'
                        f'{rec.regulatory_reference}\n'
                    )
            
            csv_str = output.getvalue()
            output.close()
            
            logger.info(
                f"Successfully exported report to CSV "
                f"({len(csv_str)} characters)"
            )
            
            return csv_str
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}", exc_info=True)
            raise ExportError(f"Failed to export to CSV: {e}")
    
    def get_csv_filename(self, report: ComplianceReport) -> str:
        """
        Generate a filename for CSV export.
        
        Args:
            report: ComplianceReport
            
        Returns:
            Suggested filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"compliance_report_{report.document_id}_{timestamp}.csv"
    
    def export_to_pdf(
        self,
        report: ComplianceReport,
        recommendations: Optional[List[Recommendation]] = None
    ) -> bytes:
        """
        Export compliance report to PDF format using professional generator.
        
        Args:
            report: ComplianceReport to export
            recommendations: Optional list of recommendations
            
        Returns:
            PDF file as bytes
        """
        logger.info(f"Exporting report {report.document_id} to PDF...")
        
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available for PDF generation")
            raise ExportError(
                "PDF export requires reportlab library. "
                "Install with: pip install reportlab"
            )
        
        try:
            # Import professional PDF generator
            from services.pdf_report_generator import PDFReportGenerator
            
            # Convert ComplianceReport to PDF generator format
            analysis_results = self._convert_to_pdf_format(report, recommendations)
            
            # Generate PDF
            pdf_gen = PDFReportGenerator(output_dir="reports")
            pdf_path = pdf_gen.generate_compliance_report(
                analysis_results,
                output_filename=None  # Auto-generate filename
            )
            
            # Read PDF file as bytes
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Cleanup temp file
            import os
            try:
                os.remove(pdf_path)
            except:
                pass
            
            logger.info(
                f"Successfully exported report to PDF "
                f"({len(pdf_bytes)} bytes)"
            )
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}", exc_info=True)
            raise ExportError(f"Failed to export to PDF: {e}")
    
    def _convert_to_pdf_format(
        self,
        report: ComplianceReport,
        recommendations: Optional[List[Recommendation]] = None
    ) -> Dict[str, Any]:
        """
        Convert ComplianceReport to PDF generator format.
        
        Args:
            report: ComplianceReport object
            recommendations: Optional recommendations
            
        Returns:
            Dictionary formatted for PDF generator
        """
        from models.regulatory_requirement import ComplianceStatus, RiskLevel
        
        # Calculate metrics
        total_clauses = len(report.clause_results)
        compliant_clauses = sum(
            1 for c in report.clause_results 
            if c.compliance_status == ComplianceStatus.COMPLIANT
        )
        non_compliant_clauses = sum(
            1 for c in report.clause_results 
            if c.compliance_status == ComplianceStatus.NON_COMPLIANT
        )
        missing_clauses = len(report.missing_requirements)
        
        # Risk distribution
        risk_distribution = {'high': 0, 'medium': 0, 'low': 0}
        for clause in report.clause_results:
            if clause.risk_level == RiskLevel.HIGH:
                risk_distribution['high'] += 1
            elif clause.risk_level == RiskLevel.MEDIUM:
                risk_distribution['medium'] += 1
            elif clause.risk_level == RiskLevel.LOW:
                risk_distribution['low'] += 1
        
        # Clause analysis
        clause_analysis = []
        for clause in report.clause_results[:50]:  # Limit to 50 for PDF
            clause_analysis.append({
                'clause_id': clause.clause_id or 'N/A',
                'clause_text': clause.clause_text or 'N/A',
                'is_compliant': clause.compliance_status == ComplianceStatus.COMPLIANT,
                'risk_level': clause.risk_level.value.lower() if clause.risk_level else 'low',
                'issues': clause.issues or []
            })
        
        # Recommendations
        rec_list = []
        if recommendations:
            rec_list = [rec.description for rec in recommendations[:10]]
        
        # Executive summary
        exec_summary = ""
        if report.summary:
            exec_summary = (
                f"This compliance analysis covers {', '.join(report.frameworks_checked)} frameworks. "
                f"The contract achieved an overall compliance score of {report.overall_score:.1f}%. "
            )
            if report.overall_score >= 80:
                exec_summary += "The contract demonstrates strong compliance with regulatory requirements."
            elif report.overall_score >= 70:
                exec_summary += "The contract shows moderate compliance, with some areas requiring attention."
            else:
                exec_summary += "The contract has significant compliance gaps that require immediate attention."
        
        # Framework scores (if available in summary)
        framework = report.frameworks_checked[0] if report.frameworks_checked else "General"
        
        return {
            'contract_name': report.document_id,
            'compliance_score': report.overall_score,
            'framework': framework,
            'processed_at': datetime.now().isoformat(),
            'total_clauses': total_clauses,
            'compliant_clauses': compliant_clauses,
            'non_compliant_clauses': non_compliant_clauses,
            'missing_clauses': missing_clauses,
            'risk_distribution': risk_distribution,
            'clause_analysis': clause_analysis,
            'recommendations': rec_list,
            'executive_summary': exec_summary
        }
    
    def get_pdf_filename(self, report: ComplianceReport) -> str:
        """
        Generate a filename for PDF export.
        
        Args:
            report: ComplianceReport
            
        Returns:
            Suggested filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"compliance_report_{report.document_id}_{timestamp}.pdf"


class PDFReportGenerator:
    """
    DEPRECATED: Legacy PDF generator kept for backward compatibility.
    Use services.pdf_report_generator.PDFReportGenerator for new reports.
    
    Generate formatted PDF reports for compliance analysis.
    """
    
    def __init__(self):
        """Initialize PDF Report Generator."""
        if not REPORTLAB_AVAILABLE:
            raise ExportError("ReportLab library not available")
        
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2e86ab'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        ))
    
    def generate_report(
        self,
        report: ComplianceReport,
        recommendations: Optional[List[Recommendation]] = None
    ) -> bytes:
        """
        Generate complete PDF report.
        
        Args:
            report: ComplianceReport to generate
            recommendations: Optional list of recommendations
            
        Returns:
            PDF file as bytes
        """
        # Create in-memory buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build document content
        story = []
        
        # Add title page
        story.extend(self._create_title_page(report))
        
        # Add executive summary
        story.extend(self._create_executive_summary(report))
        
        # Add compliance details
        story.extend(self._create_compliance_details(report))
        
        # Add missing requirements
        if report.missing_requirements:
            story.extend(self._create_missing_requirements_section(report))
        
        # Add recommendations
        if recommendations:
            story.extend(self._create_recommendations_section(recommendations))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _create_title_page(self, report: ComplianceReport) -> List:
        """Create title page elements."""
        elements = []
        
        # Title
        title = Paragraph(
            "Compliance Analysis Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Document info
        info_data = [
            ['Document ID:', report.document_id],
            ['Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Frameworks:', ', '.join(report.frameworks_checked)],
            ['Overall Score:', f"{report.overall_score:.1f}%"]
        ]
        
        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(info_table)
        elements.append(PageBreak())
        
        return elements
    
    def _create_executive_summary(self, report: ComplianceReport) -> List:
        """Create executive summary section."""
        elements = []
        
        # Section header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Summary metrics
        if report.summary:
            summary_data = [
                ['Metric', 'Value'],
                ['Total Clauses Analyzed', str(report.summary.total_clauses)],
                ['Compliant Clauses', str(report.summary.compliant_clauses)],
                ['Non-Compliant Clauses', str(report.summary.non_compliant_clauses)],
                ['Partial Compliance', str(report.summary.partial_clauses)],
                ['High Risk Items', str(report.summary.high_risk_count)],
                ['Medium Risk Items', str(report.summary.medium_risk_count)],
                ['Low Risk Items', str(report.summary.low_risk_count)],
                ['Missing Requirements', str(len(report.missing_requirements))]
            ]
            
            summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e86ab')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
            ]))
            
            elements.append(summary_table)
        
        elements.append(Spacer(1, 0.3 * inch))
        
        # Overall assessment
        assessment_text = self._get_assessment_text(report.overall_score)
        assessment = Paragraph(
            f"<b>Overall Assessment:</b> {assessment_text}",
            self.styles['Normal']
        )
        elements.append(assessment)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_compliance_details(self, report: ComplianceReport) -> List:
        """Create detailed compliance results section."""
        elements = []
        
        # Section header
        header = Paragraph("Detailed Compliance Results", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Group results by framework
        for framework in report.frameworks_checked:
            framework_results = [
                r for r in report.clause_results
                if r.framework == framework
            ]
            
            if framework_results:
                # Framework subsection
                subheader = Paragraph(
                    f"{framework} Compliance",
                    self.styles['SubSection']
                )
                elements.append(subheader)
                
                # Create table data
                table_data = [['Clause ID', 'Type', 'Status', 'Risk', 'Issues']]
                
                for result in framework_results[:20]:  # Limit to first 20 for space
                    issues_preview = (
                        result.issues[0][:50] + '...'
                        if result.issues and len(result.issues[0]) > 50
                        else result.issues[0] if result.issues else 'None'
                    )
                    
                    table_data.append([
                        result.clause_id,
                        result.clause_type[:20],
                        result.compliance_status.value,
                        result.risk_level.value,
                        issues_preview
                    ])
                
                # Create table
                clause_table = Table(
                    table_data,
                    colWidths=[0.8 * inch, 1.5 * inch, 1 * inch, 0.8 * inch, 2.4 * inch]
                )
                
                # Style table
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e86ab')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
                ]
                
                # Add color coding for risk levels
                for i, result in enumerate(framework_results[:20], start=1):
                    if result.risk_level.value == 'High':
                        table_style.append(
                            ('BACKGROUND', (3, i), (3, i), colors.HexColor('#ff6b6b'))
                        )
                    elif result.risk_level.value == 'Medium':
                        table_style.append(
                            ('BACKGROUND', (3, i), (3, i), colors.HexColor('#ffd166'))
                        )
                    else:
                        table_style.append(
                            ('BACKGROUND', (3, i), (3, i), colors.HexColor('#06d6a0'))
                        )
                
                clause_table.setStyle(TableStyle(table_style))
                elements.append(clause_table)
                elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_missing_requirements_section(self, report: ComplianceReport) -> List:
        """Create missing requirements section."""
        elements = []
        
        # Section header
        header = Paragraph("Missing Requirements", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Create table
        table_data = [['Framework', 'Article', 'Clause Type', 'Description']]
        
        for req in report.missing_requirements:
            desc_preview = (
                req.description[:80] + '...'
                if len(req.description) > 80
                else req.description
            )
            
            table_data.append([
                req.framework,
                req.article_reference,
                req.clause_type[:25],
                desc_preview
            ])
        
        missing_table = Table(
            table_data,
            colWidths=[0.8 * inch, 1.2 * inch, 1.5 * inch, 3 * inch]
        )
        
        missing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6b6b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff0f0')])
        ]))
        
        elements.append(missing_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_recommendations_section(self, recommendations: List[Recommendation]) -> List:
        """Create recommendations section."""
        elements = []
        
        # Section header
        header = Paragraph("Recommendations", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Sort by priority
        sorted_recs = sorted(recommendations, key=lambda r: r.priority)
        
        # Create table
        table_data = [['Priority', 'Action', 'Description', 'Reference']]
        
        for rec in sorted_recs[:15]:  # Limit to first 15
            desc_preview = (
                rec.description[:60] + '...'
                if len(rec.description) > 60
                else rec.description
            )
            
            table_data.append([
                rec.get_priority_label(),
                rec.action_type.value,
                desc_preview,
                rec.regulatory_reference[:30]
            ])
        
        rec_table = Table(
            table_data,
            colWidths=[0.8 * inch, 1.2 * inch, 3 * inch, 1.5 * inch]
        )
        
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e86ab')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')])
        ]))
        
        elements.append(rec_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _get_assessment_text(self, score: float) -> str:
        """Get assessment text based on score."""
        if score >= 90:
            return "Excellent compliance. Minor improvements recommended."
        elif score >= 80:
            return "Good compliance. Some areas need attention."
        elif score >= 70:
            return "Moderate compliance. Several issues require remediation."
        elif score >= 60:
            return "Fair compliance. Significant improvements needed."
        else:
            return "Poor compliance. Immediate action required."


class ExportError(Exception):
    """Exception raised when export operations fail."""
    pass
