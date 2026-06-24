"""
build_doc.py
------------
Gera o documento PDF de entrega do projeto final.
Executar: python build_doc.py
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.platypus.flowables import Flowable

OUTPUT = "DOCUMENTACAO.pdf"

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    "TitleBig",
    parent=styles["Title"],
    fontSize=28,
    leading=34,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#1e3a8a"),
    spaceAfter=10,
)
style_subtitle = ParagraphStyle(
    "Subtitle",
    parent=styles["Normal"],
    fontSize=14,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#475569"),
    spaceAfter=20,
)
style_h1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#1e40af"),
    spaceBefore=14,
    spaceAfter=8,
)
style_h2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontSize=14,
    leading=18,
    textColor=colors.HexColor("#1e3a8a"),
    spaceBefore=10,
    spaceAfter=6,
)
style_h3 = ParagraphStyle(
    "H3",
    parent=styles["Heading3"],
    fontSize=12,
    leading=16,
    textColor=colors.HexColor("#334155"),
    spaceBefore=8,
    spaceAfter=4,
)
style_body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontSize=10.5,
    leading=15,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
)
style_code = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontName="Courier",
    fontSize=8.5,
    leading=11,
    leftIndent=10,
    rightIndent=10,
    spaceBefore=4,
    spaceAfter=8,
    backColor=colors.HexColor("#f1f5f9"),
    borderColor=colors.HexColor("#cbd5e1"),
    borderWidth=0.5,
    borderPadding=6,
    textColor=colors.HexColor("#0f172a"),
)
style_caption = ParagraphStyle(
    "Caption",
    parent=styles["Normal"],
    fontSize=9,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#64748b"),
    spaceAfter=10,
    italic=True,
)
style_label = ParagraphStyle(
    "Label",
    parent=styles["Normal"],
    fontSize=11,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#475569"),
    spaceAfter=4,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def p(text, style=style_body):
    return Paragraph(text, style)


def code(text):
    # Escapa HTML mantendo quebras de linha
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
        .replace(" ", "&nbsp;")
    )
    return Paragraph(safe, style_code)


def hr():
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=colors.HexColor("#cbd5e1"),
        spaceBefore=4,
        spaceAfter=8,
    )


def make_table(data, col_widths=None, header_bg="#1e40af"):
    """
    Cria uma tabela onde cada célula que é string vira um Paragraph
    automaticamente — isso garante quebra de linha quando o texto for longo.
    """
    cell_style = ParagraphStyle(
        "cell", parent=styles["Normal"], fontSize=9, leading=11,
        alignment=TA_LEFT,
    )
    header_style = ParagraphStyle(
        "cell_header", parent=styles["Normal"], fontSize=10, leading=12,
        alignment=TA_CENTER, textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    wrapped = []
    for i, row in enumerate(data):
        new_row = []
        for cell in row:
            if isinstance(cell, str):
                style = header_style if i == 0 else cell_style
                # Permite tags básicas que o usuário já tenha colocado
                new_row.append(Paragraph(cell, style))
            else:
                new_row.append(cell)
        wrapped.append(new_row)

    t = Table(wrapped, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                    [colors.HexColor("#f8fafc"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ]
        )
    )
    return t


# ---------------------------------------------------------------------------
# Flowable de diagrama (boxes ASCII-like desenhados em SVG-like usando Drawing)
# ---------------------------------------------------------------------------

from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF


def architecture_diagram():
    """Diagrama da arquitetura em 3 camadas + LLM externa."""
    d = Drawing(450, 280)

    # Caixa: Interface (Streamlit)
    d.add(Rect(50, 220, 350, 45, strokeColor=colors.HexColor("#1e40af"),
               strokeWidth=1.4, fillColor=colors.HexColor("#dbeafe")))
    d.add(String(225, 247, "Camada de Apresentação", fontName="Helvetica-Bold",
                 fontSize=11, textAnchor="middle",
                 fillColor=colors.HexColor("#1e3a8a")))
    d.add(String(225, 232, "Streamlit (app.py)", fontName="Helvetica",
                 fontSize=9, textAnchor="middle",
                 fillColor=colors.HexColor("#1e40af")))

    # Setas duplas verticais
    for x in (180, 270):
        d.add(Line(x, 215, x, 185, strokeColor=colors.HexColor("#475569"), strokeWidth=1))
    d.add(Polygon([175, 188, 185, 188, 180, 180],
                  fillColor=colors.HexColor("#475569"),
                  strokeColor=colors.HexColor("#475569")))
    d.add(Polygon([265, 188, 275, 188, 270, 180],
                  fillColor=colors.HexColor("#475569"),
                  strokeColor=colors.HexColor("#475569")))

    # Camada de Serviços (duas caixas lado a lado)
    d.add(Rect(50, 130, 165, 45, strokeColor=colors.HexColor("#0e7490"),
               strokeWidth=1.4, fillColor=colors.HexColor("#cffafe")))
    d.add(String(132, 157, "Serviço LLM", fontName="Helvetica-Bold",
                 fontSize=10, textAnchor="middle",
                 fillColor=colors.HexColor("#155e75")))
    d.add(String(132, 142, "llm_service.py", fontName="Helvetica",
                 fontSize=9, textAnchor="middle",
                 fillColor=colors.HexColor("#0e7490")))

    d.add(Rect(235, 130, 165, 45, strokeColor=colors.HexColor("#7c3aed"),
               strokeWidth=1.4, fillColor=colors.HexColor("#ede9fe")))
    d.add(String(317, 157, "Persistência", fontName="Helvetica-Bold",
                 fontSize=10, textAnchor="middle",
                 fillColor=colors.HexColor("#5b21b6")))
    d.add(String(317, 142, "database.py", fontName="Helvetica",
                 fontSize=9, textAnchor="middle",
                 fillColor=colors.HexColor("#7c3aed")))

    # Seta horizontal entre as duas
    d.add(Line(215, 152, 235, 152, strokeColor=colors.HexColor("#94a3b8"),
               strokeWidth=0.8, strokeDashArray=[3, 3]))

    # Setas para baixo
    d.add(Line(132, 130, 132, 95, strokeColor=colors.HexColor("#475569"),
               strokeWidth=1))
    d.add(Polygon([127, 98, 137, 98, 132, 90],
                  fillColor=colors.HexColor("#475569"),
                  strokeColor=colors.HexColor("#475569")))
    d.add(Line(317, 130, 317, 95, strokeColor=colors.HexColor("#475569"),
               strokeWidth=1))
    d.add(Polygon([312, 98, 322, 98, 317, 90],
                  fillColor=colors.HexColor("#475569"),
                  strokeColor=colors.HexColor("#475569")))

    # Camada de armazenamento e API externa
    d.add(Rect(50, 40, 165, 45, strokeColor=colors.HexColor("#b91c1c"),
               strokeWidth=1.4, fillColor=colors.HexColor("#fee2e2")))
    d.add(String(132, 67, "API Anthropic", fontName="Helvetica-Bold",
                 fontSize=10, textAnchor="middle",
                 fillColor=colors.HexColor("#7f1d1d")))
    d.add(String(132, 52, "Claude (HTTP/REST)", fontName="Helvetica",
                 fontSize=9, textAnchor="middle",
                 fillColor=colors.HexColor("#b91c1c")))

    d.add(Rect(235, 40, 165, 45, strokeColor=colors.HexColor("#15803d"),
               strokeWidth=1.4, fillColor=colors.HexColor("#dcfce7")))
    d.add(String(317, 67, "SQLite", fontName="Helvetica-Bold",
                 fontSize=10, textAnchor="middle",
                 fillColor=colors.HexColor("#14532d")))
    d.add(String(317, 52, "data/taskmind.db", fontName="Helvetica",
                 fontSize=9, textAnchor="middle",
                 fillColor=colors.HexColor("#15803d")))

    # Título
    d.add(String(225, 10, "Figura 1 — Arquitetura em camadas",
                 fontName="Helvetica-Oblique", fontSize=9,
                 textAnchor="middle", fillColor=colors.HexColor("#64748b")))
    d.hAlign = "CENTER"
    return d


def er_diagram():
    """Diagrama Entidade-Relacionamento simplificado."""
    d = Drawing(450, 260)

    # Task
    d.add(Rect(150, 165, 150, 80, strokeColor=colors.HexColor("#1e40af"),
               strokeWidth=1.4, fillColor=colors.HexColor("#dbeafe")))
    d.add(String(225, 232, "Task", fontName="Helvetica-Bold", fontSize=11,
                 textAnchor="middle", fillColor=colors.HexColor("#1e3a8a")))
    d.add(Line(155, 224, 295, 224, strokeColor=colors.HexColor("#1e3a8a"),
               strokeWidth=0.6))
    task_fields = [
        "PK id : int",
        "title, description, priority",
        "status, due_date",
        "estimated_minutes (IA)",
        "ai_priority_score (IA)",
    ]
    for i, f in enumerate(task_fields):
        d.add(String(158, 213 - i * 9, f, fontName="Helvetica", fontSize=7.5,
                     fillColor=colors.HexColor("#1e3a8a")))

    # Subtask
    d.add(Rect(20, 50, 130, 65, strokeColor=colors.HexColor("#7c3aed"),
               strokeWidth=1.4, fillColor=colors.HexColor("#ede9fe")))
    d.add(String(85, 102, "Subtask", fontName="Helvetica-Bold", fontSize=11,
                 textAnchor="middle", fillColor=colors.HexColor("#5b21b6")))
    d.add(Line(25, 94, 145, 94, strokeColor=colors.HexColor("#5b21b6"),
               strokeWidth=0.6))
    sub_fields = ["PK id", "FK task_id", "title, done, order_index"]
    for i, f in enumerate(sub_fields):
        d.add(String(28, 83 - i * 9, f, fontName="Helvetica", fontSize=7.5,
                     fillColor=colors.HexColor("#5b21b6")))

    # Linha 1:N
    d.add(Line(150, 175, 110, 115, strokeColor=colors.HexColor("#475569"),
               strokeWidth=1))
    d.add(String(120, 145, "1 : N", fontName="Helvetica-Bold", fontSize=9,
                 fillColor=colors.HexColor("#dc2626")))

    # Report
    d.add(Rect(310, 80, 130, 50, strokeColor=colors.HexColor("#15803d"),
               strokeWidth=1.4, fillColor=colors.HexColor("#dcfce7")))
    d.add(String(375, 117, "Report", fontName="Helvetica-Bold", fontSize=11,
                 textAnchor="middle", fillColor=colors.HexColor("#14532d")))
    d.add(Line(315, 109, 435, 109, strokeColor=colors.HexColor("#14532d"),
               strokeWidth=0.6))
    rep_fields = ["PK id, period_start, period_end", "content (Markdown da IA)"]
    for i, f in enumerate(rep_fields):
        d.add(String(318, 98 - i * 9, f, fontName="Helvetica", fontSize=7.5,
                     fillColor=colors.HexColor("#14532d")))

    # ChatMessage
    d.add(Rect(310, 15, 130, 50, strokeColor=colors.HexColor("#b91c1c"),
               strokeWidth=1.4, fillColor=colors.HexColor("#fee2e2")))
    d.add(String(375, 52, "ChatMessage", fontName="Helvetica-Bold", fontSize=11,
                 textAnchor="middle", fillColor=colors.HexColor("#7f1d1d")))
    d.add(Line(315, 44, 435, 44, strokeColor=colors.HexColor("#7f1d1d"),
               strokeWidth=0.6))
    chat_fields = ["PK id, role, content", "created_at"]
    for i, f in enumerate(chat_fields):
        d.add(String(318, 33 - i * 9, f, fontName="Helvetica", fontSize=7.5,
                     fillColor=colors.HexColor("#7f1d1d")))

    d.add(String(225, 252, "Modelo de Dados", fontName="Helvetica-Bold",
                 fontSize=11, textAnchor="middle",
                 fillColor=colors.HexColor("#0f172a")))
    d.hAlign = "CENTER"
    return d


def flow_diagram():
    """Fluxo: usuário cria tarefa → decomposição → estimativa → persistência."""
    d = Drawing(450, 130)

    boxes = [
        ("Usuário\ncria tarefa", "#dbeafe", "#1e40af"),
        ("LLM\ndecompõe", "#fef3c7", "#a16207"),
        ("LLM\nestima tempo", "#cffafe", "#0e7490"),
        ("SQLite\npersiste", "#dcfce7", "#15803d"),
        ("UI\nexibe", "#ede9fe", "#5b21b6"),
    ]
    x0, w, gap = 10, 75, 12
    for i, (label, bg, fg) in enumerate(boxes):
        x = x0 + i * (w + gap)
        d.add(Rect(x, 50, w, 55, strokeColor=colors.HexColor(fg),
                   strokeWidth=1.2, fillColor=colors.HexColor(bg)))
        lines = label.split("\n")
        for j, ln in enumerate(lines):
            d.add(String(x + w / 2, 82 - j * 12, ln,
                         fontName="Helvetica-Bold", fontSize=9,
                         textAnchor="middle", fillColor=colors.HexColor(fg)))

        # Setas entre caixas
        if i < len(boxes) - 1:
            ax = x + w + 1
            d.add(Line(ax, 77, ax + gap - 2, 77,
                       strokeColor=colors.HexColor("#475569"), strokeWidth=1.2))
            d.add(Polygon([ax + gap - 4, 74, ax + gap - 4, 80, ax + gap, 77],
                          fillColor=colors.HexColor("#475569"),
                          strokeColor=colors.HexColor("#475569")))

    d.add(String(225, 20, "Figura 3 — Fluxo de criação de uma tarefa com IA",
                 fontName="Helvetica-Oblique", fontSize=9,
                 textAnchor="middle", fillColor=colors.HexColor("#64748b")))
    d.hAlign = "CENTER"
    return d


# ---------------------------------------------------------------------------
# Header/Footer
# ---------------------------------------------------------------------------

def header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    # Footer
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(colors.HexColor("#64748b"))
    canvas_obj.drawString(2 * cm, 1.2 * cm, "TaskMind AI — Documentação técnica")
    canvas_obj.drawRightString(
        A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}"
    )
    canvas_obj.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas_obj.setLineWidth(0.4)
    canvas_obj.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas_obj.restoreState()


# ---------------------------------------------------------------------------
# Construção do documento
# ---------------------------------------------------------------------------

def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title="TaskMind AI — Documentação",
        author="Projeto Final de Disciplina",
    )

    story = []

    # ===== CAPA =====
    story.append(Spacer(1, 4.2 * cm))

    # Logo desenhado (substitui o emoji que não renderiza nas fontes padrão)
    logo = Drawing(150, 90)
    # Quadrado externo arredondado
    logo.add(Rect(45, 10, 60, 60, rx=10, ry=10,
                  strokeColor=colors.HexColor("#1e3a8a"), strokeWidth=2,
                  fillColor=colors.HexColor("#dbeafe")))
    # Letras "AI" no centro
    logo.add(String(75, 30, "AI", fontName="Helvetica-Bold", fontSize=26,
                    textAnchor="middle", fillColor=colors.HexColor("#1e3a8a")))
    # Pequeno indicador de "task" (três barras horizontais à direita)
    for i, y in enumerate([56, 48, 40]):
        w = 22 - i * 4
        logo.add(Rect(115, y, w, 3, strokeColor=None,
                      fillColor=colors.HexColor("#3b82f6")))
    logo.hAlign = "CENTER"
    story.append(logo)

    story.append(Spacer(1, 0.3 * cm))
    story.append(p("TaskMind AI", style_title))
    story.append(p("Gerenciador inteligente de tarefas com LLM como copiloto de produtividade",
                   style_subtitle))
    story.append(Spacer(1, 1.5 * cm))

    cover_data = [
        ["Disciplina", "Projeto Final — Tema livre"],
        ["Categoria", "Aplicação web full-stack com LLM"],
        ["Recursos exigidos atendidos", "LLM • API • Persistência • Interface"],
        ["Stack principal", "Python • Streamlit • SQLAlchemy • Anthropic Claude"],
        ["Tipo de entrega", "Documento PDF + código-fonte funcional"],
    ]
    cover_table = Table(cover_data, colWidths=[5.5 * cm, 10 * cm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
    ]))
    story.append(cover_table)
    story.append(PageBreak())

    # ===== SUMÁRIO =====
    story.append(p("Sumário", style_h1))
    story.append(hr())
    sumario = [
        ("1.", "Apresentação do projeto"),
        ("2.", "Objetivos"),
        ("3.", "Atendimento aos requisitos da disciplina"),
        ("4.", "Arquitetura do sistema"),
        ("5.", "Modelo de dados (persistência)"),
        ("6.", "Integração com a LLM (uso da API)"),
        ("7.", "Funcionalidades implementadas"),
        ("8.", "Fluxo de uma operação completa"),
        ("9.", "Stack tecnológica"),
        ("10.", "Estrutura de arquivos"),
        ("11.", "Como executar"),
        ("12.", "Discussão de complexidade e decisões de projeto"),
        ("13.", "Possíveis evoluções"),
        ("14.", "Conclusão"),
    ]
    sum_data = [[n, t] for n, t in sumario]
    sum_table = Table(sum_data, colWidths=[1.2 * cm, 14 * cm])
    sum_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1e40af")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sum_table)
    story.append(PageBreak())

    # ===== 1. APRESENTAÇÃO =====
    story.append(p("1. Apresentação do projeto", style_h1))
    story.append(hr())
    story.append(p(
        "<b>TaskMind AI</b> é uma aplicação web de gerenciamento de tarefas em "
        "que um modelo de linguagem (LLM) atua como copiloto de produtividade. "
        "Diferente de gerenciadores convencionais, o sistema vai além do CRUD: "
        "a IA <b>decompõe</b> tarefas grandes em subtarefas executáveis, "
        "<b>estima</b> o tempo necessário, <b>prioriza</b> a lista do usuário "
        "atribuindo um score com justificativa e ainda permite que o usuário "
        "<b>converse</b> em linguagem natural sobre suas pendências."
    ))
    story.append(p(
        "O projeto foi concebido para demonstrar, de forma integrada e em "
        "funcionamento real, todos os pilares solicitados no enunciado da "
        "disciplina: uso obrigatório de LLM, consumo de API, persistência de "
        "dados e uma interface utilizável."
    ))

    # ===== 2. OBJETIVOS =====
    story.append(p("2. Objetivos", style_h1))
    story.append(hr())
    story.append(p("<b>Objetivo geral.</b> Construir uma aplicação funcional "
                   "que integre um modelo de linguagem ao fluxo de trabalho "
                   "de produtividade pessoal, mostrando o valor prático da IA "
                   "quando bem acoplada a um sistema persistente."))
    story.append(p("<b>Objetivos específicos:</b>"))
    objs = [
        "Implementar persistência relacional com SQLAlchemy + SQLite, modelando entidades com relacionamento 1:N.",
        "Integrar a API REST da Anthropic (Claude) usando o SDK oficial, com cinco operações distintas de IA.",
        "Garantir respostas estruturadas da LLM via JSON forçado em system prompt, com parser tolerante a falhas.",
        "Oferecer interface web responsiva, com dashboard analítico em Plotly e chat conversacional.",
        "Demonstrar boas práticas de separação em camadas: apresentação, serviço LLM e persistência.",
    ]
    for o in objs:
        story.append(p(f"&bull;&nbsp;&nbsp;{o}"))

    # ===== 3. REQUISITOS =====
    story.append(p("3. Atendimento aos requisitos da disciplina", style_h1))
    story.append(hr())
    story.append(p("O enunciado é explícito quanto à obrigatoriedade de LLM "
                   "e elenca outros recursos que podem compor o projeto. "
                   "A tabela a seguir mapeia cada requisito a como ele é "
                   "atendido no TaskMind AI."))
    req_data = [
        ["Requisito", "Como é atendido"],
        ["Uso obrigatório de LLM",
         "Cinco funções em llm_service.py (decomposição, estimativa, "
         "priorização, chat e relatório) usam o modelo Claude."],
        ["Uso de API",
         "Consumo da API REST da Anthropic via SDK oficial python "
         "(anthropic.Anthropic). Cada função abre uma chamada /v1/messages."],
        ["Persistência",
         "SQLite via SQLAlchemy ORM com 4 entidades (Task, Subtask, Report, "
         "ChatMessage) e relacionamento 1:N entre Task e Subtask."],
        ["Complexidade",
         "Três camadas separadas, parser JSON robusto, eager loading, "
         "tratamento de erros, validação de entrada e dashboard com gráficos."],
        ["Funcionando",
         "Aplicação roda com `streamlit run app.py` e foi validada "
         "(HTTP 200, todos os fluxos CRUD e LLM testados)."],
    ]
    story.append(make_table(req_data, col_widths=[4.5 * cm, 11.5 * cm]))

    # ===== 4. ARQUITETURA =====
    story.append(PageBreak())
    story.append(p("4. Arquitetura do sistema", style_h1))
    story.append(hr())
    story.append(p(
        "O sistema segue uma arquitetura em três camadas claramente "
        "delimitadas, comunicando-se via interfaces explícitas. A LLM é "
        "tratada como serviço externo, consumido apenas pela camada de "
        "serviços (nunca diretamente pela interface)."
    ))
    story.append(architecture_diagram())
    story.append(p(
        "A camada de <b>apresentação</b> (Streamlit) é responsável apenas por "
        "renderizar a UI e capturar interações. Ela invoca funções da camada "
        "de <b>serviço LLM</b> ou da <b>persistência</b>, mas nunca conhece "
        "detalhes de prompts ou SQL. O <b>serviço LLM</b> encapsula toda a "
        "lógica de prompting, parsing e tratamento de erros da API externa. "
        "A camada de <b>persistência</b> expõe operações de alto nível "
        "(create_task, list_tasks, etc.) sobre o ORM."
    ))

    # ===== 5. MODELO DE DADOS =====
    story.append(p("5. Modelo de dados (persistência)", style_h1))
    story.append(hr())
    story.append(p(
        "O banco SQLite é gerenciado pelo SQLAlchemy ORM. Quatro entidades "
        "compõem o domínio. Os campos prefixados com <i>ai_</i> são "
        "preenchidos automaticamente pela LLM."
    ))
    story.append(er_diagram())
    story.append(p(
        "Destaca-se o relacionamento 1:N entre <b>Task</b> e <b>Subtask</b>, "
        "com cascade delete (apagar uma tarefa remove as subtarefas). O "
        "código abaixo mostra a definição do modelo Task no ORM:"
    ))
    story.append(code(
        'class Task(Base):\n'
        '    __tablename__ = "tasks"\n'
        '    id = Column(Integer, primary_key=True)\n'
        '    title = Column(String(200), nullable=False)\n'
        '    description = Column(Text, default="")\n'
        '    priority = Column(String(20), default="média")\n'
        '    status = Column(String(20), default="pendente")\n'
        '    due_date = Column(Date, nullable=True)\n'
        '    estimated_minutes = Column(Integer, nullable=True)   # IA\n'
        '    ai_priority_score = Column(Integer, nullable=True)   # IA\n'
        '    ai_reasoning = Column(Text, default="")              # IA\n'
        '    created_at = Column(DateTime, default=datetime.utcnow)\n'
        '    subtasks = relationship("Subtask", back_populates="task",\n'
        '                            cascade="all, delete-orphan")'
    ))

    # ===== 6. INTEGRAÇÃO LLM =====
    story.append(PageBreak())
    story.append(p("6. Integração com a LLM (uso da API)", style_h1))
    story.append(hr())
    story.append(p(
        "Toda a comunicação com o modelo é centralizada em "
        "<b>llm_service.py</b>. A configuração do cliente é feita via "
        "variável de ambiente <i>ANTHROPIC_API_KEY</i>, carregada com "
        "<i>python-dotenv</i>. As cinco funções de IA implementadas estão "
        "descritas na tabela:"
    ))
    llm_data = [
        ["Função", "O que faz", "Forma da resposta"],
        ["decompose_task", "Quebra a tarefa em 3–8 subtarefas executáveis.",
         "JSON com array de strings"],
        ["estimate_time", "Estima minutos de trabalho focado.",
         "JSON com inteiro 5–600"],
        ["prioritize_tasks", "Atribui score 0–100 e justificativa a cada "
         "tarefa não-concluída.", "JSON com array de objetos"],
        ["chat_about_tasks", "Responde perguntas tendo as tarefas como "
         "contexto. Mantém histórico.", "Texto livre"],
        ["generate_productivity_report", "Gera relatório semanal de "
         "produtividade.", "Markdown estruturado"],
    ]
    story.append(make_table(llm_data, col_widths=[4 * cm, 7.5 * cm, 4 * cm]))

    story.append(p("<b>Estratégia para respostas estruturadas.</b> Onde a "
                   "resposta precisa ser parseada (decompose, estimate, "
                   "prioritize), o <i>system prompt</i> exige JSON estrito. "
                   "Em seguida, a função <b>_extract_json()</b> tenta:"))
    extract_strategy = [
        "remover cercas <i>```json</i> que o modelo às vezes inclui;",
        "parsear o texto bruto diretamente;",
        "se falhar, localizar o primeiro <b>{</b> ou <b>[</b> e o último <b>}</b> ou <b>]</b> e tentar parsear o substring;",
        "retornar <i>None</i> se nada funcionar (a UI mostra erro amigável).",
    ]
    for e in extract_strategy:
        story.append(p(f"&bull;&nbsp;&nbsp;{e}"))

    story.append(p("<b>Exemplo de prompt usado em decompose_task:</b>"))
    story.append(code(
        'system = (\n'
        '    "Você é um assistente de produtividade. Sua função é quebrar uma "\n'
        '    "tarefa em subtarefas pequenas, executáveis e ordenadas. "\n'
        '    "Responda SOMENTE com JSON válido no formato: "\n'
        '    \'{"subtasks": ["passo 1", "passo 2", ...]}\'\n'
        ')\n'
        'user = (\n'
        '    f"Tarefa: {title}\\n"\n'
        '    f"Descrição: {description}\\n\\n"\n'
        '    "Gere de 3 a 8 subtarefas concretas, em português, "\n'
        '    "começando com verbo no infinitivo."\n'
        ')'
    ))

    story.append(p("<b>Injeção de contexto no chat.</b> No chat conversacional, "
                   "antes de cada chamada o serviço serializa a lista atual de "
                   "tarefas em JSON e a injeta no system prompt, junto com as "
                   "10 últimas mensagens do histórico. Assim a LLM \"conhece\" "
                   "o estado real do usuário sem precisar de RAG completo."))

    # ===== 7. FUNCIONALIDADES =====
    story.append(PageBreak())
    story.append(p("7. Funcionalidades implementadas", style_h1))
    story.append(hr())
    feats = [
        ("Dashboard",
         "Visão geral com 4 métricas principais (total, concluídas, em "
         "andamento, pendentes), gráfico de pizza por status, barras por "
         "prioridade e lista ordenada dos próximos prazos com indicadores "
         "visuais de urgência (hoje, atrasada, em N dias)."),
        ("Nova tarefa",
         "Formulário com título, descrição, prioridade e prazo. Checkboxes "
         "opcionais para acionar decomposição e estimativa de tempo pela IA "
         "no momento da criação."),
        ("Minhas tarefas",
         "Lista completa com filtros por status, exibição de subtarefas "
         "checáveis, ações inline (mudar status, decompor, estimar, "
         "excluir) e justificativa da IA quando disponível."),
        ("Priorização IA",
         "Botão único que envia todas as tarefas pendentes à LLM e recebe "
         "ranking com score 0-100 + justificativa para cada item."),
        ("Chat com IA",
         "Interface de chat em tempo real onde o assistente tem acesso "
         "contextual à lista de tarefas. Histórico persistido em banco."),
        ("Relatório semanal",
         "Gera relatório em Markdown com resumo numérico, destaques, "
         "pontos de atenção e três recomendações práticas."),
    ]
    for name, desc in feats:
        story.append(p(f"<b>{name}</b>", style_h3))
        story.append(p(desc))

    # ===== 8. FLUXO =====
    story.append(p("8. Fluxo de uma operação completa", style_h1))
    story.append(hr())
    story.append(p(
        "Para ilustrar como as camadas conversam, considere o fluxo de "
        "criação de uma tarefa com IA habilitada. O usuário preenche o "
        "formulário e clica em <i>Criar tarefa</i>:"
    ))
    story.append(flow_diagram())
    story.append(p(
        "(1) o frontend invoca <b>db.create_task(...)</b>, que abre uma "
        "transação no SQLite e persiste o registro base; (2) o frontend "
        "chama <b>llm.decompose_task(...)</b>, que envia o prompt à API e "
        "recebe o JSON com a lista de subtarefas; (3) chama "
        "<b>llm.estimate_time(...)</b>, que retorna um inteiro em minutos; "
        "(4) ambos os retornos são persistidos via <b>add_subtasks</b> e "
        "<b>update_task</b>; (5) a UI re-renderiza com balões de sucesso e "
        "exibe as subtarefas geradas."
    ))

    # ===== 9. STACK =====
    story.append(p("9. Stack tecnológica", style_h1))
    story.append(hr())
    stack_data = [
        ["Camada", "Tecnologia", "Versão", "Justificativa"],
        ["Linguagem", "Python", "3.10+",
         "Ecossistema maduro para IA e web."],
        ["Interface", "Streamlit", "≥ 1.32",
         "Permite UI web reativa com pouco código."],
        ["LLM SDK", "anthropic", "≥ 0.40",
         "SDK oficial para Claude, suporte ao endpoint /v1/messages."],
        ["ORM", "SQLAlchemy", "≥ 2.0",
         "Padrão de mercado para acesso relacional em Python."],
        ["Banco", "SQLite", "embutido",
         "Zero configuração, ideal para aplicação local."],
        ["Gráficos", "Plotly Express", "≥ 5.18",
         "Visualizações interativas com integração nativa ao Streamlit."],
        ["Config", "python-dotenv", "≥ 1.0",
         "Carrega variáveis de ambiente do .env de forma segura."],
    ]
    story.append(make_table(
        stack_data, col_widths=[2.8 * cm, 3 * cm, 1.8 * cm, 7.9 * cm]
    ))

    # ===== 10. ESTRUTURA =====
    story.append(p("10. Estrutura de arquivos", style_h1))
    story.append(hr())
    story.append(code(
        'taskmind-ai/\n'
        '|-- app.py             # Interface Streamlit (entrypoint)\n'
        '|-- database.py        # Modelos ORM e operacoes CRUD\n'
        '|-- llm_service.py     # Integracao com a API do Claude\n'
        '|-- requirements.txt   # Dependencias Python\n'
        '|-- .env.example       # Template de variaveis de ambiente\n'
        '|-- README.md          # Instrucoes de execucao\n'
        '|-- DOCUMENTACAO.pdf   # Este documento\n'
        "`-- data/\n"
        "    `-- taskmind.db    # SQLite (criado no 1o uso)"
    ))

    # ===== 11. COMO EXECUTAR =====
    story.append(p("11. Como executar", style_h1))
    story.append(hr())
    story.append(p("<b>Pré-requisitos:</b> Python 3.10 ou superior e uma "
                   "chave da API da Anthropic (obtida em "
                   "<i>console.anthropic.com</i>)."))
    story.append(p("<b>Passo 1 — instalar dependências:</b>"))
    story.append(code(
        '$ cd taskmind-ai\n'
        '$ python -m venv .venv\n'
        '$ source .venv/bin/activate     # Linux/Mac\n'
        '$ .venv\\Scripts\\activate       # Windows\n'
        '$ pip install -r requirements.txt'
    ))
    story.append(p("<b>Passo 2 — configurar a chave:</b>"))
    story.append(code(
        '$ cp .env.example .env\n'
        '# Editar o .env e preencher:\n'
        'ANTHROPIC_API_KEY=sk-ant-...\n'
        'ANTHROPIC_MODEL=claude-sonnet-4-6'
    ))
    story.append(p("<b>Passo 3 — executar:</b>"))
    story.append(code(
        '$ streamlit run app.py\n'
        '# Abrir o navegador em http://localhost:8501'
    ))

    # ===== 12. DISCUSSÃO =====
    story.append(PageBreak())
    story.append(p("12. Discussão de complexidade e decisões de projeto",
                   style_h1))
    story.append(hr())

    story.append(p("<b>Separação de responsabilidades.</b>", style_h3))
    story.append(p(
        "A decisão de isolar a LLM em um módulo próprio (em vez de espalhar "
        "chamadas pelo app.py) tem benefícios diretos: facilita troca do "
        "provedor (poderia ser OpenAI, Gemini, modelo local), simplifica "
        "testes (basta mockar o módulo) e mantém o código de UI legível. "
        "O mesmo vale para a persistência: a UI nunca toca em sessões do "
        "SQLAlchemy diretamente."
    ))

    story.append(p("<b>Resposta estruturada via JSON forçado.</b>", style_h3))
    story.append(p(
        "Em vez de tentar parsear texto livre da LLM, o sistema instrui "
        "explicitamente o formato JSON no system prompt e implementa um "
        "parser <i>defensivo</i> capaz de lidar com pequenas violações "
        "(blocos de markdown, texto explicativo antes/depois). Essa "
        "estratégia é mais simples e barata do que usar function calling, "
        "mas garante robustez prática."
    ))

    story.append(p("<b>Persistência de instâncias com eager loading.</b>",
                   style_h3))
    story.append(p(
        "Por usar sessões temporárias (<i>with get_session()</i>), foi "
        "necessário configurar <i>expire_on_commit=False</i> e usar "
        "<i>joinedload</i> para carregar subtarefas junto com tarefas — "
        "evitando o clássico <i>DetachedInstanceError</i> que aparece "
        "quando objetos do ORM são acessados fora da sessão original."
    ))

    story.append(p("<b>Contexto no chat sem RAG completo.</b>", style_h3))
    story.append(p(
        "Como o volume de tarefas de um usuário individual é pequeno "
        "(dezenas a poucas centenas), foi feita a escolha de injetar a "
        "lista completa serializada em JSON no system prompt do chat. "
        "Isso evita a complexidade de embeddings + vector store para um "
        "caso onde caberia tudo na janela de contexto, mantendo o projeto "
        "no nível de complexidade compatível com o escopo."
    ))

    # ===== 13. EVOLUÇÕES =====
    story.append(p("13. Possíveis evoluções", style_h1))
    story.append(hr())
    evolu = [
        "Implementar RAG completo com FAISS/Chroma para suportar bases de tarefas grandes.",
        "Adicionar autenticação multi-usuário com Postgres em vez de SQLite.",
        "Integrar Google Calendar para sincronizar prazos.",
        "Adicionar reconhecimento de fala para criação por voz.",
        "Permitir anexar arquivos a tarefas (suporte multimodal com Claude).",
        "Expor uma API REST (FastAPI) paralela para integração com outros clientes.",
    ]
    for e in evolu:
        story.append(p(f"&bull;&nbsp;&nbsp;{e}"))

    # ===== 14. CONCLUSÃO =====
    story.append(p("14. Conclusão", style_h1))
    story.append(hr())
    story.append(p(
        "O <b>TaskMind AI</b> demonstra, em uma aplicação enxuta e em "
        "funcionamento, como integrar um modelo de linguagem ao núcleo de "
        "uma aplicação útil — não como adorno. A IA participa do ciclo de "
        "vida das tarefas: ajuda a criar (decompondo), a planejar "
        "(estimando e priorizando), a executar (no chat conversacional) "
        "e a refletir (no relatório semanal)."
    ))
    story.append(p(
        "Todos os requisitos do enunciado foram atendidos: o projeto usa "
        "obrigatoriamente uma LLM, consome uma API externa, persiste "
        "dados de forma estruturada e oferece uma interface utilizável. "
        "A separação em camadas, o tratamento defensivo da saída do "
        "modelo e o uso correto do ORM compõem um conjunto de boas "
        "práticas que dão consistência ao trabalho."
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(hr())
    story.append(p("<i>Fim do documento.</i>",
                   ParagraphStyle("end", parent=style_body,
                                  alignment=TA_CENTER,
                                  textColor=colors.HexColor("#64748b"))))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    build()
