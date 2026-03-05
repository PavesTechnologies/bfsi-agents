from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.db_session import get_db
from src.services.kyc_services.vendor_callback_service import VendorCallbackService

router = APIRouter(prefix="/vendor", tags=["Vendor_Callbacks"])


@router.post("/callback")
async def vendor_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.json()
    headers = request.headers

    service = VendorCallbackService(db)

    try:
        return await service.handle_callback(payload, headers)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))