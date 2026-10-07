from html import escape

from .diagram_renderer import render_diagram


def esc(value):
    """
    Safely escape text before putting it into HTML.
    """
    if value is None:
        return ""

    return escape(str(value))


# ==========================================================
# Practice Question Renderer
# ==========================================================

def render_practice_question(question):
    """
    Render one lecture practice question.
    """

    parts = []

    parts.append(
        f"<div class='question-card'>"
        f"<h4>📝 {esc(question.question)}</h4>"
    )

    if question.given:
        parts.append(
            f"<div class='subbox'>"
            f"<b>Given:</b><br>{esc(question.given)}"
            f"</div>"
        )

    if question.approach:
        parts.append(
            f"<div class='subbox'>"
            f"<b>Approach:</b><br>{esc(question.approach)}"
            f"</div>"
        )

    if question.solution_steps:
        parts.append(
            "<div class='subbox'>"
            "<b>Solution:</b>"
            "<ol>"
        )

        for step in question.solution_steps:
            parts.append(
                f"<li>{esc(step)}</li>"
            )

        parts.append(
            "</ol>"
            "</div>"
        )

    if question.final_answer:
        parts.append(
            f"<div class='answer-box'>"
            f"<b>Final Answer:</b><br>"
            f"{esc(question.final_answer)}"
            f"</div>"
        )

    if question.explanation:
        parts.append(
            f"<div class='subbox'>"
            f"<b>Explanation:</b><br>"
            f"{esc(question.explanation)}"
            f"</div>"
        )

    parts.append("</div>")

    return "".join(parts)


# ==========================================================
# Lecture Table Renderer
# ==========================================================

def render_table(table):
    """
    Render a lecture table.
    """

    parts = [
        "<div class='lecture-table-card'>"
    ]

    if table.title:
        parts.append(
            f"<h4>📊 {esc(table.title)}</h4>"
        )

    if table.columns:
        parts.append("<table>")
        parts.append("<thead><tr>")

        for column in table.columns:
            parts.append(
                f"<th>{esc(column)}</th>"
            )

        parts.append("</tr></thead>")

    if table.rows:
        parts.append("<tbody>")

        for row in table.rows:
            parts.append("<tr>")

            for value in row:
                parts.append(
                    f"<td>{esc(value)}</td>"
                )

            parts.append("</tr>")

        parts.append("</tbody></table>")

    if table.explanation:
        parts.append(
            f"<div class='table-explanation'>"
            f"{esc(table.explanation)}"
            f"</div>"
        )

    parts.append("</div>")

    return "".join(parts)


# ==========================================================
# Visual Insight Renderer
# ==========================================================

def render_visual(visual):
    """
    Render one visual extracted from the lecture video.

    Supports:
    - slide
    - board
    - diagram
    - table
    - formula
    - question
    - example
    - image
    - other
    """

    parts = []

    parts.append("<div class='visual-card'>")

    # Timestamp
    if visual.timestamp:
        parts.append(
            f"<div class='visual-time'>"
            f"⏱ {esc(visual.timestamp)}"
            f"</div>"
        )

    # Visual type
    if visual.type:
        parts.append(
            f"<div class='visual-type'>"
            f"{esc(visual.type.upper())}"
            f"</div>"
        )

    # Title
    if visual.title:
        parts.append(
            f"<h4>{esc(visual.title)}</h4>"
        )

    # Main visual description/content
    if visual.content:
        parts.append(
            f"<div class='visual-content'>"
            f"{esc(visual.content)}"
            f"</div>"
        )

    # Important visible text
    if visual.important_text:
        parts.append(
            "<div class='visual-text-box'>"
            "<b>Visible / Important Text:</b>"
            "<ul>"
        )

        for item in visual.important_text:
            parts.append(
                f"<li>{esc(item)}</li>"
            )

        parts.append(
            "</ul>"
            "</div>"
        )

    parts.append("</div>")

    return "".join(parts)


# ==========================================================
# Main Notes Renderer
# ==========================================================

def render_notes(notes, note_id=None, visual_status=None):

    sec = []

    # ======================================================
    # Sections
    # ======================================================

    for s in notes.sections:

        b = []

        # ---------------------------------------------
        # Basic concept information
        # ---------------------------------------------

        for title, val in [
            ("Definition", s.definition),
            ("Intuition", s.intuition),
            ("Explanation", s.explanation),
            ("Example", s.example),
            ("Formula", s.formula),
            ("Complexity", s.complexity),
        ]:

            if val:
                b.append(
                    f"<h3>{title}</h3>"
                    f"<div class='boxtext'>{esc(val)}</div>"
                )

        # ---------------------------------------------
        # ALL lecture examples
        # ---------------------------------------------

        if getattr(s, "examples", None):

            b.append(
                "<h3>📌 Lecture Examples</h3>"
                "<div class='example-list'>"
                +
                "".join(
                    f"<div class='boxtext example-item'>"
                    f"<strong>Example {i}:</strong><br>"
                    f"{esc(example)}"
                    f"</div>"
                    for i, example in enumerate(s.examples, 1)
                    if example
                )
                +
                "</div>"
            )

        # ---------------------------------------------
        # Steps
        # ---------------------------------------------

        if s.steps:

            b.append(
                "<h3>Steps</h3>"
                "<ol>"
                +
                "".join(
                    f"<li>{esc(x)}</li>"
                    for x in s.steps
                )
                +
                "</ol>"
            )

        # ---------------------------------------------
        # Key points / mistakes / exam tips
        # ---------------------------------------------

        for title, vals in [
            ("Key Points", s.key_points),
            ("Common Mistakes", s.common_mistakes),
            ("Exam Tips", s.exam_tips),
        ]:

            if vals:

                b.append(
                    f"<h3>{title}</h3>"
                    "<ul>"
                    +
                    "".join(
                        f"<li>{esc(x)}</li>"
                        for x in vals
                    )
                    +
                    "</ul>"
                )

        # ---------------------------------------------
        # Practice Questions
        # ---------------------------------------------

        if s.practice_questions:

            b.append(
                "<h3>📝 Practice Questions</h3>"
            )

            for question in s.practice_questions:

                b.append(
                    render_practice_question(question)
                )

        # ---------------------------------------------
        # Lecture Tables
        # ---------------------------------------------

        if s.tables:

            b.append(
                "<h3>📊 Lecture Tables</h3>"
            )

            for table in s.tables:

                b.append(
                    render_table(table)
                )

        # ---------------------------------------------
        # Diagram
        # ---------------------------------------------

        if s.diagram:

            b.append(
                render_diagram(s.diagram)
            )

        # ---------------------------------------------
        # Section
        # ---------------------------------------------

        sec.append(
            f"<section>"
            f"<h2>{esc(s.title)}</h2>"
            f"{''.join(b)}"
            f"</section>"
        )

    # ======================================================
    # Lecture Visuals
    #
    # IMPORTANT:
    # visuals are LectureNotes-level data,
    # so they are rendered OUTSIDE the section loop.
    # ======================================================

    visual_html = ""

    if getattr(notes, "visuals", None):

        visual_parts = []

        visual_parts.append(
            "<section class='visuals-section'>"
            "<h2>🎥 Lecture Visuals</h2>"
            "<div class='visual-intro'>"
            "Important slides, board content, diagrams, tables, "
            "formulas and other useful visuals detected from the lecture."
            "</div>"
        )

        for visual in notes.visuals:

            visual_parts.append(
                render_visual(visual)
            )

        visual_parts.append("</section>")

        visual_html = "".join(visual_parts)

    # ======================================================
    # Final HTML
    # ======================================================

    return f"""
<!doctype html>

<html>

<head>

<meta charset="utf-8">

<title>{esc(notes.lecture_title)}</title>

<link
    href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&display=swap"
    rel="stylesheet"
>

<style>

/* =====================================================
   Base Page
   ===================================================== */

body {{
    margin: 0;
    background: #e8e1d2;
    font-family: Kalam, cursive;
    color: #29251f;
}}

.page {{
    max-width: 1050px;
    margin: 28px auto;
    padding: 50px 65px;

    background: #fffdf6;

    box-shadow: 0 8px 30px #0002;

    background-image:
        linear-gradient(
            #0000 31px,
            #b7d0e333 32px
        );

    background-size: 100% 32px;
}}


/* =====================================================
   Headings
   ===================================================== */

h1 {{
    font-size: 36px;
}}

h2 {{
    font-size: 27px;
    border-bottom: 2px dashed #82776a;
    padding-bottom: 5px;
}}

h3 {{
    font-size: 19px;
}}

h4 {{
    font-size: 18px;
    margin-top: 5px;
}}

p,
li,
.boxtext {{
    font-size: 17px;
    line-height: 1.55;
}}

.boxtext {{
    padding: 10px 15px;
    border-left: 4px solid #635b51;
    background: #f4efe3;
    margin-bottom: 12px;
}}


/* =====================================================
   Practice Question
   ===================================================== */

.question-card {{
    margin: 18px 0;
    padding: 18px;

    background: #fffaf0;

    border: 2px dashed #8b8174;

    border-radius: 14px;
}}

.question-card h4 {{
    margin-top: 0;
    font-size: 20px;
}}

.subbox {{
    margin-top: 10px;
    padding: 10px 14px;

    background: #f4efe3;

    border-left: 4px solid #635b51;

    font-size: 16px;
    line-height: 1.5;
}}

.answer-box {{
    margin-top: 12px;
    padding: 12px 15px;

    background: #e9ead8;

    border-left: 5px solid #575f43;

    font-size: 17px;
}}


/* =====================================================
   Lecture Table
   ===================================================== */

.lecture-table-card {{
    margin: 20px 0;
    padding: 16px;

    background: #fffaf0;

    border: 2px dashed #8b8174;

    border-radius: 14px;

    overflow-x: auto;
}}

.lecture-table-card h4 {{
    margin-top: 0;
    font-size: 20px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 16px;
}}

th,
td {{
    border: 1.5px solid #6f665b;
    padding: 9px 11px;
    text-align: left;
    vertical-align: top;
}}

th {{
    background: #e7dfce;
    font-weight: 700;
}}

td {{
    background: #fffdf6;
}}

.table-explanation {{
    margin-top: 12px;
    padding: 10px 14px;

    background: #f4efe3;

    border-left: 4px solid #635b51;

    font-size: 16px;
    line-height: 1.5;
}}


/* =====================================================
   Lecture Visuals
   ===================================================== */

.visuals-section {{
    margin-top: 35px;
}}

.visual-intro {{
    margin: 12px 0 20px 0;
    padding: 12px 15px;

    background: #f4efe3;

    border-left: 4px solid #635b51;

    font-size: 16px;
    line-height: 1.5;
}}

.visual-card {{
    margin: 20px 0;
    padding: 18px;

    background: #fffaf0;

    border: 2px dashed #8b8174;

    border-radius: 14px;
}}

.visual-card h4 {{
    margin-top: 12px;
    margin-bottom: 12px;
    font-size: 21px;
}}

.visual-time {{
    display: inline-block;

    padding: 5px 10px;

    background: #e7dfce;

    border-radius: 8px;

    font-size: 15px;
    font-weight: 700;
}}

.visual-type {{
    display: inline-block;

    margin-left: 8px;

    padding: 4px 8px;

    border-radius: 7px;

    background: #f0eadb;

    font-size: 13px;
    font-weight: 700;
}}

.visual-content {{
    margin-top: 12px;

    padding: 12px 15px;

    background: #f4efe3;

    border-left: 4px solid #635b51;

    font-size: 17px;
    line-height: 1.55;

    white-space: pre-wrap;
}}

.visual-text-box {{
    margin-top: 12px;

    padding: 10px 14px;

    background: #f4efe3;

    border-left: 4px solid #635b51;

    font-size: 16px;

    line-height: 1.5;
}}

.visual-text-box ul {{
    margin-bottom: 5px;
}}


/* =====================================================
   Diagrams
   ===================================================== */

.diagram-wrap {{
    margin: 20px 0;
    padding: 12px;

    background: #fffdf6;

    border: 2px dashed #8b8174;

    border-radius: 15px;

    overflow: hidden;
}}

.diagram-title {{
    font-size: 20px;
}}

svg {{
    width: 100%;
    height: auto;
}}

.box,
.treebox,
.circlebox {{
    fill: #fffaf0;
    stroke: #4d463d;
    stroke-width: 2;
}}

.treebox {{
    fill: #f9f3df;
}}

.circlebox {{
    fill: #f7efe1;
}}

.edge {{
    stroke: #4b453d;
    stroke-width: 2.2;
}}

text {{
    font-family: Kalam, cursive;
    fill: #2f2a24;
    font-size: 17px;
}}


.visual-status-box {{
    margin-top: 24px;
    padding: 12px 16px;
    border: 1px dashed #8b8174;
    border-radius: 12px;
    background: #fffaf0;
    font-size: 14px;
}}


/* =====================================================
   Mobile
   ===================================================== */

@media (max-width: 700px) {{

    .page {{
        margin: 0;
        padding: 30px 20px;
    }}

    h1 {{
        font-size: 30px;
    }}

    h2 {{
        font-size: 24px;
    }}

    table {{
        min-width: 600px;
    }}

    .visual-card {{
        padding: 14px;
    }}

    .visual-time {{
        font-size: 13px;
    }}

    .visual-type {{
        font-size: 11px;
    }}
}}


/* =====================================================
   Print
   ===================================================== */

@media print {{

    body {{
        background: white;
    }}

    .page {{
        box-shadow: none;
        margin: 0;
        max-width: none;
    }}

    .visual-card,
    .question-card,
    .lecture-table-card {{
        break-inside: avoid;
    }}
}}

</style>

</head>


<body>

<div class="page">

<h1>
    ✍️ {esc(notes.lecture_title)}
</h1>

<div class="boxtext">
    <b>Overview:</b>
    {esc(notes.overview)}
</div>

{''.join(sec)}

{visual_html}

<div id="visual-status" class="visual-status-box">
    {"🎥 Visual analysis is running in the background. Notes are ready; this page will refresh automatically." if visual_status == "processing" else ""}
</div>

</div>

<script>
(function () {{
    const noteId = {repr(note_id)};
    const initialStatus = {repr(visual_status)};
    if (!noteId || initialStatus !== "processing") return;
    const timer = setInterval(async function () {{
        try {{
            const response = await fetch("/api/notes/" + noteId + "/status", {{ cache: "no-store" }});
            if (!response.ok) return;
            const data = await response.json();
            if (data.visual_status === "completed" || data.visual_status === "failed") {{
                clearInterval(timer);
                window.location.reload();
            }}
        }} catch (_) {{}}
    }}, 5000);
}})();
</script>

</body>

</html>
"""