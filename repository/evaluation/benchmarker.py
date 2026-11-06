from typing import List

from repository.evaluation.models import (
    EvaluationCase,
    BenchmarkResult,
)


class BenchmarkRunner:

    def __init__(
        self,
        agent_runner,
        retrieval_evaluator,
        tool_evaluator,
        diagnosis_evaluator,
        overall_evaluator,
    ):
        self.agent_runner = agent_runner
        self.retrieval_evaluator = retrieval_evaluator
        self.tool_evaluator = tool_evaluator
        self.diagnosis_evaluator = diagnosis_evaluator
        self.overall_evaluator = overall_evaluator

    def run(self, cases: List[EvaluationCase]) -> BenchmarkResult:

        if not cases:
            return BenchmarkResult(
                total_cases=0,
                average_retrieval_score=0.0,
                average_tool_selection_score=0.0,
                average_diagnosis_score=0.0,
                average_overall_score=0.0,
            )

        retrieval_results = []
        tool_results = []
        diagnosis_results = []
        overall_results = []

        for case in cases:

            # 1. Run the actual AI debugger
            state = self.agent_runner.run(case.bug_description)

            # 2. Evaluate retrieval
            retrieval_result = (
                self.retrieval_evaluator.evaluate_case(case)
            )
            retrieval_results.append(retrieval_result)

            # 3. Evaluate tool selection using the actual AgentState
            tool_result = (
                self.tool_evaluator.evaluate_case(
                    case,
                    state,
                )
            )
            tool_results.append(tool_result)

            # 4. Extract the final diagnosis
            actual_diagnosis = self._get_final_diagnosis(state)

            # 5. Evaluate diagnosis
            diagnosis_result = (
                self.diagnosis_evaluator.evaluate_case(
                    case,
                    actual_diagnosis,
                )
            )
            diagnosis_results.append(diagnosis_result)

            # 6. Combine all scores
            overall_result = self.overall_evaluator.evaluate(
                retrieval=retrieval_result,
                tool_selection=tool_result,
                diagnosis=diagnosis_result,
            )

            overall_results.append(overall_result)

        return BenchmarkResult(
            total_cases=len(cases),
            average_retrieval_score=self._average(
                [result.score for result in retrieval_results]
            ),
            average_tool_selection_score=self._average(
                [result.score for result in tool_results]
            ),
            average_diagnosis_score=self._average(
                [result.score for result in diagnosis_results]
            ),
            average_overall_score=self._average(
                [result.overall_score for result in overall_results]
            ),
        )

    @staticmethod
    def _average(values: List[float]) -> float:

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _get_final_diagnosis(state) -> str:

        for message in reversed(state.messages):

            if (
                message.role == "assistant"
                and message.content
            ):
                return message.content

        return ""