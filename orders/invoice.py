import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_order_invoice_pdf(order):
    """
    Generates a downloadable PDF tax invoice for a Tasty Tap Order (Section 53).
    Includes:
    TASTY TAP, Business Name, Business Address, Order ID, Customer,
    Items, Quantity, Price, Discount, Tax, Delivery Fee, Total, Payment Status, Date.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#9E421B'),
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        'InvoiceSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4A4A4A'),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#1A5F72'),
        spaceBefore=8,
        spaceAfter=6,
    )

    elements = []
    elements.append(Paragraph("TASTY TAP — TAX INVOICE", title_style))
    elements.append(Paragraph('"Tap. Taste. Delivered." | Multi-Vendor Local Food Marketplace', sub_style))

    meta_data = [
        [
            Paragraph(f"<b>Order ID:</b> #{order.order_number}", styles['Normal']),
            Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %b %Y, %I:%M %p')}", styles['Normal']),
        ],
        [
            Paragraph(f"<b>Business Partner:</b> {order.business.name}", styles['Normal']),
            Paragraph(f"<b>Customer:</b> {order.customer_name} ({order.customer_phone})", styles['Normal']),
        ],
        [
            Paragraph(f"<b>Business Address:</b> {order.business.address}, {order.business.area}, {order.business.city}", styles['Normal']),
            Paragraph(f"<b>Delivery Address:</b> {order.delivery_address}, {order.delivery_area}, {order.delivery_city}", styles['Normal']),
        ],
        [
            Paragraph(f"<b>Payment Method:</b> {order.get_payment_method_display()}", styles['Normal']),
            Paragraph(f"<b>Payment Status:</b> {order.get_payment_status_display()} | <b>Order Status:</b> {order.get_status_display()}", styles['Normal']),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[85 * mm, 88 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FDF8F2')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#E2CFC0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#EFE3D8')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Order Items Summary", section_style))

    item_rows = [['#', 'Item & Customization', 'Qty', 'Unit Price (INR)', 'Line Total (INR)']]
    for idx, item in enumerate(order.items.all(), start=1):
        desc = item.food_name
        if item.customization_details:
            desc += f" ({item.customization_details})"
        unit_total = item.unit_price + item.addon_price
        item_rows.append([
            str(idx),
            Paragraph(desc, styles['Normal']),
            str(item.quantity),
            f"Rs. {unit_total:.2f}",
            f"Rs. {item.line_total:.2f}",
        ])

    item_rows.extend([
        ['', '', '', 'Subtotal:', f"Rs. {order.subtotal:.2f}"],
        ['', '', '', 'Coupon / Promo Discount:', f"- Rs. {order.discount_amount:.2f}"],
        ['', '', '', 'Tasty Points Redeemed:', f"- Rs. {order.points_discount:.2f}"],
        ['', '', '', 'GST & Platform Taxes (5%):', f"Rs. {order.tax_amount:.2f}"],
        ['', '', '', 'Delivery Partner Fee:', f"Rs. {order.delivery_fee:.2f}"],
        ['', '', '', 'GRAND TOTAL:', f"Rs. {order.total_amount:.2f}"],
    ])

    items_table = Table(item_rows, colWidths=[12 * mm, 82 * mm, 16 * mm, 33 * mm, 30 * mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9E421B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -7), 0.5, colors.HexColor('#DCC8B8')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (3, -1), (4, -1), colors.HexColor('#F5E6D8')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph(
        "Thank you for supporting local food businesses on TASTY TAP! "
        "This is a computer-generated digital invoice.",
        sub_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
