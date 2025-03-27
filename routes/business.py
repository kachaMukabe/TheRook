from fastapi import APIRouter
from config import get_store
from models.business import Business

router = APIRouter(prefix="/businesses", tags=["Businesses"])


@router.post("/")
def register_business(business: Business):
    with get_store() as session:
        business.Id = f"businesses/{business.name.lower().replace(' ', '_')}"
        session.store(business, business.Id)
        session.save_changes()
    return {"message": "Business registered", "business_id": business.Id}
