from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
from typing import Optional, List
import os

# ─── FONT SOZLASH ───────────────────────────────────────────────────────────
# Windows uchun Arial (kirill va lotin harflarni qo'llab-quvvatlaydi)
def _register_fonts():
    font_paths = [
        ("C:/Windows/Fonts/arial.ttf", "Arial"),
        ("C:/Windows/Fonts/arialbd.ttf", "Arial-Bold"),
        ("C:/Windows/Fonts/ariali.ttf", "Arial-Italic"),
    ]
    for path, name in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:
                pass

_register_fonts()

def _get_font(bold=False, italic=False):
    try:
        if bold:
            return "Arial-Bold"
        if italic:
            return "Arial-Italic"
        return "Arial"
    except Exception:
        return "Helvetica-Bold" if bold else "Helvetica"

# ─── RANGLAR ────────────────────────────────────────────────────────────────
PRIMARY    = colors.HexColor("#2563EB")
SECONDARY  = colors.HexColor("#64748B")
SUCCESS    = colors.HexColor("#16A34A")
LIGHT_GRAY = colors.HexColor("#F1F5F9")
BORDER     = colors.HexColor("#E2E8F0")
WHITE      = colors.white
BLACK      = colors.black
DARK       = colors.HexColor("#1E293B")

# ─── STYLE HELPER ───────────────────────────────────────────────────────────
def _style(name, font_size=10, bold=False, color=BLACK,
           alignment=0, space_before=0, space_after=4):
    return ParagraphStyle(
        name=name,
        fontName=_get_font(bold=bold),
        fontSize=font_size,
        textColor=color,
        alignment=alignment,
        spaceBefore=space_before,
        spaceAfter=space_after,
        leading=font_size * 1.4
    )

# ─── KLINIKA HEADER ─────────────────────────────────────────────────────────
def _clinic_header(clinic_name: str, clinic_address: str = "", clinic_phone: str = "") -> list:
    elements = []

    # Klinika nomi
    elements.append(Paragraph(
        clinic_name.upper(),
        _style("clinic_name", font_size=16, bold=True, color=PRIMARY, alignment=1)
    ))

    if clinic_address:
        elements.append(Paragraph(
            f"📍 {clinic_address}",
            _style("addr", font_size=9, color=SECONDARY, alignment=1)
        ))
    if clinic_phone:
        elements.append(Paragraph(
            f"📞 {clinic_phone}",
            _style("phone", font_size=9, color=SECONDARY, alignment=1)
        ))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    elements.append(Spacer(1, 0.3 * cm))
    return elements

# ─── INFO JADVAL ────────────────────────────────────────────────────────────
def _info_table(data: list, col_widths=None) -> Table:
    """Ikki ustunli ma'lumot jadvali"""
    if col_widths is None:
        col_widths = [5 * cm, 12 * cm]

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
        ("FONTNAME", (0, 0), (0, -1), _get_font(bold=True)),
        ("FONTNAME", (1, 0), (1, -1), _get_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), DARK),
        ("TEXTCOLOR", (1, 0), (1, -1), BLACK),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUND", (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


# ════════════════════════════════════════════════════════════════════════════
# 1. RETSEPT (PRESCRIPTION) PDF
# ════════════════════════════════════════════════════════════════════════════
def generate_prescription_pdf(
    clinic_name: str,
    clinic_address: str,
    clinic_phone: str,
    doctor_name: str,
    doctor_specialization: str,
    patient_name: str,
    patient_birth_date: str,
    diagnosis: str,
    prescription: List[dict],
    recommendations: str = "",
    next_visit: str = "",
    record_date: str = ""
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )
    elements = []

    # Header
    elements += _clinic_header(clinic_name, clinic_address, clinic_phone)

    # Sarlavha
    elements.append(Paragraph(
        "RETSEPT / РЕЦЕПТ",
        _style("title", font_size=14, bold=True, color=PRIMARY, alignment=1)
    ))
    elements.append(Spacer(1, 0.4 * cm))

    # Sana
    date_str = record_date or datetime.now().strftime("%d.%m.%Y")
    elements.append(Paragraph(
        f"Sana / Дата: {date_str}",
        _style("date", font_size=9, color=SECONDARY, alignment=2)
    ))
    elements.append(Spacer(1, 0.3 * cm))

    # Bemor va doctor ma'lumotlari
    info_data = [
        ["Bemor / Пациент:", patient_name],
        ["Tug'ilgan sana / Дата рожд.:", patient_birth_date or "—"],
        ["Shifokor / Врач:", f"{doctor_name} ({doctor_specialization})"],
        ["Tashxis / Диагноз:", diagnosis or "—"],
    ]
    elements.append(_info_table(info_data))
    elements.append(Spacer(1, 0.5 * cm))

    # Dori-darmonlar
    elements.append(Paragraph(
        "Tayinlangan dorilar / Назначенные препараты:",
        _style("drugs_title", font_size=11, bold=True, color=PRIMARY)
    ))
    elements.append(Spacer(1, 0.2 * cm))

    drug_headers = [["№", "Dori nomi / Препарат", "Dozasi / Доза", "Chastota / Частота", "Davomiyligi / Длительность"]]
    drug_data = drug_headers + [
        [
            str(i + 1),
            drug.get("drug_name", ""),
            drug.get("dosage", ""),
            drug.get("frequency", ""),
            drug.get("duration", "")
        ]
        for i, drug in enumerate(prescription)
    ]

    drug_table = Table(
        drug_data,
        colWidths=[1 * cm, 5.5 * cm, 3 * cm, 3.5 * cm, 3.5 * cm]
    )
    drug_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
        ("FONTNAME", (0, 1), (-1, -1), _get_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(drug_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Tavsiyalar
    if recommendations:
        elements.append(Paragraph(
            "Tavsiyalar / Рекомендации:",
            _style("rec_title", font_size=10, bold=True, color=PRIMARY)
        ))
        elements.append(Paragraph(
            recommendations,
            _style("rec_body", font_size=9, space_before=4)
        ))
        elements.append(Spacer(1, 0.3 * cm))

    # Keyingi ko'rik
    if next_visit:
        elements.append(Paragraph(
            f"Keyingi ko'rik / Следующий приём: {next_visit}",
            _style("next", font_size=9, bold=True, color=SUCCESS)
        ))
        elements.append(Spacer(1, 0.5 * cm))

    # Imzo
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Spacer(1, 0.3 * cm))
    sign_data = [
        [
            Paragraph(f"Shifokor / Врач:\n{doctor_name}", _style("sign_doc", font_size=9)),
            Paragraph("Imzo / Подпись: ___________", _style("sign_line", font_size=9, alignment=2))
        ]
    ]
    sign_table = Table(sign_data, colWidths=[9 * cm, 8 * cm])
    sign_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
    elements.append(sign_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ════════════════════════════════════════════════════════════════════════════
# 2. BEMOR KARTASI PDF
# ════════════════════════════════════════════════════════════════════════════
def generate_patient_card_pdf(
    clinic_name: str,
    clinic_address: str,
    clinic_phone: str,
    patient: dict,
    appointments: List[dict],
    medical_records: List[dict],
    lab_results: List[dict]
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )
    elements = []

    # Header
    elements += _clinic_header(clinic_name, clinic_address, clinic_phone)

    elements.append(Paragraph(
        "BEMOR KARTASI / КАРТА ПАЦИЕНТА",
        _style("title", font_size=14, bold=True, color=PRIMARY, alignment=1)
    ))
    elements.append(Spacer(1, 0.4 * cm))

    # Bemor ma'lumotlari
    elements.append(Paragraph(
        "Shaxsiy ma'lumotlar / Личные данные",
        _style("section", font_size=11, bold=True, color=PRIMARY)
    ))
    elements.append(Spacer(1, 0.2 * cm))

    patient_info = [
        ["Bemor kodi / Код:", patient.get("patient_code", "—")],
        ["F.I.O / ФИО:", patient.get("full_name", "—")],
        ["Tug'ilgan sana / Дата рожд.:", str(patient.get("birth_date", "—"))],
        ["Jinsi / Пол:", patient.get("gender", "—")],
        ["Telefon / Телефон:", patient.get("phone", "—")],
        ["Manzil / Адрес:", patient.get("address", "—")],
        ["Qon guruhi / Группа крови:", patient.get("blood_type", "—")],
        ["Allergiya / Аллергия:", patient.get("allergies", "Yo'q / Нет")],
        ["Surunkali kasalliklar / Хрон. болезни:", patient.get("chronic_diseases", "Yo'q / Нет")],
    ]
    elements.append(_info_table(patient_info))
    elements.append(Spacer(1, 0.5 * cm))

    # Ko'riklar tarixi
    if appointments:
        elements.append(Paragraph(
            "Ko'riklar tarixi / История посещений",
            _style("section", font_size=11, bold=True, color=PRIMARY)
        ))
        elements.append(Spacer(1, 0.2 * cm))

        appt_headers = [["Sana", "Shifokor", "Navbat №", "Status"]]
        appt_data = appt_headers + [
            [
                str(a.get("appointment_date", "")),
                a.get("doctor_name", "—"),
                str(a.get("queue_number", "")),
                a.get("status", "")
            ]
            for a in appointments
        ]
        appt_table = Table(appt_data, colWidths=[4 * cm, 7 * cm, 3 * cm, 3.5 * cm])
        appt_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
            ("FONTNAME", (0, 1), (-1, -1), _get_font()),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(appt_table)
        elements.append(Spacer(1, 0.5 * cm))

    # Tibbiy yozuvlar
    if medical_records:
        elements.append(Paragraph(
            "Tibbiy yozuvlar / Медицинские записи",
            _style("section", font_size=11, bold=True, color=PRIMARY)
        ))
        elements.append(Spacer(1, 0.2 * cm))

        for i, rec in enumerate(medical_records, 1):
            elements.append(Paragraph(
                f"{i}. Sana: {rec.get('created_at', '—')} | Shifokor: {rec.get('doctor_name', '—')}",
                _style("rec_header", font_size=9, bold=True, color=DARK)
            ))
            rec_data = [
                ["Shikoyat:", rec.get("complaint", "—")],
                ["Tashxis:", rec.get("diagnosis", "—")],
                ["Davolash:", rec.get("treatment", "—")],
                ["Tavsiyalar:", rec.get("recommendations", "—")],
            ]
            elements.append(_info_table(rec_data))
            elements.append(Spacer(1, 0.3 * cm))

    # Tahlil natijalari
    if lab_results:
        elements.append(Paragraph(
            "Tahlil natijalari / Результаты анализов",
            _style("section", font_size=11, bold=True, color=PRIMARY)
        ))
        elements.append(Spacer(1, 0.2 * cm))

        lab_headers = [["Tahlil nomi", "Kategoriya", "Status", "Sana"]]
        lab_data = lab_headers + [
            [
                l.get("test_name", ""),
                l.get("test_category", "—"),
                l.get("status", ""),
                str(l.get("created_at", ""))
            ]
            for l in lab_results
        ]
        lab_table = Table(lab_data, colWidths=[6 * cm, 4 * cm, 3 * cm, 4.5 * cm])
        lab_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
            ("FONTNAME", (0, 1), (-1, -1), _get_font()),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(lab_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ════════════════════════════════════════════════════════════════════════════
# 3. KASSA CHEKI PDF
# ════════════════════════════════════════════════════════════════════════════
def generate_receipt_pdf(
    clinic_name: str,
    clinic_address: str,
    clinic_phone: str,
    receipt_number: str,
    patient_name: str,
    cashier_name: str,
    services: List[dict],
    subtotal: float,
    discount: float,
    total_amount: float,
    paid_amount: float,
    change_amount: float,
    payment_method: str,
    payment_date: str = ""
) -> BytesIO:
    # Chek A5 formatda (kichikroq)
    from reportlab.lib.pagesizes import A5
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A5,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm
    )
    elements = []

    # Header
    elements.append(Paragraph(
        clinic_name.upper(),
        _style("clinic", font_size=13, bold=True, color=PRIMARY, alignment=1)
    ))
    if clinic_address:
        elements.append(Paragraph(
            clinic_address,
            _style("addr", font_size=8, color=SECONDARY, alignment=1)
        ))
    if clinic_phone:
        elements.append(Paragraph(
            clinic_phone,
            _style("phone", font_size=8, color=SECONDARY, alignment=1)
        ))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY))
    elements.append(Spacer(1, 0.2 * cm))

    elements.append(Paragraph(
        "KASSA CHEKI / КАССОВЫЙ ЧЕК",
        _style("chek_title", font_size=11, bold=True, color=PRIMARY, alignment=1)
    ))
    elements.append(Spacer(1, 0.3 * cm))

    # Chek ma'lumotlari
    date_str = payment_date or datetime.now().strftime("%d.%m.%Y %H:%M")
    meta_data = [
        ["Chek №:", receipt_number],
        ["Sana / Дата:", date_str],
        ["Bemor / Пациент:", patient_name],
        ["Kassir / Кассир:", cashier_name],
        ["To'lov usuli:", payment_method],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 8.5 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), _get_font(bold=True)),
        ("FONTNAME", (1, 0), (1, -1), _get_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("TEXTCOLOR", (0, 0), (0, -1), DARK),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, lineCap="butt", dash=[3, 3]))
    elements.append(Spacer(1, 0.2 * cm))

    # Xizmatlar
    elements.append(Paragraph(
        "Xizmatlar / Услуги:",
        _style("srv_title", font_size=9, bold=True, color=DARK)
    ))
    elements.append(Spacer(1, 0.1 * cm))

    srv_headers = [["Xizmat", "Soni", "Narxi", "Jami"]]
    srv_data = srv_headers + [
        [
            s.get("service_name", ""),
            str(s.get("qty", 1)),
            f"{float(s.get('price', 0)):,.0f}",
            f"{float(s.get('price', 0)) * int(s.get('qty', 1)):,.0f}"
        ]
        for s in services
    ]
    srv_table = Table(
        srv_data,
        colWidths=[6 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm]
    )
    srv_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
        ("FONTNAME", (0, 1), (-1, -1), _get_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(srv_table)
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, lineCap="butt", dash=[3, 3]))
    elements.append(Spacer(1, 0.2 * cm))

    # Jami hisob
    total_data = [
        ["Jami / Итого:", f"{subtotal:,.0f} so'm"],
        ["Chegirma / Скидка:", f"{discount:,.0f} so'm"],
        ["To'lash kerak / К оплате:", f"{total_amount:,.0f} so'm"],
        ["To'landi / Оплачено:", f"{paid_amount:,.0f} so'm"],
        ["Qaytim / Сдача:", f"{change_amount:,.0f} so'm"],
    ]
    total_table = Table(total_data, colWidths=[7 * cm, 5.5 * cm])
    total_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -3), _get_font()),
        ("FONTNAME", (0, -2), (0, -1), _get_font(bold=True)),
        ("FONTNAME", (1, 0), (1, -3), _get_font()),
        ("FONTNAME", (1, -2), (1, -1), _get_font(bold=True)),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, -2), (-1, -1), SUCCESS),
        ("BACKGROUND", (0, -2), (-1, -2), colors.HexColor("#DCFCE7")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=PRIMARY))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "Rahmat! Sog'ligingiz uchun xizmat qilamiz.",
        _style("footer", font_size=8, color=SECONDARY, alignment=1)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ════════════════════════════════════════════════════════════════════════════
# 4. OYLIK HISOBOT PDF
# ════════════════════════════════════════════════════════════════════════════
def generate_monthly_report_pdf(
    clinic_name: str,
    report_month: str,
    total_patients: int,
    total_appointments: int,
    total_revenue: float,
    revenue_by_method: dict,
    top_services: List[dict],
    daily_revenue: List[dict]
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm
    )
    elements = []

    # Header
    elements += _clinic_header(clinic_name)

    elements.append(Paragraph(
        f"OYLIK HISOBOT / ЕЖЕМЕСЯЧНЫЙ ОТЧЁТ — {report_month}",
        _style("title", font_size=13, bold=True, color=PRIMARY, alignment=1)
    ))
    elements.append(Spacer(1, 0.5 * cm))

    # Umumiy statistika
    elements.append(Paragraph(
        "Umumiy ko'rsatkichlar / Общие показатели",
        _style("section", font_size=11, bold=True, color=PRIMARY)
    ))
    elements.append(Spacer(1, 0.2 * cm))

    stats_data = [
        ["Ko'rsatkich / Показатель", "Qiymat / Значение"],
        ["Jami bemorlar / Всего пациентов", str(total_patients)],
        ["Jami navbatlar / Всего приёмов", str(total_appointments)],
        ["Jami daromad / Общий доход", f"{total_revenue:,.0f} so'm"],
        ["Naqd / Наличные", f"{revenue_by_method.get('cash', 0):,.0f} so'm"],
        ["Karta / Карта", f"{revenue_by_method.get('card', 0):,.0f} so'm"],
        ["POS terminal", f"{revenue_by_method.get('pos', 0):,.0f} so'm"],
    ]
    stats_table = Table(stats_data, colWidths=[10 * cm, 7 * cm])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
        ("FONTNAME", (0, 1), (-1, -1), _get_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (1, 0), (1, -1), 8),
        # Jami daromad qatorini ajratish
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#DBEAFE")),
        ("FONTNAME", (0, 3), (-1, 3), _get_font(bold=True)),
        ("TEXTCOLOR", (0, 3), (-1, 3), PRIMARY),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Top xizmatlar
    if top_services:
        elements.append(Paragraph(
            "Eng ko'p talab qilingan xizmatlar / Топ услуги",
            _style("section", font_size=11, bold=True, color=PRIMARY)
        ))
        elements.append(Spacer(1, 0.2 * cm))

        svc_headers = [["№", "Xizmat nomi / Услуга", "Soni / Кол-во", "Daromad / Доход"]]
        svc_data = svc_headers + [
            [str(i + 1), s.get("name", ""), str(s.get("count", 0)), f"{float(s.get('revenue', 0)):,.0f}"]
            for i, s in enumerate(top_services[:10])
        ]
        svc_table = Table(svc_data, colWidths=[1.5 * cm, 9 * cm, 3 * cm, 4 * cm])
        svc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
            ("FONTNAME", (0, 1), (-1, -1), _get_font()),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (1, 1), (1, -1), "LEFT"),
            ("ALIGN", (3, 1), (3, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(svc_table)
        elements.append(Spacer(1, 0.5 * cm))

    # Kunlik daromad
    if daily_revenue:
        elements.append(Paragraph(
            "Kunlik daromad / Ежедневный доход",
            _style("section", font_size=11, bold=True, color=PRIMARY)
        ))
        elements.append(Spacer(1, 0.2 * cm))

        day_headers = [["Sana / Дата", "Tranzaksiyalar", "Jami daromad"]]
        day_data = day_headers + [
            [d.get("date", ""), str(d.get("count", 0)), f"{float(d.get('total', 0)):,.0f} so'm"]
            for d in daily_revenue
        ]
        day_table = Table(day_data, colWidths=[6 * cm, 5 * cm, 6.5 * cm])
        day_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), _get_font(bold=True)),
            ("FONTNAME", (0, 1), (-1, -1), _get_font()),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(day_table)

    # Footer
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        f"Hisobot yaratildi / Отчёт создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        _style("footer", font_size=8, color=SECONDARY, alignment=2)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer