from fastapi import FastAPI
from real_estate_backend.customers.router import router as customers_router
from real_estate_backend.properties.router import router as properties_router
from real_estate_backend.leads.router import router as leads_router

app = FastAPI(title="Real Estate Backend")

app.include_router(customers_router)
app.include_router(properties_router)
app.include_router(leads_router)


@app.get("/")
def root():
    return {"message": "Real Estate API is running"}