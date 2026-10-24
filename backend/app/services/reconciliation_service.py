from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.invoice import Invoice, InvoiceStatus, Payment, InvoicePaymentAllocation
from app.models.reconciliation import ReconciliationRecord, ReconciliationStatus, MatchType, MatchedEntityType

class ReconciliationService:
    """
    Intelligent transaction-to-invoice and payment reconciliation engine.
    - Generates explainable candidate matches with clear confidence scoring.
    - Strictly prevents double allocations.
    - Requires human review and approval before mutating invoice payment statuses.
    """

    @staticmethod
    def find_candidate_matches(db: Session, business_id: str) -> List[Dict[str, Any]]:
        """
        Scans unreconciled positive inflow transactions against unpaid invoices.
        """
        unreconciled_txs = db.query(Transaction).filter(
            Transaction.business_id == business_id,
            Transaction.status != TransactionStatus.RECONCILED,
            Transaction.is_internal_transfer == False
        ).all()

        unpaid_invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE])
        ).all()

        candidates = []

        for tx in unreconciled_txs:
            tx_amount = Decimal(str(tx.amount))
            # Inflow transactions correspond to customer payments
            if tx_amount <= 0:
                continue

            for inv in unpaid_invoices:
                unpaid_amount = Decimal(str(inv.total_amount)) - Decimal(str(inv.amount_paid or "0.00"))
                if unpaid_amount <= 0:
                    continue

                score = Decimal("0.00")
                reasons = []
                match_type = MatchType.AMBIGUOUS

                # 1. Exact amount match
                amount_diff = abs(tx_amount - unpaid_amount)
                if amount_diff == Decimal("0.00"):
                    score += Decimal("50.00")
                    reasons.append("Exact monetary amount match.")
                elif tx_amount < unpaid_amount:
                    score += Decimal("30.00")
                    reasons.append(f"Possible partial payment of ₹{tx_amount} towards ₹{unpaid_amount}.")

                # 2. Reference / Invoice Number containment
                desc_lower = tx.description.lower() if tx.description else ""
                ref_lower = tx.reference_number.lower() if tx.reference_number else ""
                inv_num_lower = inv.invoice_number.lower()

                if inv_num_lower in desc_lower or (ref_lower and inv_num_lower in ref_lower):
                    score += Decimal("40.00")
                    reasons.append(f"Invoice number '{inv.invoice_number}' explicitly cited in transaction.")

                # 3. Customer name match
                cust_name_lower = inv.customer_name.lower()
                cust_tokens = [t for t in cust_name_lower.split() if len(t) > 2]
                if any(token in desc_lower for token in cust_tokens):
                    score += Decimal("25.00")
                    reasons.append(f"Customer name match ('{inv.customer_name}').")

                # 4. Date proximity
                days_diff = abs((tx.transaction_date - inv.issue_date).days)
                if days_diff <= 14:
                    score += Decimal("10.00")
                    reasons.append(f"Transaction date is within {days_diff} days of invoice.")

                if score >= Decimal("90.00"):
                    match_type = MatchType.EXACT
                elif score >= Decimal("70.00"):
                    match_type = MatchType.PROBABLE
                else:
                    match_type = MatchType.AMBIGUOUS

                if score >= Decimal("50.00"):
                    # Check if candidate record already exists
                    existing = db.query(ReconciliationRecord).filter(
                        ReconciliationRecord.transaction_id == tx.id,
                        ReconciliationRecord.matched_entity_type == MatchedEntityType.INVOICE,
                        ReconciliationRecord.matched_entity_id == inv.id
                    ).first()

                    if not existing:
                        rec = ReconciliationRecord(
                            business_id=business_id,
                            transaction_id=tx.id,
                            matched_entity_type=MatchedEntityType.INVOICE,
                            matched_entity_id=inv.id,
                            confidence_score=min(Decimal("100.00"), score),
                            match_type=match_type,
                            status=ReconciliationStatus.PENDING_REVIEW,
                            matched_amount=min(tx_amount, unpaid_amount),
                            explanation="; ".join(reasons)
                        )
                        db.add(rec)
                        db.flush()
                        existing = rec

                    candidates.append({
                        "reconciliation_id": existing.id,
                        "transaction_id": tx.id,
                        "transaction_date": tx.transaction_date,
                        "transaction_amount": tx_amount,
                        "transaction_description": tx.description,
                        "invoice_id": inv.id,
                        "invoice_number": inv.invoice_number,
                        "customer_name": inv.customer_name,
                        "invoice_total": Decimal(str(inv.total_amount)),
                        "unpaid_amount": unpaid_amount,
                        "matched_amount": existing.matched_amount,
                        "confidence_score": existing.confidence_score,
                        "match_type": existing.match_type.value,
                        "status": existing.status.value,
                        "explanation": existing.explanation,
                    })

        db.commit()
        return candidates

    @staticmethod
    def approve_reconciliation(
        db: Session,
        reconciliation_id: str,
        business_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Approves a candidate reconciliation match.
        Guarantees that an invoice or transaction cannot be double-reconciled.
        """
        rec = db.query(ReconciliationRecord).filter(
            ReconciliationRecord.id == reconciliation_id,
            ReconciliationRecord.business_id == business_id
        ).first()

        if not rec:
            raise ValueError(f"Reconciliation candidate {reconciliation_id} not found.")

        if rec.status == ReconciliationStatus.APPROVED:
            raise ValueError("Reconciliation has already been approved.")

        # Retrieve transaction
        tx = db.query(Transaction).filter(Transaction.id == rec.transaction_id).first()
        if not tx:
            raise ValueError("Associated transaction not found.")

        if tx.status == TransactionStatus.RECONCILED:
            raise ValueError("Transaction has already been reconciled with another record.")

        # If matched with Invoice
        if rec.matched_entity_type == MatchedEntityType.INVOICE:
            invoice = db.query(Invoice).filter(Invoice.id == rec.matched_entity_id).first()
            if not invoice:
                raise ValueError("Associated invoice not found.")

            allocated_amount = Decimal(str(rec.matched_amount))
            current_paid = Decimal(str(invoice.amount_paid or "0.00"))
            total_inv = Decimal(str(invoice.total_amount))

            new_paid = (current_paid + allocated_amount).quantize(Decimal("0.01"))
            if new_paid > total_inv:
                raise ValueError(f"Allocation of ₹{allocated_amount} exceeds outstanding balance of invoice.")

            invoice.amount_paid = new_paid
            if new_paid >= total_inv:
                invoice.status = InvoiceStatus.PAID
            else:
                invoice.status = InvoiceStatus.PARTIALLY_PAID

            # Create corresponding Payment record if none existed
            payment = Payment(
                business_id=business_id,
                account_id=tx.account_id,
                payment_date=tx.transaction_date,
                amount=allocated_amount,
                currency=tx.currency,
                reference_number=tx.reference_number or f"TX-{tx.id[:8]}",
                payer_name=invoice.customer_name,
                notes=f"Reconciled from transaction '{tx.description}'",
                unallocated_amount=Decimal("0.00")
            )
            db.add(payment)
            db.flush()

            # Create non-duplicative allocation record
            allocation = InvoicePaymentAllocation(
                business_id=business_id,
                invoice_id=invoice.id,
                payment_id=payment.id,
                allocated_amount=allocated_amount
            )
            db.add(allocation)

        tx.status = TransactionStatus.RECONCILED
        rec.status = ReconciliationStatus.APPROVED
        rec.reviewed_by_user_id = user_id
        rec.reviewed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "status": "APPROVED",
            "reconciliation_id": rec.id,
            "transaction_id": tx.id,
            "matched_amount": rec.matched_amount,
            "invoice_id": rec.matched_entity_id if rec.matched_entity_type == MatchedEntityType.INVOICE else None
        }

    @staticmethod
    def reject_reconciliation(
        db: Session,
        reconciliation_id: str,
        business_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        rec = db.query(ReconciliationRecord).filter(
            ReconciliationRecord.id == reconciliation_id,
            ReconciliationRecord.business_id == business_id
        ).first()

        if not rec:
            raise ValueError(f"Reconciliation candidate {reconciliation_id} not found.")

        rec.status = ReconciliationStatus.REJECTED
        rec.reviewed_by_user_id = user_id
        rec.reviewed_at = datetime.now(timezone.utc)
        db.commit()

        return {"status": "REJECTED", "reconciliation_id": rec.id}
