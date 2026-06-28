"""
数据库初始化核心脚本
功能：创建项目所有数据表、建立数据库连接、导入岗位Excel数据

重要说明：
1. 本表包含项目早期设计的所有数据表，部分表仅为预留/历史版本，当前系统未实际使用；
2. 部分表结构经过多次迭代修改，旧字段/废弃表未删除，仅作历史保留；
4. 其余未使用表均为历史遗留或废弃功能，不影响当前系统运行。
"""

import sqlite3
import os
import re
import json
from config import SQLITE_DB_PATH, UPLOAD_FOLDER

try:
    import pandas as pd
except ImportError:
    pd = None

COLUMN_ALIASES = {
    "岗位名称": "job_name",
    "地址": "location",
    "薪资范围": "salary_range",
    "公司名称": "company",
    "所属行业": "industry",
    "公司规模": "company_size",
    "公司类型": "company_type",
    "岗位编码": "job_code",
    "岗位详情": "job_description",
    "更新日期": "updated_at",
    "公司详情": "company_info",
    "岗位来源地址": "source_url",
}

def get_db():
    db_dir = os.path.dirname(SQLITE_DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_columns(columns):
    new_cols = []
    for col in columns:
        if col in COLUMN_ALIASES:
            col = COLUMN_ALIASES[col]
        col = re.sub(r"\W+", "_", col)
        col = col.strip(" _").lower()
        if not col:
            col = "col"
        new_cols.append(col)
    return new_cols

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    try:
        from services.data_importer import ensure_core_tables
        ensure_core_tables(conn)
    except Exception as e:
        print(f"核心数据表初始化失败: {e}")

    # 如果存在 Excel 文件，自动创建 job 表并导入数据
    base_dir = os.path.dirname(__file__)
    excel_filename = '20260226105856_457.xls'  # 你的文件名
    excel_path = os.path.join(base_dir, excel_filename)
    if pd is not None and os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
        sanitized = sanitize_columns(df.columns.tolist())
        df.columns = sanitized

        # 核心修改1：不再将 job_code 设为主键，强制使用自增 id 作为主键
        col_defs = ['id INTEGER PRIMARY KEY AUTOINCREMENT']  # 固定自增主键
        for col in df.columns:
            dtype = str(df[col].dtype)
            if 'int' in dtype:
                typ = 'INTEGER'
            elif 'float' in dtype:
                typ = 'REAL'
            else:
                typ = 'TEXT'
            # 所有字段都作为普通字段，不设置主键约束
            col_defs.append(f"{col} {typ}")
        
        # 重建 job 表（先删除旧表，确保结构生效；如果需要保留旧数据，可注释掉 DROP TABLE）
        # cursor.execute("DROP TABLE IF EXISTS job")
        # 检查 job 表是否存在，不存在才创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE TABLE job ({', '.join(col_defs)})")
            print("✅ job 表已创建")
        else:
            print("⚠️ job 表已存在，跳过创建")

        # 检查 job 表是否已有数据，避免重复导入
        cursor.execute("SELECT COUNT(*) as cnt FROM job")
        result = cursor.fetchone()
        if result and result['cnt'] > 0:
            print(f"job 表中已有 {result['cnt']} 条数据，跳过 Excel 导入")
        else:
            # 批量导入数据，统计导入数量
            import_count = 0
            fail_count = 0
            fail_records = []

            for idx, row in df.iterrows():
                try:
                    values = [None if pd.isna(x) else x for x in row.tolist()]
                    cols = df.columns.tolist()
                    placeholders = ','.join('?' for _ in values)
                    cursor.execute(
                        f"INSERT INTO job ({','.join(cols)}) VALUES ({placeholders})",
                        values,
                    )
                    import_count += 1
                except Exception as e:
                    fail_count += 1
                    fail_records.append(f"第{idx+1}行导入失败: {str(e)}")

            # 打印导入结果，方便排查问题
            print(f"Excel数据导入完成：成功{import_count}条，失败{fail_count}条")
            if fail_records:
                print("失败记录详情：")
                for record in fail_records[:10]:  # 只打印前10条失败记录，避免刷屏
                    print(record)
            conn.commit()
    else:
        # 备用 job 表结构（如果你没有 Excel 文件，会创建这个）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                company TEXT,
                industry TEXT,
                salary_range TEXT,
                job_description TEXT,
                company_info TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    # ---------- 学生表 ----------
    # 原有 student 表创建（保留所有字段）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            major TEXT,
            grade TEXT,
            skills TEXT,
            certificates TEXT,
            internships TEXT,
            interests TEXT,
            completeness INTEGER,
            competitiveness INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ========== 新增字段（用于存储更详细的能力画像） ==========
    # 获取现有字段列表
    cursor.execute("PRAGMA table_info(student)")
    existing_columns = [row['name'] for row in cursor.fetchall()]
    
    # 需要添加的字段及其类型
    new_columns = [
        ('phone', 'TEXT'),
        ('email', 'TEXT'),
        ('education_text', 'TEXT'),
        ('work_text', 'TEXT'),
        ('project_text', 'TEXT'),
        ('skills_certs_text', 'TEXT'),
        ('summary', 'TEXT'),
        ('soft_abilities', 'TEXT'),
        ('interest_scores', 'TEXT'),
        ('education_json', 'TEXT'),
        ('work_json', 'TEXT'),
        ('project_json', 'TEXT')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE student ADD COLUMN {col_name} {col_type}")
            print(f"已添加字段 {col_name} 到 student 表")
    
    # 原有 user_id 字段检查（保留）
    cursor.execute("PRAGMA table_info(student)")
    cols = [row['name'] for row in cursor.fetchall()]
    if 'user_id' not in cols:
        cursor.execute("ALTER TABLE student ADD COLUMN user_id INTEGER")

    # 岗位画像表（用于存储大模型生成的单个岗位画像）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT UNIQUE,
            skills TEXT,
            certificates TEXT,
            soft_abilities TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 匹配结果表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            job_name TEXT,
            match_score REAL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 报告历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            job_name TEXT,
            content TEXT,
            format_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 验证码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            code TEXT,
            expires_at TIMESTAMP
        )
    ''')

    # 内容表（首页用）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            img_url TEXT,
            stage TEXT,
            type TEXT,
            category TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 用户扩展信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            name TEXT,
            gender TEXT,
            grade TEXT,
            major TEXT,
            target TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 兴趣选项表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            sort_order INTEGER DEFAULT 0
        )
    ''')

    # 用户兴趣关联表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interests (
            user_id INTEGER NOT NULL,
            interest_id INTEGER NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, interest_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (interest_id) REFERENCES interests(id) ON DELETE CASCADE
        )
    ''')

    # 能力维度表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ability_dimensions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            sort_order INTEGER DEFAULT 0
        )
    ''')

    # 用户能力评估记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ability_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            dimension_id INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (dimension_id) REFERENCES ability_dimensions(id) ON DELETE CASCADE
        )
    ''')

    # 用户规划主表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            target TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 规划阶段表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            period TEXT,
            status TEXT DEFAULT 'pending',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES user_plans(id) ON DELETE CASCADE
        )
    ''')

    # 阶段目标表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stage_id) REFERENCES plan_stages(id) ON DELETE CASCADE
        )
    ''')

    # 阶段里程碑表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stage_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stage_id) REFERENCES plan_stages(id) ON DELETE CASCADE
        )
    ''')

    # 发展路径类型表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS path_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon TEXT,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT,
            progress INTEGER DEFAULT 0,
            create_time TEXT,
            target_time TEXT,
            core_goal TEXT,
            ability_base TEXT,
            challenges TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 路径阶段模板表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS path_stage_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            period TEXT,
            status TEXT DEFAULT 'pending',
            sort_order INTEGER DEFAULT 0,
            goals TEXT,
            milestones TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (path_id) REFERENCES path_types(id) ON DELETE CASCADE
        )
    ''')

    # 学习资源表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            icon TEXT,
            color TEXT,
            title TEXT NOT NULL,
            description TEXT,
            duration TEXT,
            priority TEXT,
            link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 导师表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mentors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avatar TEXT,
            name TEXT NOT NULL,
            title TEXT,
            field TEXT,
            introduction TEXT,
            services TEXT,
            contact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 实践机会表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            color TEXT,
            title TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 测评题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            dimension TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 测评结果表（用于存储兴趣测评结果）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT DEFAULT 'guest',
            dimension_scores TEXT NOT NULL,
            recommendation TEXT,
            raw_answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 报告记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            type TEXT,
            format TEXT,
            content TEXT,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # ========== 岗位画像相关表 ==========
    # 岗位分类表（存储10+个岗位大类）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT,
            description TEXT,
            skills TEXT,
            certificates TEXT,
            soft_abilities TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
        # ========== 个人中心相关表 ==========
    # 用户头像字段（如果未添加）
    cursor.execute("PRAGMA table_info(users)")
    users_cols = [row['name'] for row in cursor.fetchall()]
    if 'avatar' not in users_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT")

    # 浏览历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_browse_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_id INTEGER,
            title TEXT,
            cover TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 岗位标签表（细分技能）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            frequency REAL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES job_categories(id) ON DELETE CASCADE
        )
    ''')

    # 在 job 表中增加 category_id 字段
    cursor.execute("PRAGMA table_info(job)")
    cols = [row['name'] for row in cursor.fetchall()]
    if 'category_id' not in cols:
        cursor.execute("ALTER TABLE job ADD COLUMN category_id INTEGER REFERENCES job_categories(id)")

    # 岗位关联图谱表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_job TEXT NOT NULL,
            to_job TEXT NOT NULL,
            relation_type TEXT CHECK(relation_type IN ('promotion', 'transition')),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 插入基础兴趣选项（系统通用数据，保留）
    cursor.execute("SELECT count(*) as cnt FROM interests")
    if cursor.fetchone()['cnt'] == 0:
        cursor.executemany('INSERT INTO interests (name, sort_order) VALUES (?, ?)', [
            ('技术研发', 1), ('产品设计', 2), ('市场营销', 3), ('运营管理', 4),
            ('教育培训', 5), ('金融投资', 6), ('行政办公', 7), ('创业管理', 8)
        ])

    # 插入基础能力维度
    cursor.execute("SELECT count(*) as cnt FROM ability_dimensions")
    if cursor.fetchone()['cnt'] == 0:
        cursor.executemany('INSERT INTO ability_dimensions (name, code, sort_order) VALUES (?, ?, ?)', [
            ('沟通能力', 'communication', 1),
            ('学习能力', 'learning', 2),
            ('团队协作', 'teamwork', 3),
            ('专业技能', 'professional', 4),
            ('创新能力', 'innovation', 5)
        ])

    # Drop legacy tables that may be created by historical init blocks above.
    # This keeps startup idempotent after the Tianchi data rebuild.
    try:
        from services.db_cleanup import DROP_TABLES, LEGACY_UNUSED_TABLES
        for table in sorted(LEGACY_UNUSED_TABLES | DROP_TABLES):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
    except Exception as e:
        print(f"legacy table cleanup skipped: {e}")

    conn.commit()
    conn.close()
    print("数据库初始化完成，文件位置：", SQLITE_DB_PATH)

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
