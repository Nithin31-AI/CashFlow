from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.members import router as members_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.imports import router as imports_router
from app.api.v1.audit import router as audit_router

# Stage 2 Routers
from app.api.v1.financial import router as financial_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.reconciliation import router as reconciliation_router
from app.api.v1.forecasting import router as forecasting_router
from app.api.v1.currencies import router as currencies_router

# Stage 3 Routers
from app.api.v1.simulations import router as simulations_router
from app.api.v1.decisions import router as decisions_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.assistant import router as assistant_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(businesses_router, prefix="/businesses", tags=["Businesses"])
api_router.include_router(members_router, prefix="/businesses", tags=["Memberships"])
api_router.include_router(accounts_router, prefix="/businesses", tags=["Financial Accounts"])
api_router.include_router(uploads_router, prefix="/businesses", tags=["File Uploads"])
api_router.include_router(imports_router, prefix="/businesses", tags=["Imports"])
api_router.include_router(audit_router, prefix="/businesses", tags=["Audit Logs"])

# Stage 2 Route Inclusions
api_router.include_router(financial_router, prefix="/businesses", tags=["Financial Overview"])
api_router.include_router(transactions_router, prefix="/businesses", tags=["Transactions"])
api_router.include_router(invoices_router, prefix="/businesses", tags=["Invoices & Payments"])
api_router.include_router(reconciliation_router, prefix="/businesses", tags=["Reconciliation"])
api_router.include_router(forecasting_router, prefix="/businesses", tags=["Forecasting & Risk"])
api_router.include_router(currencies_router, prefix="/businesses", tags=["Currencies"])

# Stage 3 Route Inclusions
api_router.include_router(simulations_router, prefix="/businesses", tags=["Monte Carlo Simulations"])
api_router.include_router(decisions_router, prefix="/businesses", tags=["Decisions & Scenarios"])
api_router.include_router(alerts_router, prefix="/businesses", tags=["Financial Alerts"])
api_router.include_router(assistant_router, prefix="/businesses", tags=["Conversational Assistant"])
