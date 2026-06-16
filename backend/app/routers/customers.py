from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity
from app.models.conversation import Conversation
from app.models.message import Message

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("")
async def list_customers(
    search: Optional[str] = None,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Customer).filter(Customer.is_merged == False)
    if search:
        query = query.filter(
            Customer.display_name.ilike(f"%{search}%")
        )
    customers = query.limit(10).all()
    return [
        {
            "id": c.id,
            "display_name": c.display_name,
            "platform": c.platform,
            "platform_user_id": c.platform_user_id,
        }
        for c in customers
    ]

@router.get("/{customer_id}")
async def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Find all linked customers
    identities = db.query(CustomerIdentity).filter(
        (CustomerIdentity.master_customer_id == customer_id) | 
        (CustomerIdentity.linked_customer_id == customer_id)
    ).all()
    
    linked_customers = []
    master_id = customer_id
    
    if customer.is_merged and customer.merged_into_id:
        master_id = customer.merged_into_id
        
    all_identities = db.query(CustomerIdentity).filter(
        CustomerIdentity.master_customer_id == master_id
    ).all()
    
    # Collect all related IDs
    related_ids = [master_id] + [i.linked_customer_id for i in all_identities]
    # Unique IDs
    related_ids = list(set(related_ids))
    
    related_customers = db.query(Customer).filter(Customer.id.in_(related_ids)).all()
    
    platforms = list(set([c.platform for c in related_customers]))
    
    master_customer = next((c for c in related_customers if c.id == master_id), customer)
    
    return {
        "id": master_customer.id,
        "display_name": master_customer.display_name,
        "phone": master_customer.phone,
        "email": master_customer.email,
        "avatar_url": master_customer.avatar_url,
        "notes": master_customer.notes,
        "platforms": platforms,
        "linked_accounts": [
            {
                "id": c.id,
                "platform": c.platform,
                "display_name": c.display_name
            } for c in related_customers if c.id != master_customer.id
        ]
    }

class CreateAndLinkRequest(BaseModel):
    display_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    token: Optional[str] = None

@router.post("/{customer_id}/create_and_link")
async def create_and_link_customer(customer_id: int, req: CreateAndLinkRequest, db: Session = Depends(get_db)):
    # 1. Find the current customer (usually a social platform customer)
    current_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not current_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # If the current customer is already merged, we attach to its master
    if current_customer.is_merged:
        current_customer = db.query(Customer).filter(Customer.id == current_customer.merged_into_id).first()

    # 2. Create the new manual customer. We will make this the new MASTER.
    new_master = Customer(
        business_id=current_customer.business_id,
        platform="manual",
        platform_user_id=f"manual_{datetime.now().timestamp()}",
        display_name=req.display_name,
        phone=req.phone,
        email=req.email,
        is_merged=False
    )
    db.add(new_master)
    db.flush() # get new_master.id
    
    # 3. Create identity link
    identity = CustomerIdentity(
        business_id=current_customer.business_id,
        master_customer_id=new_master.id,
        linked_customer_id=current_customer.id
    )
    db.add(identity)
    
    # 4. Mark current customer as merged into the new manual customer
    current_customer.is_merged = True
    current_customer.merged_into_id = new_master.id
    
    db.commit()
    return {"status": "success", "new_master_id": new_master.id}

class LinkRequest(BaseModel):
    link_to_customer_id: Optional[int] = None
    linked_customer_id: Optional[int] = None  # alias used by frontend
    token: Optional[str] = None

@router.post("/{customer_id}/link")
async def link_customer(customer_id: int, req: LinkRequest, db: Session = Depends(get_db)):
    # Support both field names
    target_id = req.linked_customer_id or req.link_to_customer_id
    if not target_id:
        raise HTTPException(status_code=400, detail="linked_customer_id is required")

    customer1 = db.query(Customer).filter(Customer.id == customer_id).first()
    customer2 = db.query(Customer).filter(Customer.id == target_id).first()
    
    if not customer1 or not customer2:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # We make customer1 the master if it isn't already merged
    master = customer1
    merged = customer2
    
    if customer1.is_merged:
        master = db.query(Customer).filter(Customer.id == customer1.merged_into_id).first()
        
    if master.id == merged.id:
        return {"status": "already linked"}
        
    # Create identity link
    identity = CustomerIdentity(
        business_id=master.business_id,
        master_customer_id=master.id,
        linked_customer_id=merged.id
    )
    db.add(identity)
    
    # Mark as merged
    merged.is_merged = True
    merged.merged_into_id = master.id
    
    db.commit()
    return {"status": "success"}

class NoteRequest(BaseModel):
    note: str

@router.post("/{customer_id}/notes")
async def update_notes(customer_id: int, req: NoteRequest, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    customer.notes = req.note
    db.commit()
    return {"status": "success"}

@router.get("/{customer_id}/conversations")
async def get_customer_conversations(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    master_id = customer.merged_into_id if customer.is_merged else customer.id
    
    all_identities = db.query(CustomerIdentity).filter(
        CustomerIdentity.master_customer_id == master_id
    ).all()
    
    related_ids = [master_id] + [i.linked_customer_id for i in all_identities]
    
    conversations = db.query(Conversation).filter(
        Conversation.customer_id.in_(related_ids)
    ).order_by(Conversation.created_at.desc()).all()
    
    result = []
    for conv in conversations:
        conv_cust = db.query(Customer).filter(Customer.id == conv.customer_id).first()
        last_message = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.timestamp.desc()).first()
        
        result.append({
            "id": conv.id,
            "platform": conv_cust.platform if conv_cust else "unknown",
            "status": conv.status,
            "last_message": last_message.content if last_message else "",
            "time": last_message.timestamp if last_message else conv.created_at
        })
        
    return result
