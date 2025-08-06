# PDF generation service using ReportLab
# Single responsibility: Generate share certificates

from typing import Optional
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from sqlalchemy.orm import Session
from app.repositories.shareholder import ShareIssuanceRepository
from app.config import settings


class PDFService:
    """
    PDF generation service for share certificates.
    Creates professional, watermarked certificates for share issuances.
    """

    def __init__(self, db: Session):
        self.db = db
        self.issuance_repo = ShareIssuanceRepository(db)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def generate_share_certificate(self, issuance_id: int) -> Optional[BytesIO]:
        """
        Generate PDF share certificate for given issuance.

        Args:
            issuance_id: Share issuance ID

        Returns:
            BytesIO buffer containing PDF data, None if issuance not found
        """
        # Get issuance with shareholder data
        issuance = self.issuance_repo.get(issuance_id)
        if not issuance:
            return None

        # Create PDF buffer
        buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=f"Share Certificate {issuance.certificate_number}"
        )

        # Build certificate content
        story = self._build_certificate_content(issuance)

        # Generate PDF
        doc.build(story, onFirstPage=self._add_watermark, onLaterPages=self._add_watermark)

        # Return buffer positioned at start
        buffer.seek(0)
        return buffer

    def _setup_custom_styles(self) -> None:
        """Setup custom paragraph styles for certificate"""

        # Certificate title style
        self.title_style = ParagraphStyle(
            'CertificateTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )

        # Company name style
        self.company_style = ParagraphStyle(
            'CompanyName',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkgreen,
            fontName='Helvetica-Bold'
        )

        # Certificate body style
        self.body_style = ParagraphStyle(
            'CertificateBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )

        # Signature style
        self.signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )

    def _build_certificate_content(self, issuance) -> list:
        """
        Build the content structure for the share certificate.

        Args:
            issuance: Share issuance object with loaded shareholder data

        Returns:
            List of Platypus flowables for PDF generation
        """
        story = []

        # Add spacer at top
        story.append(Spacer(1, 0.5 * inch))

        # Company name
        story.append(Paragraph(settings.company_name, self.company_style))

        # Certificate title
        story.append(Paragraph("SHARE CERTIFICATE", self.title_style))

        # Certificate number and date
        # Continuing from app/services/pdf.py

        cert_info = f"Certificate No: {issuance.certificate_number} | Issue Date: {issuance.issued_date.strftime('%B %d, %Y')}"
        story.append(Paragraph(cert_info, self.body_style))

        story.append(Spacer(1, 0.3 * inch))

        # Certificate body text
        certificate_text = f"""
                This is to certify that <b>{issuance.shareholder.full_name}</b> is the registered holder of 
                <b>{issuance.number_of_shares:,} shares</b> of common stock of {settings.company_name}, 
                each share having a par value of <b>${issuance.price_per_share}</b>.
                """
        story.append(Paragraph(certificate_text, self.body_style))

        story.append(Spacer(1, 0.2 * inch))

        # Share details table
        share_data = [
            ['Shareholder Name:', issuance.shareholder.full_name],
            ['Number of Shares:', f"{issuance.number_of_shares:,}"],
            ['Price per Share:', f"${issuance.price_per_share}"],
            ['Total Value:', f"${issuance.total_value:,.2f}"],
            ['Issue Date:', issuance.issued_date.strftime('%B %d, %Y')],
        ]

        share_table = Table(share_data, colWidths=[2 * inch, 3 * inch])
        share_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(share_table)
        story.append(Spacer(1, 0.4 * inch))

        # Additional notes if any
        if issuance.notes:
            story.append(Paragraph(f"<b>Notes:</b> {issuance.notes}", self.body_style))
            story.append(Spacer(1, 0.2 * inch))

        # Signature section
        story.append(Spacer(1, 0.5 * inch))

        signature_data = [
            ['', ''],
            ['_' * 30, '_' * 30],
            ['Company Secretary', 'Chief Executive Officer'],
            [f'{settings.company_name}', f'{settings.company_name}']
        ]

        signature_table = Table(signature_data, colWidths=[2.5 * inch, 2.5 * inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ]))

        story.append(signature_table)

        # Footer disclaimer
        story.append(Spacer(1, 0.5 * inch))
        disclaimer = """
                This certificate is evidence of ownership of the shares described herein and is transferable 
                only on the books of the corporation by the holder hereof in person or by attorney upon 
                surrender of this certificate properly endorsed.
                """
        story.append(Paragraph(disclaimer, self.signature_style))

        return story

    def _add_watermark(self, canvas, doc):
        """
        Add watermark and header/footer to each page.

        Args:
            canvas: ReportLab canvas object
            doc: Document template object
        """
        # Save canvas state
        canvas.saveState()

        # Add watermark
        canvas.setFont('Helvetica-Bold', 60)
        canvas.setFillColor(colors.lightgrey)
        canvas.setFillAlpha(0.3)

        # Calculate center position for watermark
        page_width, page_height = A4
        canvas.translate(page_width / 2, page_height / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "SHARE CERTIFICATE")

        # Restore canvas state
        canvas.restoreState()

        # Add page border
        canvas.setStrokeColor(colors.darkblue)
        canvas.setLineWidth(2)
        canvas.rect(36, 36, page_width - 72, page_height - 72)

        # Add footer with generation timestamp
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | {settings.company_name}"
        canvas.drawString(72, 50, footer_text)