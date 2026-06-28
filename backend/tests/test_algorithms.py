from backend.deprecated.algorithms import compute_match_score, recommend_jobs, score_student_competitiveness

# 简单单元测试
if __name__ == '__main__':
    student = {'skills': ['python', 'sql'], 'interests': ['数据分析'], 'competitiveness': 70}
    job = {'job_name': '数据分析师', 'skills': ['python', 'pandas'], 'industry': '软件', 'soft_abilities': {'communication':80}}
    score = compute_match_score(student, job)
    print('score', score)
    recs = recommend_jobs(student, [job], top_n=1)
    print('recs', recs)
    print('competitiveness', score_student_competitiveness(student))
