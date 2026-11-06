import re

from repository.evaluation.models import DiagnosisEvaluation


class DiagnosisEvaluator:

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def evaluate_case(self, case, actual_diagnosis):

        messages = [
            {
                "role": "user",
                "content": f"""
Compare the expected diagnosis with the actual diagnosis.

Case ID: {case.case_id}

Expected Diagnosis:
{case.expected_diagnosis}

Actual Diagnosis:
{actual_diagnosis}

Score the actual diagnosis from 0.0 to 1.0.

0.0 = completely incorrect
0.5 = partially correct
1.0 = fully correct

Return only the numeric score.
""",
            }
        ]

        response = self.llm_client.invoke(messages)

        # FIX D: LLMs often return "0.7 — partially correct" instead of
        # just "0.7". Extract the first float from whatever is returned
        # instead of crashing with ValueError on float(non_numeric_string).
        raw = str(response).strip()
        match = re.search(r"[-+]?\d*\.?\d+", raw)
        if match:
            score = float(match.group())
            score = max(0.0, min(1.0, score))   # clamp to [0.0, 1.0]
        else:
            score = 0.0

        return DiagnosisEvaluation(
            case_id=case.case_id,
            expected_diagnosis=case.expected_diagnosis,
            actual_diagnosis=actual_diagnosis,
            score=score,
        )