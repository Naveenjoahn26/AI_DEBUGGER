"""Evaluation metrics API."""

from fastapi import APIRouter, status

from app.schemas.evaluation import EvaluationSummaryResponse
from app.services.evaluation_service import get_evaluation_summary

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get(
    "/summary",
    response_model=EvaluationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieval evaluation summary",
    description=(
        "Returns real measured retrieval metrics comparing BM25 baseline "
        "against hybrid retrieval on the sample evaluation fixture."
    ),
)
def evaluation_summary() -> EvaluationSummaryResponse:
    return get_evaluation_summary()
