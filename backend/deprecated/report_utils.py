import io
from flask import send_file
from db import get_db

def get_report_row(report_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM report_history WHERE id = ?', (report_id,))
    row = cur.fetchone()
    conn.close()
    return row


def export_report_file(report_id: int, fmt: str = 'html'):
    """
    返回一个 Flask 可返回的 send_file 对象（BytesIO）和 mime 类型/文件名。
    如果 fmt == 'pdf' 会尝试使用 pdfkit 生成 PDF，否则返回 HTML 字节流。
    """
    row = get_report_row(report_id)
    if not row:
        return None

    content = row['content'] or '<div>无内容</div>'

    if fmt == 'pdf':
        try:
            import pdfkit
            pdf_bytes = pdfkit.from_string(content, False)
            bio = io.BytesIO(pdf_bytes)
            bio.seek(0)
            return send_file(bio, as_attachment=True, download_name=f'report_{report_id}.pdf', mimetype='application/pdf')
        except Exception:
            # 回退到 HTML
            pass

    bio = io.BytesIO()
    bio.write(content.encode('utf-8'))
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name=f'report_{report_id}.html', mimetype='text/html')
