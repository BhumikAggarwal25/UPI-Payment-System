from fastapi import FastAPI
import redis
import uuid
import random

app=FastAPI()

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.get("/")
def home():
    return {"message":"UPI Payment Sysytem Running"}

@app.post("/pay")
def make_payment(sender:str, receiver:str, amount:float, idempotency_key:str):

    existing=r.get(f"idem:{idempotency_key}")
    if existing:
        return {
            "message":"Duplicate requested detected- not charged again",
            "payment_id": existing,
            "status":"ALREADY_PROCESSED"

        }
    # new payment -create id 
    payment_id=str(uuid.uuid4())

    # save idempotency key in redis
    r.setex(f"idem:{idempotency_key}",86400,payment_id)

    r.hset(f"payment:{payment_id}", mapping={
        "sender":sender,
        "receiver":receiver,
        "amount":amount,
        "status":"STARTED"
    })
    
    
    return {
        "payment_id":payment_id,
        "status":"STARTED",
        "message":f"Payment of ₹{amount} initiated"
    }

@app.get("/payment/{payment_id}")
def get_payment(payment_id:str):
    payment=r.hgetall(f"payment:{payment_id}")

    if payment:
        return payment
    return {"error":"Payment not found"}


@app.post("/bank/deduct")
def bank_deduct(payment_id:str, amount:float):
# random bank crash
    if random.random() < 0.3:
         raise Exception("Bank Server Crashed")

# Success - update payment status
    r.hset(f"payment:{payment_id}", mapping={
    "status":"CHARGED"
})

    return {"status":"CHARGED","message":f"Rs.{amount} deducted from bank"}


@app.post("/pay/process/{payment_id}")
def process_payment(payment_id:str):

    payment=r.hgetall(f"payment:{payment_id}")
    if not payment:
        return {"error":"Payment not found"}
    
    current_status = payment.get("status")
    if current_status in ["CONFIRMED", "REFUNDED", "FAILED"]:
        return {
            "message": "Payment already processed — cannot process again",
            "status": current_status
        }
    
    amount=payment["amount"]

    # step-1 charge bank
    try:
        if random.random()<0.3:
            raise Exception("Bank Crashed")
        
        r.hset(f"payment:{payment_id}", mapping={"status":"CHARGED"})
        print(f"Step 1 done-Rs.{amount} charged")

    except Exception as e:
        r.hset(f"payment:{payment_id}", mapping={"status":"FAILED"})
        return {"status":"FAILED","message":"Bank failed-nothing charged"}
    # step 2- confirm booking

    try:
        if random.random()<0.3:
            raise Exception("Booking system crashed") 
        r.hset(f"payment:{payment_id}",mapping={"status":"CONFIRMED"})  
        print("booking confirmed")

    except:
            # SAGA - auto refund
        r.hset(f"payment:{payment_id}",mapping={"status":"REFUNDED"})
        print("auto refunding...")
        return {"status":"REFUNDED","message":f"Booking failed- Rs.{amount} refunded automatically"}

    return {"status": "CONFIRMED","message":f"Payment done! Booking confirmed"}  
