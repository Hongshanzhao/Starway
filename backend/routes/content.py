# routes/content.py
from flask import Blueprint, request, jsonify
from db import get_db

content_bp = Blueprint('content', __name__, url_prefix='/api')

@content_bp.route('/contents', methods=['GET'])
def get_contents():
    """
    获取内容列表（支持分页、分类筛选、排序）
    查询参数：
        page: 页码（默认1）
        size: 每页条数（默认8）
        category: 分类（direction/template/case，可选）
        sort_by: 排序字段（sort_order/id/title，默认sort_order）
        order: 排序方向（asc/desc，默认asc）
    """
    # 获取参数
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 8, type=int)
    category = request.args.get('category')
    sort_by = request.args.get('sort_by', 'sort_order')
    order = request.args.get('order', 'asc')

    # 参数校验
    if page < 1 or size < 1:
        return jsonify({"error": "分页参数无效"}), 400

    allowed_sort_fields = ['sort_order', 'id', 'title']
    if sort_by not in allowed_sort_fields:
        sort_by = 'sort_order'
    if order.lower() not in ['asc', 'desc']:
        order = 'asc'

    offset = (page - 1) * size
    conn = get_db()
    cursor = conn.cursor()

    # 构建查询
    base_sql = "SELECT id, title, img_url, stage, type FROM content"
    count_sql = "SELECT COUNT(*) FROM content"
    params = []

    if category:
        base_sql += " WHERE category = ?"
        count_sql += " WHERE category = ?"
        params.append(category)

    # 排序
    base_sql += f" ORDER BY {sort_by} {order}"

    # 分页
    base_sql += " LIMIT ? OFFSET ?"
    params_page = params + [size, offset]

    # 执行查询
    cursor.execute(base_sql, params_page)
    rows = cursor.fetchall()

    # 获取总条数
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    conn.close()

    # 构造返回数据
    items = []
    for row in rows:
        items.append({
            "id": row['id'],
            "title": row['title'],
            "imgUrl": row['img_url'],
            "stage": row['stage'],
            "type": row['type']
        })

    return jsonify({
        "total": total,
        "page": page,
        "size": size,
        "data": items
    })