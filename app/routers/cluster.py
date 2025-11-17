"""
Cluster PoC API routes
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.cluster import ClusterRequest, ClusterResponse
from app.services.cluster import calculate

router = APIRouter()


class OriginForbiddenError(Exception):
    """Custom exception for forbidden origins"""

    pass


def handle_error(error: Exception) -> JSONResponse:
    """Handle errors and return appropriate JSON response"""
    print(f"Error: {error}")

    if isinstance(error, OriginForbiddenError):
        return JSONResponse(
            status_code=403, content={"error": "Forbidden - Invalid origin"}
        )

    error_message = (
        str(error) if isinstance(error, Exception) else "Internal Server Error"
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "details": error_message},
    )


@router.post("/cluster", response_model=ClusterResponse)
async def calculate_cluster(cluster_request: ClusterRequest):
    try:
        # print(cluster_request)
        response = await calculate(cluster_request)

        return response

    except Exception as e:
        return handle_error(e)
