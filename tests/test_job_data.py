import unittest

import pandas as pd

from job_data import (
    build_analytics,
    filter_jobs,
    find_similar_jobs,
    normalize_jobs,
    retrieve_jobs,
)


class JobDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.jobs = normalize_jobs(
            pd.DataFrame(
                [
                    {
                        "JOB TITLE": "Data Analyst",
                        "COMPANY NAME": "Northwind",
                        "INDUSTRY": "Technology",
                        "LOCATION": "Remote",
                        "SKILL CATEGORY": "Python; SQL",
                        "JOB DESCRIPTION": "Build data dashboards",
                    },
                    {
                        "JOB TITLE": "Data Scientist",
                        "COMPANY NAME": "Contoso",
                        "INDUSTRY": "Technology",
                        "LOCATION": "London",
                        "SKILL CATEGORY": "Python; Machine Learning",
                        "JOB DESCRIPTION": "Train predictive models",
                    },
                    {
                        "JOB TITLE": "Nurse",
                        "COMPANY NAME": "Health Co",
                        "INDUSTRY": "Healthcare",
                        "LOCATION": "Remote",
                        "SKILL CATEGORY": "Patient care",
                        "JOB DESCRIPTION": "Support patients",
                    },
                ]
            )
        )

    def test_normalizes_and_counts_workbook_fields(self) -> None:
        analytics = build_analytics(self.jobs)
        self.assertEqual(analytics["total_jobs"], 3)
        self.assertEqual(analytics["top_roles"][0], {"label": "Data Analyst", "count": 1})
        self.assertEqual(analytics["top_skills"][0], {"label": "Python", "count": 2})

    def test_filters_are_case_insensitive_and_composable(self) -> None:
        result = filter_jobs(
            self.jobs,
            query="dashboard",
            industry="technology",
            skill="python",
            location="remote",
        )
        self.assertEqual(result["job_id"].tolist(), ["job-0"])

    def test_similarity_excludes_the_source_job(self) -> None:
        results = find_similar_jobs(self.jobs, "job-0")
        self.assertTrue(results)
        self.assertNotIn("job-0", [result["job_id"] for result in results])
        self.assertGreater(results[0]["similarity"], 0)

    def test_retrieval_returns_only_relevant_records(self) -> None:
        results = retrieve_jobs(self.jobs, "predictive models")
        self.assertEqual([result["job_id"] for result in results], ["job-1"])


if __name__ == "__main__":
    unittest.main()
