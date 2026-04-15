"""
repair_tracker/pdf_views.py

Generates a downloadable PDF for a single Repair ticket.

"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from .models import Repair
from .audit_models import AuditLog

# ── Color palette ──────────────────────────────────────────────────────────────
HH_NAVY   = colors.HexColor('#003366')
HH_LIGHT  = colors.HexColor('#e8eef6')
BORDER    = colors.HexColor('#dee2e6')
LABEL_CLR = colors.HexColor('#495057')
TEXT_CLR  = colors.HexColor('#212529')
GREEN     = colors.HexColor('#198754')
RED       = colors.HexColor('#dc3545')
MUTED     = colors.HexColor('#6c757d')


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')


def _row(label, value, styles):
    """Return a two-cell table row used inside info sections."""
    return [
        Paragraph(f'<b>{label}</b>', styles['label']),
        Paragraph(str(value) if value else '—', styles['value']),
    ]


def _section_table(rows, col_widths=(1.6 * inch, 4.4 * inch)):
    """Wrap a list of rows in a styled two-column table."""
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (0, -1), HH_LIGHT),
        ('TEXTCOLOR',   (0, 0), (0, -1), LABEL_CLR),
        ('GRID',        (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING',  (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


@login_required
def repair_pdf(request, pk):
    repair = get_object_or_404(Repair, pk=pk)
    can_view_student = request.user.has_perm('repair_tracker.view_student_info')

    # ── Audit log ──────────────────────────────────────────────────────────────
    AuditLog.objects.create(
        user=request.user,
        username=request.user.username,
        action='PRINT',
        object_repr=repair.get_audit_representation(),
        changes={
            'ticket_id': repair.id,
            'included_pii': can_view_student,
            'printed_at': timezone.now().isoformat(),
        },
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
    )

    # ── HTTP response ──────────────────────────────────────────────────────────
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="repair_ticket_{repair.id}.pdf"'
    )

    # ── Document setup ─────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # ── Styles ─────────────────────────────────────────────────────────────────
    base = getSampleStyleSheet()
    S = {
        'title': ParagraphStyle(
            'title', parent=base['Normal'],
            fontSize=18, textColor=colors.white,
            fontName='Helvetica-Bold', leading=22,
        ),
        'subtitle': ParagraphStyle(
            'subtitle', parent=base['Normal'],
            fontSize=9, textColor=colors.HexColor('#b0c4de'),
            fontName='Helvetica',
        ),
        'meta': ParagraphStyle(
            'meta', parent=base['Normal'],
            fontSize=9, textColor=colors.white,
            fontName='Helvetica', alignment=TA_RIGHT,
        ),
        'section_head': ParagraphStyle(
            'section_head', parent=base['Normal'],
            fontSize=9, textColor=HH_NAVY,
            fontName='Helvetica-Bold',
            spaceAfter=4, spaceBefore=10,
            textTransform='uppercase',
        ),
        'label': ParagraphStyle(
            'label', parent=base['Normal'],
            fontSize=9, fontName='Helvetica-Bold',
            textColor=LABEL_CLR,
        ),
        'value': ParagraphStyle(
            'value', parent=base['Normal'],
            fontSize=9, fontName='Helvetica',
            textColor=TEXT_CLR,
        ),
        'block_text': ParagraphStyle(
            'block_text', parent=base['Normal'],
            fontSize=9, fontName='Helvetica',
            textColor=TEXT_CLR, leading=13,
            leftIndent=6, rightIndent=6,
        ),
        'footer': ParagraphStyle(
            'footer', parent=base['Normal'],
            fontSize=7.5, textColor=MUTED,
            fontName='Helvetica',
        ),
        'footer_right': ParagraphStyle(
            'footer_right', parent=base['Normal'],
            fontSize=7.5, textColor=MUTED,
            fontName='Helvetica', alignment=TA_RIGHT,
        ),
        'sig_label': ParagraphStyle(
            'sig_label', parent=base['Normal'],
            fontSize=8, textColor=LABEL_CLR,
            fontName='Helvetica',
        ),
    }

    story = []
    full_width = 7.0 * inch   # letter - margins

    # ── Header banner ──────────────────────────────────────────────────────────
    header_data = [[
        Paragraph('Hendrick Hudson School District<br/><font size="9" color="#b0c4de">IT Repair Ticket</font>', S['title']),
        Paragraph(
            f'<b>Ticket #{repair.id}</b><br/>'
            f'Created: {repair.created_at.strftime("%m/%d/%Y")}<br/>'
            f'Updated: {repair.updated_at.strftime("%m/%d/%Y")}<br/>'
            f'By: {repair.created_by.username if repair.created_by else "—"}',
            S['meta'],
        ),
    ]]
    header_table = Table(header_data, colWidths=[4.5 * inch, 2.5 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HH_NAVY),
        ('TOPPADDING',  (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # ── Status & Assignment  |  Device Information ─────────────────────────────
    status_rows = [
        _row('Status',        repair.get_status_display(), S),
        _row('Assigned To',   repair.assigned_to.username if repair.assigned_to else 'Unassigned', S),
        _row('Loaner',        str(repair.loaner) if repair.loaner else 'None', S),
        _row('ServiceNow INC', repair.service_now_inc_number or '—', S),
    ]
    device_rows = [
        _row('Device Name',  repair.device_name or '—', S),
        _row('DAM ID',       repair.device_DAM_ID or '—', S),
        _row('Serial Number', repair.device_serial or '—', S),
    ]

    # Side-by-side via outer table
    col_w = 1.5 * inch
    val_w = 1.9 * inch
    left_tbl  = _section_table(status_rows, (col_w, val_w))
    right_tbl = _section_table(device_rows, (col_w, val_w))

    row1_head = Table(
        [[Paragraph('STATUS &amp; ASSIGNMENT', S['section_head']),
          Paragraph('DEVICE INFORMATION', S['section_head'])]],
        colWidths=[full_width / 2, full_width / 2],
    )
    row1_head.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(row1_head)

    row1 = Table([[left_tbl, right_tbl]], colWidths=[full_width / 2, full_width / 2])
    row1.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(row1)
    story.append(Spacer(1, 8))

    # ── Student Information (gated) ────────────────────────────────────────────
    if can_view_student:
        story.append(Paragraph('STUDENT INFORMATION <font size="7" color="#dc3545">(FERPA PROTECTED)</font>', S['section_head']))
        student_rows = [
            _row('Name',        repair.student_name or '—', S),
            _row('Student ID',  repair.student_id or '—', S),
            _row('Grade',       repair.get_student_grade_display() if repair.student_grade else '—', S),
            _row('School',      repair.get_student_school_display() if repair.student_school else '—', S),
            _row('Email',       repair.student_email or '—', S),
        ]
        story.append(_section_table(student_rows, (1.5 * inch, 5.5 * inch)))
        story.append(Spacer(1, 8))

    # ── Dell Repair ────────────────────────────────────────────────────────────
    story.append(Paragraph('DELL REPAIR SHIPMENT', S['section_head']))
    dell_rows = [
        _row('Sent to Dell',    'Yes' if repair.sent_to_dell_check else 'No', S),
        _row('Dell Service #',  repair.dell_service_number or '—', S),
        _row('Submitted Under', repair.submitted_under or '—', S),
    ]
    story.append(_section_table(dell_rows, (1.5 * inch, 5.5 * inch)))
    story.append(Spacer(1, 8))

    # ── Issue Description ──────────────────────────────────────────────────────
    story.append(Paragraph('ISSUE DESCRIPTION', S['section_head']))
    issue_text = (repair.issue_description or '—').replace('\n', '<br/>')
    issue_tbl = Table(
        [[Paragraph(issue_text, S['block_text'])]],
        colWidths=[full_width],
    )
    issue_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID',         (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(issue_tbl)
    story.append(Spacer(1, 8))

    # ── Resolution Notes ───────────────────────────────────────────────────────
    if repair.resolution_notes:
        story.append(Paragraph('RESOLUTION NOTES', S['section_head']))
        res_text = repair.resolution_notes.replace('\n', '<br/>')
        res_tbl = Table(
            [[Paragraph(res_text, S['block_text'])]],
            colWidths=[full_width],
        )
        res_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, -1), colors.HexColor('#f0fff4')),
            ('GRID',         (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING',   (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(res_tbl)
        story.append(Spacer(1, 8))

    # ── Privacy & Compliance ───────────────────────────────────────────────────
    story.append(Paragraph('PRIVACY &amp; COMPLIANCE', S['section_head']))
    def check(val): return '☑' if val else '☐'
    compliance_rows = [
        _row(f'{check(repair.contains_student_data)}  Contains Student Data',
             f'{check(repair.third_party_access)}  Third-Party Access  |  {check(repair.consent_on_file)}  Parent Consent on File',
             S),
    ]
    story.append(_section_table(compliance_rows, (2.5 * inch, 4.5 * inch)))
    story.append(Spacer(1, 16))

    # ── Signature Lines ────────────────────────────────────────────────────────
    sig_data = [[
        Paragraph('_' * 42 + '<br/>Technician Signature &amp; Date', S['sig_label']),
        Paragraph('_' * 42 + '<br/>Student / Staff Signature &amp; Date', S['sig_label']),
    ]]
    sig_table = Table(sig_data, colWidths=[full_width / 2, full_width / 2])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 20),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 14))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=full_width, thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4))
    now_str = timezone.now().strftime('%m/%d/%Y %H:%M')
    footer_data = [[
        Paragraph('Hendrick Hudson School District — IT Department', S['footer']),
        Paragraph(f'Ticket #{repair.id} | Printed {now_str} by {request.user.username}', S['footer_right']),
    ]]
    footer_table = Table(footer_data, colWidths=[full_width / 2, full_width / 2])
    footer_table.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(footer_table)

    doc.build(story)
    return response