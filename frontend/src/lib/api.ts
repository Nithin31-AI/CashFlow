// Exported central API base URL with safe fallback.
export let API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
// If not defined, fall back to local Docker address and warn during build/runtime.
if (!API_BASE) {
  // During local development (or when building without Vercel env vars) use the Docker default.
  API_BASE = "http://localhost:8000/api/v1";
  if (typeof console !== "undefined" && console.warn) {
    console.warn(
      "WARN: NEXT_PUBLIC_API_URL is not set – falling back to http://localhost:8000/api/v1. Set this variable in Vercel to point to your Render backend."
    );
  }
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Business {
  id: string;
  name: string;
  slug: string;
  currency: string;
  country: string;
  timezone: string;
  minimum_cash_reserve?: number;
  created_at: string;
  role?: string;
}

export interface Membership {
  id: string;
  business_id: string;
  user_id: string;
  role: "OWNER" | "FINANCE_MANAGER" | "ACCOUNTANT" | "VIEWER";
  created_at: string;
  user: User;
}

export interface FinancialAccount {
  id: string;
  business_id: string;
  name: string;
  account_type: "BANK" | "CREDIT_CARD" | "WALLET" | "OTHER";
  account_number_mask?: string;
  currency: string;
  institution_name?: string;
  opening_balance?: number;
  opening_balance_date?: string;
  current_balance?: number;
  total_inflows?: number;
  total_outflows?: number;
  is_active: boolean;
  created_at: string;
}

export interface FinancialOverview {
  business_id: string;
  reporting_currency: string;
  actual_cash_balance: number;
  minimum_cash_reserve: number;
  reserve_headroom: number;
  outstanding_receivables: number;
  overdue_receivables: number;
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  accounts: {
    account_id: string;
    account_name: string;
    account_type: string;
    currency: string;
    opening_balance: number;
    current_balance: number;
    total_inflows: number;
    total_outflows: number;
  }[];
}

export interface TransactionRecord {
  id: string;
  business_id: string;
  account_id: string;
  transaction_date: string;
  amount: number;
  currency: string;
  description: string;
  category: string;
  transaction_type: string;
  status: string;
  is_internal_transfer: boolean;
  reference_number?: string;
  notes?: string;
  created_at: string;
}

export interface InvoiceRecord {
  id: string;
  business_id: string;
  invoice_number: string;
  customer_name: string;
  customer_email?: string;
  issue_date: string;
  due_date: string;
  currency: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  amount_paid: number;
  status: "DRAFT" | "SENT" | "PARTIALLY_PAID" | "PAID" | "OVERDUE" | "CANCELLED";
  expected_payment_date?: string;
  predicted_delay_days: number;
  notes?: string;
  created_at: string;
  allocations?: {
    id: string;
    payment_id: string;
    allocated_amount: number;
    allocated_at: string;
  }[];
}

export interface PaymentRecord {
  id: string;
  business_id: string;
  account_id?: string;
  payment_date: string;
  amount: number;
  currency: string;
  payment_method: string;
  reference_number?: string;
  payer_name?: string;
  unallocated_amount: number;
  notes?: string;
  created_at: string;
}

export interface ReconciliationCandidate {
  reconciliation_id: string;
  transaction_id: string;
  transaction_date: string;
  transaction_amount: number;
  transaction_description: string;
  invoice_id: string;
  invoice_number: string;
  customer_name: string;
  invoice_total: number;
  unpaid_amount: number;
  matched_amount: number;
  confidence_score: number;
  match_type: "EXACT" | "PROBABLE" | "AMBIGUOUS" | "MANUAL";
  status: "PENDING_REVIEW" | "APPROVED" | "REJECTED";
  explanation: string;
}

export interface DailyProjectionPoint {
  date: string;
  projected_cash: number;
  inflow: number;
  outflow: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  forecast_id: string;
  business_id: string;
  run_date: string;
  horizon_days: number;
  currency: string;
  starting_cash: number;
  projected_inflows: number;
  projected_outflows: number;
  net_change: number;
  ending_cash: number;
  confidence_lower: number;
  confidence_upper: number;
  model_version: string;
  assumptions: Record<string, any>;
  daily_projections: DailyProjectionPoint[];
}

export interface RiskAssessmentItem {
  id: string;
  risk_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  title: string;
  description: string;
  potential_date?: string;
  estimated_shortfall?: number;
  recommended_action: string;
  status: string;
  contributing_factors?: Record<string, any>;
}

export interface ExpenseAnomalyItem {
  id: string;
  transaction_id?: string;
  description?: string;
  date?: string;
  category: string;
  amount: number;
  expected_range: string;
  anomaly_score: number;
  reason: string;
  reviewed: boolean;
}

export interface BatchFileResult {
  filename: string;
  file_size: number;
  status: "SUCCESS" | "FAILED";
  mime_type?: string;
  upload_id?: string;
  import_job_id?: string;
  error_message?: string;
}

export interface BatchUploadResponse {
  total_files: number;
  successful_count: number;
  failed_count: number;
  results: BatchFileResult[];
}

export interface UploadedFileRecord {
  id: string;
  business_id: string;
  uploader_user_id?: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  file_hash: string;
  status: "UPLOADED" | "PROCESSING" | "PROCESSED" | "FAILED";
  error_message?: string;
  created_at: string;
}

export interface ImportJobRecord {
  id: string;
  business_id: string;
  account_id?: string;
  uploaded_file_id: string;
  file_type: string;
  status: "PENDING_MAPPING" | "VALIDATING" | "READY_FOR_PREVIEW" | "APPROVED" | "FAILED";
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  created_at: string;
}

export interface ImportValidationSummary {
  job_id: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  preview_rows: any[];
  available_columns: string[];
  suggested_mappings: Record<string, string>;
  validation_errors: { row_index: number; field: string; error: string; raw_value: any }[];
}

export interface ImportedRecord {
  id: string;
  business_id: string;
  account_id?: string;
  import_job_id: string;
  row_index: number;
  transaction_date: string;
  description: string;
  reference_number?: string;
  debit?: number;
  credit?: number;
  amount: number;
  currency: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  business_id?: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  created_at: string;
}

class ApiClient {
  private getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("cashflow_token");
    }
    return null;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      if (res.status === 401 && typeof window !== "undefined") {
        localStorage.removeItem("cashflow_token");
        if (!window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/register")) {
          window.location.href = "/login";
        }
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || `Request failed with status ${res.status}`);
      }

      return res.json();
    } catch (err: any) {
      if (err.name === "TypeError" && (err.message === "Failed to fetch" || err.message?.includes("fetch"))) {
          throw new Error(`Unable to connect to the cashFlow server. Please ensure the backend is reachable at ${API_BASE}.`);
      }
      throw err;
    }
  }

  // Auth
  async register(data: { email: string; password: string; full_name: string }): Promise<User> {
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async login(credentials: { email?: string; password?: string } | FormData): Promise<{ access_token: string; token_type: string; user?: any }> {
    let body: any;
    const headers: Record<string, string> = {};
    if (credentials instanceof FormData) {
      body = credentials;
    } else {
      body = JSON.stringify({
        email: credentials.email || "",
        password: credentials.password || "",
      });
      headers["Content-Type"] = "application/json";
    }

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers,
        body,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || "Invalid login credentials");
      }

      return res.json();
    } catch (err: any) {
      if (err.name === "TypeError" && (err.message === "Failed to fetch" || err.message?.includes("fetch"))) {
        throw new Error(`Unable to connect to the cashFlow server. Please ensure the backend is running at ${API_BASE}.`);
      }
      throw err;
    }
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  async forgotPassword(email: string): Promise<{ message: string; dev_reset_token?: string }> {
    return this.request("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, new_password: string): Promise<{ message: string }> {
    return this.request("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    });
  }

  async googleAuth(credential: string): Promise<{ access_token: string; token_type: string; user: User }> {
    return this.request<{ access_token: string; token_type: string; user: User }>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential }),
    });
  }

  async getGoogleConfig(): Promise<{ client_id: string | null; enabled: boolean }> {
    return this.request<{ client_id: string | null; enabled: boolean }>("/auth/google/config");
  }

  // Businesses
  async listBusinesses(): Promise<Business[]> {
    return this.request<Business[]>("/businesses/");
  }

  async getMyBusinesses(): Promise<Business[]> {
    return this.listBusinesses();
  }

  async createBusiness(data: { name: string; currency?: string; country?: string; timezone?: string }): Promise<Business> {
    return this.request<Business>("/businesses/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getBusiness(businessId: string): Promise<Business> {
    return this.request<Business>(`/businesses/${businessId}`);
  }

  async updateBusiness(businessId: string, data: { name?: string; currency?: string; country?: string; timezone?: string }): Promise<Business> {
    return this.request<Business>(`/businesses/${businessId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Members
  async listMembers(businessId: string): Promise<Membership[]> {
    return this.request<Membership[]>(`/businesses/${businessId}/members`);
  }

  async inviteMember(
    businessId: string,
    emailOrData: string | { email: string; role: string },
    role?: string
  ): Promise<Membership> {
    const body = typeof emailOrData === "string" ? { email: emailOrData, role: role || "VIEWER" } : emailOrData;
    return this.request<Membership>(`/businesses/${businessId}/members`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async updateMemberRole(businessId: string, memberId: string, role: string): Promise<Membership> {
    return this.request<Membership>(`/businesses/${businessId}/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
  }

  async removeMember(businessId: string, memberId: string): Promise<void> {
    return this.request<void>(`/businesses/${businessId}/members/${memberId}`, {
      method: "DELETE",
    });
  }

  // Financial Accounts
  async listAccounts(businessId: string): Promise<FinancialAccount[]> {
    return this.request<FinancialAccount[]>(`/businesses/${businessId}/accounts`);
  }

  async createAccount(
    businessId: string,
    data: {
      name: string;
      account_type: string;
      currency?: string;
      opening_balance?: number;
      account_number_mask?: string;
      institution_name?: string;
    }
  ): Promise<FinancialAccount> {
    return this.request<FinancialAccount>(`/businesses/${businessId}/accounts`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Financial Engine
  async getFinancialOverview(businessId: string): Promise<FinancialOverview> {
    return this.request<FinancialOverview>(`/businesses/${businessId}/financial/overview`);
  }

  async updateMinimumReserve(businessId: string, reserve: number): Promise<any> {
    return this.request(`/businesses/${businessId}/financial/settings/reserve`, {
      method: "PATCH",
      body: JSON.stringify({ minimum_cash_reserve: reserve }),
    });
  }

  // Transactions
  async listTransactions(
    businessId: string,
    params?: { category?: string; status?: string; is_internal_transfer?: boolean; search?: string }
  ): Promise<TransactionRecord[]> {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.status) q.set("status", params.status);
    if (params?.is_internal_transfer !== undefined) q.set("is_internal_transfer", String(params.is_internal_transfer));
    if (params?.search) q.set("search", params.search);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return this.request<TransactionRecord[]>(`/businesses/${businessId}/transactions${qs}`);
  }

  async createTransaction(businessId: string, payload: any): Promise<TransactionRecord> {
    return this.request<TransactionRecord>(`/businesses/${businessId}/transactions`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async updateTransactionCategory(businessId: string, txId: string, category: string, notes?: string): Promise<TransactionRecord> {
    return this.request<TransactionRecord>(`/businesses/${businessId}/transactions/${txId}/classification`, {
      method: "PATCH",
      body: JSON.stringify({ category, notes }),
    });
  }

  // Invoices & Payments
  async listInvoices(businessId: string, status?: string): Promise<InvoiceRecord[]> {
    const qs = status ? `?status=${status}` : "";
    return this.request<InvoiceRecord[]>(`/businesses/${businessId}/invoices${qs}`);
  }

  async createInvoice(businessId: string, payload: any): Promise<InvoiceRecord> {
    return this.request<InvoiceRecord>(`/businesses/${businessId}/invoices`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listPayments(businessId: string): Promise<PaymentRecord[]> {
    return this.request<PaymentRecord[]>(`/businesses/${businessId}/payments`);
  }

  async recordPayment(businessId: string, payload: any): Promise<PaymentRecord> {
    return this.request<PaymentRecord>(`/businesses/${businessId}/payments`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  // Reconciliation
  async listReconciliationCandidates(businessId: string): Promise<ReconciliationCandidate[]> {
    return this.request<ReconciliationCandidate[]>(`/businesses/${businessId}/reconciliations/candidates`);
  }

  async approveReconciliation(businessId: string, reconciliationId: string): Promise<any> {
    return this.request(`/businesses/${businessId}/reconciliations/${reconciliationId}/approve`, {
      method: "POST",
    });
  }

  async rejectReconciliation(businessId: string, reconciliationId: string): Promise<any> {
    return this.request(`/businesses/${businessId}/reconciliations/${reconciliationId}/reject`, {
      method: "POST",
    });
  }

  // Forecasting & Risks
  async getForecast(businessId: string, horizonDays: number = 30): Promise<ForecastResponse> {
    return this.request<ForecastResponse>(`/businesses/${businessId}/forecasts?horizon_days=${horizonDays}`);
  }

  async getRisks(businessId: string, horizonDays: number = 30): Promise<RiskAssessmentItem[]> {
    return this.request<RiskAssessmentItem[]>(`/businesses/${businessId}/forecasts/risks?horizon_days=${horizonDays}`);
  }

  async getExpenseAnomalies(businessId: string): Promise<ExpenseAnomalyItem[]> {
    return this.request<ExpenseAnomalyItem[]>(`/businesses/${businessId}/forecasts/anomalies`);
  }

  async markAnomalyReviewed(businessId: string, anomalyId: string): Promise<any> {
    return this.request(`/businesses/${businessId}/forecasts/anomalies/${anomalyId}/review`, {
      method: "POST",
    });
  }

  // Uploads
  async uploadFile(businessId: string, file: File): Promise<UploadedFileRecord> {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<UploadedFileRecord>(`/businesses/${businessId}/uploads`, {
      method: "POST",
      body: formData,
    });
  }

  async uploadBatchFiles(businessId: string, files: File[]): Promise<BatchUploadResponse> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    return this.request<BatchUploadResponse>(`/businesses/${businessId}/uploads/batch`, {
      method: "POST",
      body: formData,
    });
  }

  async listUploads(businessId: string): Promise<UploadedFileRecord[]> {
    return this.request<UploadedFileRecord[]>(`/businesses/${businessId}/uploads`);
  }

  // Imports
  async startImport(businessId: string, uploadId: string): Promise<any> {
    return this.request(`/businesses/${businessId}/imports/start?upload_id=${uploadId}`, {
      method: "POST",
    });
  }

  async applyMapping(
    businessId: string,
    jobId: string,
    payload: {
      account_id?: string;
      column_mappings: Record<string, string | null>;
      date_format?: string;
    }
  ): Promise<ImportValidationSummary> {
    return this.request<ImportValidationSummary>(`/businesses/${businessId}/imports/${jobId}/mapping`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getImportPreview(businessId: string, jobId: string): Promise<ImportValidationSummary> {
    return this.request<ImportValidationSummary>(`/businesses/${businessId}/imports/${jobId}/preview`);
  }

  async confirmImport(businessId: string, jobId: string): Promise<{ success: boolean; imported_count: number; message: string }> {
    return this.request(`/businesses/${businessId}/imports/${jobId}/confirm`, {
      method: "POST",
    });
  }

  async listImportJobs(businessId: string): Promise<ImportJobRecord[]> {
    return this.request<ImportJobRecord[]>(`/businesses/${businessId}/imports`);
  }

  async listImportedRecords(businessId: string): Promise<ImportedRecord[]> {
    return this.request<ImportedRecord[]>(`/businesses/${businessId}/records`);
  }

  // Monte Carlo Simulations
  async runSimulation(
    businessId: string,
    params?: {
      horizon_days?: number;
      num_paths?: number;
      seed?: number;
      custom_delay_days?: number;
      collection_probability?: number;
      expense_volatility_multiplier?: number;
    }
  ): Promise<SimulationRun> {
    return this.request<SimulationRun>(`/businesses/${businessId}/simulations/run`, {
      method: "POST",
      body: JSON.stringify(params || {}),
    });
  }

  async getLatestSimulation(businessId: string): Promise<SimulationRun> {
    return this.request<SimulationRun>(`/businesses/${businessId}/simulations/latest`);
  }

  // Goals, Scenarios & Decision Optimization
  async listGoals(businessId: string): Promise<FinancialGoal[]> {
    return this.request<FinancialGoal[]>(`/businesses/${businessId}/goals`);
  }

  async createGoal(
    businessId: string,
    data: {
      name: string;
      goal_type: string;
      target_amount: number;
      target_date?: string;
      is_hard_constraint?: boolean;
      priority?: number;
      notes?: string;
    }
  ): Promise<FinancialGoal> {
    return this.request<FinancialGoal>(`/businesses/${businessId}/goals`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listScenarios(businessId: string): Promise<SavedScenario[]> {
    return this.request<SavedScenario[]>(`/businesses/${businessId}/scenarios`);
  }

  async createScenario(
    businessId: string,
    data: {
      name: string;
      description?: string;
      receivable_delay_days?: number;
      collection_rate_pct?: number;
      expense_multiplier?: number;
      one_off_capex?: number;
    }
  ): Promise<SavedScenario> {
    return this.request<SavedScenario>(`/businesses/${businessId}/scenarios`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async runOptimisation(businessId: string, scenarioId?: string): Promise<OptimisationPlan> {
    const qs = scenarioId ? `?scenario_id=${scenarioId}` : "";
    return this.request<OptimisationPlan>(`/businesses/${businessId}/optimisation/run${qs}`, {
      method: "POST",
    });
  }

  async listRecommendations(businessId: string): Promise<FinancialRecommendation[]> {
    return this.request<FinancialRecommendation[]>(`/businesses/${businessId}/recommendations`);
  }

  async updateRecommendationStatus(
    businessId: string,
    recId: string,
    status: "ACCEPTED" | "DISMISSED"
  ): Promise<FinancialRecommendation> {
    return this.request<FinancialRecommendation>(
      `/businesses/${businessId}/recommendations/${recId}/status?status_update=${status}`,
      { method: "POST" }
    );
  }

  // Alerts
  async listAlertRules(businessId: string): Promise<AlertRule[]> {
    return this.request<AlertRule[]>(`/businesses/${businessId}/alerts/rules`);
  }

  async createAlertRule(
    businessId: string,
    data: {
      name: string;
      category: string;
      threshold_value: number;
      severity?: string;
      suppression_window_hours?: number;
      is_active?: boolean;
    }
  ): Promise<AlertRule> {
    return this.request<AlertRule>(`/businesses/${businessId}/alerts/rules`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listAlertEvents(businessId: string): Promise<AlertEvent[]> {
    return this.request<AlertEvent[]>(`/businesses/${businessId}/alerts/events`);
  }

  async evaluateAlerts(businessId: string): Promise<{ status: string; triggered_count: number; triggered_events: AlertEvent[] }> {
    return this.request(`/businesses/${businessId}/alerts/evaluate`, { method: "POST" });
  }

  async acknowledgeAlert(businessId: string, eventId: string): Promise<AlertEvent> {
    return this.request<AlertEvent>(`/businesses/${businessId}/alerts/events/${eventId}/acknowledge`, { method: "POST" });
  }

  async resolveAlert(businessId: string, eventId: string): Promise<AlertEvent> {
    return this.request<AlertEvent>(`/businesses/${businessId}/alerts/events/${eventId}/resolve`, { method: "POST" });
  }

  // Conversational AI Assistant
  async askAssistant(businessId: string, query: string): Promise<AssistantResponse> {
    return this.request<AssistantResponse>(`/businesses/${businessId}/assistant/query`, {
      method: "POST",
      body: JSON.stringify({ query }),
    });
  }

  // Audit Logs
  async getAuditLogs(businessId: string): Promise<AuditLogItem[]> {
    return this.request<AuditLogItem[]>(`/businesses/${businessId}/audit-logs`);
  }
}

export interface SimulationPercentilePoint {
  day: number;
  date: string;
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
}

export interface SimulationRun {
  id: string;
  business_id: string;
  horizon_days: number;
  num_paths: number;
  seed?: number;
  starting_cash: number;
  min_projected_cash: number;
  max_projected_cash: number;
  p10_ending_cash: number;
  p50_ending_cash: number;
  p90_ending_cash: number;
  reserve_breach_probability: number;
  expected_shortfall: number;
  potential_shortage_day?: number;
  assumptions: Record<string, any>;
  percentile_paths: SimulationPercentilePoint[];
  model_version: string;
  created_at: string;
}

export interface FinancialGoal {
  id: string;
  business_id: string;
  name: string;
  goal_type: string;
  target_amount: number;
  target_date?: string;
  is_hard_constraint: boolean;
  priority: number;
  status: string;
  notes?: string;
  created_at: string;
}

export interface SavedScenario {
  id: string;
  business_id: string;
  name: string;
  description?: string;
  is_baseline: boolean;
  parameters: Record<string, any>;
  projected_ending_cash: number;
  min_cash: number;
  shortage_risk_percent: number;
  runway_days: number;
  created_at: string;
}

export interface OptimisationPlan {
  id: string;
  business_id: string;
  scenario_id?: string;
  status: "FEASIBLE" | "INFEASIBLE" | "PARTIALLY_FEASIBLE";
  objective_value: number;
  recommended_actions: any[];
  trade_offs?: string;
  hard_constraints_satisfied: boolean;
  created_at: string;
}

export interface FinancialRecommendation {
  id: string;
  business_id: string;
  title: string;
  action_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  estimated_impact: number;
  reasoning: string;
  supporting_records?: Record<string, any>;
  assumptions?: string;
  disadvantages?: string;
  status: "ACTIVE" | "ACCEPTED" | "DISMISSED";
  created_at: string;
}

export interface AlertRule {
  id: string;
  business_id: string;
  name: string;
  category: string;
  threshold_value: number;
  severity: "INFO" | "WARNING" | "CRITICAL";
  is_active: boolean;
  suppression_window_hours: number;
  created_at: string;
}

export interface AlertEvent {
  id: string;
  business_id: string;
  rule_id?: string;
  title: string;
  message: string;
  category?: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  financial_evidence?: Record<string, any>;
  is_acknowledged: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface AssistantResponse {
  query: string;
  answer: string;
  citations: string[];
  tool_data: any[];
  assumptions_note: string;
}

export const api = new ApiClient();
