import json
import os
import sys
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("LLM_PROVIDER", "local")

from backend.app import app
from backend.db import get_db


class MatchEndpointTests(unittest.TestCase):
    def setUp(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM match_history WHERE student_id = ?", (900001,))
        cur.execute("DELETE FROM student WHERE id = ?", (900001,))
        cur.execute("DELETE FROM job_profile WHERE job_name = ?", ("Python Backend Engineer",))
        cur.execute("DELETE FROM job WHERE id = ?", (900001,))
        cur.execute(
            """
            INSERT INTO student
            (id, user_id, name, major, grade, skills, certificates, soft_abilities, internships)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                900001,
                900001,
                "Student A",
                "Computer Science",
                "Senior",
                json.dumps(["Python", "SQL"]),
                json.dumps(["CET-6"]),
                json.dumps({"communication": {"score": 4}}),
                "backend internship",
            ),
        )
        cur.execute(
            "INSERT INTO job (id, job_name, company, job_description) VALUES (?, ?, ?, ?)",
            (900001, "Python Backend Engineer", "Starway", "Python Flask SQL API development"),
        )
        cur.execute(
            """
            INSERT INTO job_profile (job_name, skills, certificates, soft_abilities)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Python Backend Engineer",
                json.dumps(["Python", "Flask", "SQL"]),
                json.dumps(["CET-6"]),
                json.dumps({"communication": {"score": 4}}),
            ),
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM match_history WHERE student_id = ?", (900001,))
            cur.execute("DELETE FROM student WHERE id = ?", (900001,))
            cur.execute("DELETE FROM job_profile WHERE job_name = ?", ("Python Backend Engineer",))
            cur.execute("DELETE FROM job WHERE id = ?", (900001,))
            conn.commit()
        finally:
            conn.close()

    def test_recommend_and_match_detail(self):
        with app.test_client() as client:
            recommend = client.get("/api/match/recommend", query_string={"student_id": 900001, "limit": 5})
            self.assertEqual(recommend.status_code, 200, recommend.get_data(as_text=True))
            rec_data = recommend.get_json()
            self.assertIn("results", rec_data)
            self.assertTrue(rec_data["results"])

            detail = client.post("/api/match/match", json={
                "student_id": 900001,
                "job_name": "Python Backend Engineer",
            })
            self.assertEqual(detail.status_code, 200, detail.get_data(as_text=True))
            detail_data = detail.get_json()
            self.assertIn("overall_score", detail_data)
            self.assertIn("gap_analysis", detail_data)


if __name__ == "__main__":
    unittest.main()

