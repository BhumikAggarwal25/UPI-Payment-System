# Distributed UPI Payment System

## Problem
UPI payment crashes mid-transaction.
Money deducted from bank but booking 
not confirmed. User loses money.

## Solution
- Idempotency keys → prevents double charging
- Saga pattern → auto refund on partial failure
- Mock bank API → simulates random crashes

## API Endpoints
- POST /pay → initiate payment
- POST /pay/process/{id} → process with Saga
- GET /payment/{id} → check status

## Tech Stack
FastAPI, Redis, Python

## Outcomes
- CONFIRMED → payment + booking success
- FAILED → bank failed, nothing charged
- REFUNDED → booking failed, auto refunded
