"""
CarPool PoC API routes
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.carpool import CarpoolRequest, CarpoolResponse
from app.services.carpool import calculate

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


@router.post("/carpool", response_model=CarpoolResponse)
async def calculate_carpool(cluster_request: CarpoolRequest):
    try:
        # print(cluster_request)
        response = await calculate(cluster_request)

        return response

    except Exception as e:
        return handle_error(e)
