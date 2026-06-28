-- 数据库迁移脚本：为 student 表增加结构化能力画像字段
ALTER TABLE student ADD COLUMN education_json TEXT;
ALTER TABLE student ADD COLUMN work_json TEXT;
ALTER TABLE student ADD COLUMN project_json TEXT;

-- 兼容性字段（若尚未添加）
ALTER TABLE student ADD COLUMN phone TEXT;
ALTER TABLE student ADD COLUMN email TEXT;
ALTER TABLE student ADD COLUMN education_text TEXT;
ALTER TABLE student ADD COLUMN work_text TEXT;
ALTER TABLE student ADD COLUMN project_text TEXT;
ALTER TABLE student ADD COLUMN skills_certs_text TEXT;
ALTER TABLE student ADD COLUMN summary TEXT;
ALTER TABLE student ADD COLUMN interest_scores TEXT;