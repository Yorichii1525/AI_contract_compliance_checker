"""
Professional Contract PDF Generator
Converts sample contract text files to industry-standard PDF documents
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, KeepTogether, Image
)
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import re

class ContractPDFGenerator:
    """Generate professional legal contract PDFs"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom paragraph styles for legal documents"""
        
        # Title style - centered, large, bold
        self.styles.add(ParagraphStyle(
            name='ContractTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle - compliance level
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=24,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        # Section heading - numbered sections
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=13,
            textColor=colors.HexColor('#1a1a1a'),
            spaceBefore=16,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            keepWithNext=True
        ))
        
        # Subsection heading
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            leftIndent=20,
            keepWithNext=True
        ))
        
        # Body text - justified for professional look
        self.styles.add(ParagraphStyle(
            name='BodyJustified',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            leading=14,
            fontName='Helvetica'
        ))
        
        # Indented clause text
        self.styles.add(ParagraphStyle(
            name='ClauseText',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_JUSTIFY,
            leftIndent=30,
            spaceAfter=6,
            leading=14,
            fontName='Helvetica'
        ))
        
        # Schedule/Annex heading
        self.styles.add(ParagraphStyle(
            name='ScheduleHeading',
            parent=self.styles['Heading1'],
            fontSize=12,
            textColor=colors.HexColor('#1a1a1a'),
            spaceBefore=20,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=colors.HexColor('#333333'),
            borderPadding=8
        ))
        
        # Footer text
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        ))
        
        # Contract Definition style
        self.styles.add(ParagraphStyle(
            name='ContractDefinition',
            parent=self.styles['BodyText'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_JUSTIFY,
            leftIndent=30,
            firstLineIndent=-10,
            spaceAfter=4,
            leading=13,
            fontName='Helvetica'
        ))
    
    def _add_header_footer(self, canvas, doc, contract_title):
        """Add header and footer to each page"""
        canvas.saveState()
        
        # Header - company name and document type
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#666666'))
        canvas.drawString(inch, letter[1] - 0.5*inch, "AI Compliance Checker - Sample Contract")
        
        # Footer - page number and confidentiality notice
        canvas.setFont('Helvetica-Oblique', 7)
        canvas.drawCentredString(letter[0]/2, 0.5*inch, 
            f"Page {doc.page} | Confidential and Proprietary | Generated: {datetime.now().strftime('%B %d, %Y')}")
        
        # Document reference on right
        canvas.drawRightString(letter[0] - inch, 0.5*inch,
            f"Ref: {contract_title[:30]}")
        
        canvas.restoreState()
    
    def _parse_contract_text(self, text):
        """Parse contract text into structured components"""
        lines = text.strip().split('\n')
        
        # Extract title (first non-empty line)
        title = ""
        for line in lines:
            if line.strip():
                title = line.strip()
                break
        
        # Check for compliance level in title
        compliance_match = re.search(r'(\d+)%\s*(GDPR|HIPAA)?\s*COMPLIANT', title, re.IGNORECASE)
        compliance_level = None
        if compliance_match:
            compliance_level = f"{compliance_match.group(1)}% Compliant"
        
        return {
            'title': title,
            'compliance_level': compliance_level,
            'content': text
        }
    
    def _format_content_line(self, line):
        """Format a single line of contract content"""
        line = line.strip()
        
        if not line:
            return None
        
        # Separator lines
        if line.startswith('====='):
            return ('separator', line)
        
        # Schedule/Annex headings (ALL CAPS)
        if re.match(r'^SCHEDULE|^ANNEX', line, re.IGNORECASE):
            return ('schedule_heading', line)
        
        # Main section headings (starts with number)
        if re.match(r'^\d+\.\s+[A-Z\s]+(\(|$)', line):
            return ('section_heading', line)
        
        # Subsections (starts with number.number)
        if re.match(r'^\d+\.\d+\s+', line):
            return ('subsection_heading', line)
        
        # Clause items (starts with letter in parentheses)
        if re.match(r'^\([a-z]\)', line):
            return ('clause_item', line)
        
        # Regular paragraph
        return ('paragraph', line)
    
    def generate_pdf(self, input_file, output_file, contract_title=None):
        """Generate professional PDF from contract text file"""
        
        print(f"\n{'='*60}")
        print(f"Generating PDF: {os.path.basename(output_file)}")
        print(f"{'='*60}")
        
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Parse contract
        contract_data = self._parse_contract_text(text)
        
        if contract_title:
            contract_data['title'] = contract_title
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch,
            title=contract_data['title']
        )
        
        # Build content
        story = []
        
        # Title page
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph(contract_data['title'], self.styles['ContractTitle']))
        
        if contract_data['compliance_level']:
            story.append(Paragraph(contract_data['compliance_level'], self.styles['Subtitle']))
        
        # Add decorative line
        story.append(Spacer(1, 0.2*inch))
        table = Table([['']], colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#1a1a1a')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1a1a1a'))
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Document metadata
        metadata = f"""
        <b>Effective Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
        <b>Document Type:</b> Data Processing Agreement<br/>
        <b>Version:</b> 1.0<br/>
        <b>Status:</b> Sample Document for Compliance Testing
        """
        story.append(Paragraph(metadata, self.styles['BodyJustified']))
        story.append(Spacer(1, 0.5*inch))
        
        # Disclaimer
        disclaimer = """
        <b>DISCLAIMER:</b> <i>This is a sample contract generated for compliance testing purposes only. 
        It should not be used as an actual legal agreement without proper legal review and customization 
        for your specific requirements.</i>
        """
        story.append(Paragraph(disclaimer, self.styles['BodyJustified']))
        
        story.append(PageBreak())
        
        # Parse and format content
        lines = contract_data['content'].split('\n')
        current_paragraph = []
        
        for line in lines:
            formatted = self._format_content_line(line)
            
            if formatted is None:
                # Empty line - end current paragraph if any
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    story.append(Paragraph(para_text, self.styles['BodyJustified']))
                    current_paragraph = []
                continue
            
            format_type, content = formatted
            
            # Flush current paragraph before special formatting
            if format_type != 'paragraph' and current_paragraph:
                para_text = ' '.join(current_paragraph)
                story.append(Paragraph(para_text, self.styles['BodyJustified']))
                current_paragraph = []
            
            if format_type == 'separator':
                # Visual separator
                story.append(Spacer(1, 0.2*inch))
                table = Table([['']], colWidths=[6.5*inch])
                table.setStyle(TableStyle([
                    ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc'))
                ]))
                story.append(table)
                story.append(Spacer(1, 0.2*inch))
                
            elif format_type == 'schedule_heading':
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph(content, self.styles['ScheduleHeading']))
                
            elif format_type == 'section_heading':
                story.append(Paragraph(content, self.styles['SectionHeading']))
                
            elif format_type == 'subsection_heading':
                story.append(Paragraph(content, self.styles['SubsectionHeading']))
                
            elif format_type == 'clause_item':
                story.append(Paragraph(content, self.styles['ClauseText']))
                
            elif format_type == 'paragraph':
                # Accumulate paragraphs
                current_paragraph.append(content)
        
        # Flush any remaining paragraph
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            story.append(Paragraph(para_text, self.styles['BodyJustified']))
        
        # Add signature block
        story.append(PageBreak())
        story.append(Spacer(1, 1*inch))
        
        signature_section = """
        <b>SIGNATURE PAGE</b><br/><br/>
        IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.<br/><br/>
        """
        story.append(Paragraph(signature_section, self.styles['BodyJustified']))
        story.append(Spacer(1, 0.5*inch))
        
        # Signature table
        sig_table_data = [
            ['CONTROLLER', 'PROCESSOR'],
            ['', ''],
            ['', ''],
            ['Signature: ___________________', 'Signature: ___________________'],
            ['', ''],
            ['Name: ________________________', 'Name: ________________________'],
            ['', ''],
            ['Title: ________________________', 'Title: ________________________'],
            ['', ''],
            ['Date: _________________________', 'Date: _________________________']
        ]
        
        sig_table = Table(sig_table_data, colWidths=[3*inch, 3*inch])
        sig_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(sig_table)
        
        # Build PDF with header/footer
        doc.build(
            story,
            onFirstPage=lambda c, d: self._add_header_footer(c, d, contract_data['title']),
            onLaterPages=lambda c, d: self._add_header_footer(c, d, contract_data['title'])
        )
        
        file_size = os.path.getsize(output_file)
        print(f"✅ PDF generated successfully!")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print(f"{'='*60}\n")
        
        return output_file


def main():
    """Generate PDFs for all sample contracts"""
    
    print("\n" + "="*80)
    print(" PROFESSIONAL CONTRACT PDF GENERATOR")
    print("="*80)
    print(f" Generating industry-standard PDF contracts...")
    print(f" Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print("="*80 + "\n")
    
    # Initialize generator
    generator = ContractPDFGenerator()
    
    # Define contract files to convert
    contracts = [
        {
            'input': 'sample_contracts/synthetic_dpa_65percent_compliant.txt',
            'output': 'sample_contracts/DPA_Agreement_1.pdf',
            'title': 'DATA PROCESSING AGREEMENT 1'
        },
        {
            'input': 'sample_contracts/synthetic_dpa_40percent_compliant.txt',
            'output': 'sample_contracts/DPA_Agreement_2.pdf',
            'title': 'DATA PROCESSING AGREEMENT 2'
        },
        {
            'input': 'sample_contracts/data_processing_agreement_sample.txt',
            'output': 'sample_contracts/data_processing_agreement_sample.pdf',
            'title': 'DATA PROCESSING AGREEMENT'
        },
        {
            'input': 'sample_contracts/saas_service_agreement_sample.txt',
            'output': 'sample_contracts/saas_service_agreement_sample.pdf',
            'title': 'SOFTWARE AS A SERVICE (SaaS) AGREEMENT'
        },
        {
            'input': 'sample_contracts/vendor_service_contract_sample.txt',
            'output': 'sample_contracts/vendor_service_contract_sample.pdf',
            'title': 'MASTER VENDOR SERVICES AGREEMENT'
        }
    ]
    
    # Generate PDFs
    generated_files = []
    
    for contract in contracts:
        try:
            output_path = generator.generate_pdf(
                contract['input'],
                contract['output'],
                contract['title']
            )
            generated_files.append(output_path)
        except Exception as e:
            print(f"❌ Error generating {contract['output']}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print(" GENERATION COMPLETE")
    print("="*80)
    print(f" Successfully generated {len(generated_files)} PDF files:")
    for pdf_file in generated_files:
        size = os.path.getsize(pdf_file)
        print(f"   ✓ {pdf_file} ({size/1024:.1f} KB)")
    print("="*80 + "\n")
    
    print("📄 PDFs are ready for testing with the AI Compliance Checker!")
    print("   You can now upload these files in the Streamlit app.\n")


if __name__ == '__main__':
    main()
