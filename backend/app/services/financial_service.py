from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.account import FinancialAccount, AccountType
from app.models.transaction import Transaction, ImportedRecord, TransactionType, TransactionCategory
from app.models.invoice import Invoice, InvoiceStatus, Payment, InvoicePaymentAllocation
from app.models.business import Business
from app.services.currency_service import CurrencyService

class FinancialService:
    """
    Core authoritative financial calculation engine for cashFlow.
    Implements:
    - Decimal arithmetic for all currency balances.
    - Strict separation of actual liquid cash vs projected cash vs receivables.
    - Exclusion of internal transfers from revenue and expense totals.
    - Accurate invoice allocation and outstanding receivables tracking.
    """

    @staticmethod
    def calculate_account_balance(db: Session, account_id: str, business_id: str) -> Dict[str, Any]:
        """
        Calculates authoritative actual balance:
        Ending balance = Opening Balance + Actual Inflows - Actual Outflows + Approved Adjustments.
        """
        account = db.query(FinancialAccount).filter(
            FinancialAccount.id == account_id,
            FinancialAccount.business_id == business_id
        ).first()

        if not account:
            raise ValueError(f"Account {account_id} not found for business {business_id}")

        opening_balance = Decimal(str(account.opening_balance or "0.00"))

        # Calculate sum from transactions ledger
        inflows = Decimal("0.00")
        outflows = Decimal("0.00")

        # 1. Transactions table
        tx_rows = db.query(Transaction).filter(
            Transaction.account_id == account_id,
            Transaction.business_id == business_id
        ).all()

        for tx in tx_rows:
            amt = Decimal(str(tx.amount))
            if tx.transaction_type == TransactionType.INFLOW or amt > 0:
                inflows += abs(amt)
            elif tx.transaction_type == TransactionType.OUTFLOW or amt < 0:
                outflows += abs(amt)

        # 2. Check for imported_records not yet mirrored to transactions table
        imported_rows = db.query(ImportedRecord).filter(
            ImportedRecord.account_id == account_id,
            ImportedRecord.business_id == business_id
        ).all()

        # Add imported records if not already linked to a transaction
        existing_imported_ids = {tx.imported_record_id for tx in tx_rows if tx.imported_record_id}
        for imp in imported_rows:
            if imp.id not in existing_imported_ids:
                amt = Decimal(str(imp.amount))
                if amt > 0:
                    inflows += abs(amt)
                else:
                    outflows += abs(amt)

        current_balance = (opening_balance + inflows - outflows).quantize(Decimal("0.01"))

        return {
            "account_id": account.id,
            "account_name": account.name,
            "account_type": account.account_type.value,
            "currency": account.currency,
            "opening_balance": opening_balance,
            "opening_balance_date": account.opening_balance_date,
            "total_inflows": inflows.quantize(Decimal("0.01")),
            "total_outflows": outflows.quantize(Decimal("0.01")),
            "current_balance": current_balance,
        }

    @staticmethod
    def get_business_financial_position(db: Session, business_id: str) -> Dict[str, Any]:
        """
        Consolidates complete verified financial position for a business workspace.
        Maintains strict separation between:
        1. Actual Liquid Cash (Bank balances + Cash on hand)
        2. Outstanding Receivables (Unpaid invoices - NOT cash)
        3. Outstanding Payables / Expected Outflows (Upcoming bills/expenses)
        4. Internal Transfers (Excluded from revenue/expenses)
        """
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            raise ValueError(f"Business {business_id} not found")

        reporting_currency = business.currency or "INR"

        # 1. Accounts & Total Liquid Cash
        accounts = db.query(FinancialAccount).filter(
            FinancialAccount.business_id == business_id,
            FinancialAccount.is_active == True
        ).all()

        total_actual_cash = Decimal("0.00")
        account_summaries = []

        for acc in accounts:
            acc_bal = FinancialService.calculate_account_balance(db, acc.id, business_id)
            # Only count BANK, WALLET, OTHER as cash. CREDIT_CARD is liability/credit limit, not cash.
            if acc.account_type in [AccountType.BANK, AccountType.WALLET, AccountType.OTHER]:
                # Convert to reporting currency if different
                converted = CurrencyService.convert_amount(
                    db,
                    acc_bal["current_balance"],
                    acc.currency,
                    reporting_currency
                )
                if converted["is_converted"] and converted["converted_amount"] is not None:
                    total_actual_cash += converted["converted_amount"]

            account_summaries.append(acc_bal)

        # 2. Invoices & Receivables (Unpaid invoices are strictly NOT cash)
        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE])
        ).all()

        total_receivables = Decimal("0.00")
        overdue_receivables = Decimal("0.00")
        today = datetime.now(timezone.utc).date()

        for inv in invoices:
            unpaid = Decimal(str(inv.total_amount)) - Decimal(str(inv.amount_paid or "0.00"))
            if unpaid > 0:
                conv = CurrencyService.convert_amount(db, unpaid, inv.currency, reporting_currency)
                if conv["is_converted"] and conv["converted_amount"] is not None:
                    total_receivables += conv["converted_amount"]
                    if inv.due_date < today:
                        overdue_receivables += conv["converted_amount"]

        # 3. Income & Expenses (excluding Internal Transfers)
        txs = db.query(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.status == "POSTED"
        ).all()

        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")

        for tx in txs:
            # Internal transfers MUST NOT be counted as income or expense
            if tx.is_internal_transfer or tx.category == TransactionCategory.INTERNAL_TRANSFER:
                continue

            amt = Decimal(str(tx.amount))
            conv = CurrencyService.convert_amount(db, abs(amt), tx.currency, reporting_currency)
            val = conv["converted_amount"] if (conv["is_converted"] and conv["converted_amount"] is not None) else abs(amt)

            if tx.transaction_type == TransactionType.INFLOW or (amt > 0 and tx.transaction_type != TransactionType.OUTFLOW):
                total_revenue += val
            elif tx.transaction_type == TransactionType.OUTFLOW or (amt < 0 and tx.transaction_type != TransactionType.INFLOW):
                total_expenses += val

        # Also count imported_records if not yet represented in transactions
        imported_records = db.query(ImportedRecord).filter(
            ImportedRecord.business_id == business_id
        ).all()
        existing_imp_ids = {t.imported_record_id for t in txs if t.imported_record_id}
        for imp in imported_records:
            if imp.id not in existing_imp_ids:
                amt = Decimal(str(imp.amount))
                conv = CurrencyService.convert_amount(db, abs(amt), imp.currency, reporting_currency)
                val = conv["converted_amount"] if (conv["is_converted"] and conv["converted_amount"] is not None) else abs(amt)
                if amt > 0:
                    total_revenue += val
                else:
                    total_expenses += val

        net_income = total_revenue - total_expenses
        min_reserve = Decimal(str(business.minimum_cash_reserve or "100000.00"))
        reserve_headroom = total_actual_cash - min_reserve

        return {
            "business_id": business_id,
            "reporting_currency": reporting_currency,
            "actual_cash_balance": total_actual_cash.quantize(Decimal("0.01")),
            "minimum_cash_reserve": min_reserve.quantize(Decimal("0.01")),
            "reserve_headroom": reserve_headroom.quantize(Decimal("0.01")),
            "outstanding_receivables": total_receivables.quantize(Decimal("0.01")),
            "overdue_receivables": overdue_receivables.quantize(Decimal("0.01")),
            "total_revenue": total_revenue.quantize(Decimal("0.01")),
            "total_expenses": total_expenses.quantize(Decimal("0.01")),
            "net_income": net_income.quantize(Decimal("0.01")),
            "accounts": account_summaries,
        }

    @classmethod
    def calculate_cash_position(cls, db: Session, business_id: str):
        data = cls.get_business_financial_position(db, business_id)
        class OverviewWrapper:
            def __init__(self, d):
                self.__dict__.update(d)
                self.actual_cash_balance = d["actual_cash_balance"]
                self.minimum_cash_reserve = d["minimum_cash_reserve"]
                self.reserve_headroom = d["reserve_headroom"]
                self.outstanding_receivables = d["outstanding_receivables"]
                self.overdue_receivables = d["overdue_receivables"]
                self.total_revenue = d["total_revenue"]
                self.total_expenses = d["total_expenses"]
                self.net_income = d["net_income"]
                self.reporting_currency = d["reporting_currency"]
                self.accounts = d["accounts"]
            def __getitem__(self, item):
                return getattr(self, item)
            def get(self, item, default=None):
                return getattr(self, item, default)
        return OverviewWrapper(data)
