import requests

BASE_URL = 'http://localhost:8000/api/v1'
acme_id = '11111111-1111-1111-1111-111111111111'

# 1. Login as Alice Owner
r_login = requests.post(f'{BASE_URL}/auth/login', json={'email': 'owner@acme.com', 'password': 'Password123!'})
assert r_login.status_code == 200, f"Login failed: {r_login.text}"
token = r_login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("[+] Logged in successfully as Alice Owner (owner@acme.com)")

# 2. Financial Overview
r_fin = requests.get(f'{BASE_URL}/businesses/{acme_id}/financial/overview', headers=headers)
print('Financial Overview Status:', r_fin.status_code)
fin = r_fin.json()
print('  * Total Liquid Cash: INR', f"{float(fin['actual_cash_balance']):,.2f}", fin['reporting_currency'])
print('  * Overdue Receivables: INR', f"{float(fin['overdue_receivables']):,.2f}")
print('  * Total Operating Revenue: INR', f"{float(fin['total_revenue']):,.2f}")
print('  * Total Operating Expenses: INR', f"{float(fin['total_expenses']):,.2f}")
print('  * Net Operating Income: INR', f"{float(fin['net_income']):,.2f}")
print('  * Accounts:')
for a in fin['accounts']:
    print(f"    - {a['account_name']}: INR {float(a['current_balance']):,.2f}")

# 3. Invoices
r_inv = requests.get(f'{BASE_URL}/businesses/{acme_id}/invoices', headers=headers)
print('\nInvoices Status:', r_inv.status_code, 'Count:', len(r_inv.json()))
for inv in r_inv.json():
    print(f"  * {inv['invoice_number']} | {inv['customer_name']} | INR {float(inv['total_amount']):,.2f} | [{inv['status']}]")

# 4. Alerts
r_alerts = requests.get(f'{BASE_URL}/businesses/{acme_id}/alerts/events', headers=headers)
print('\nAlerts Status:', r_alerts.status_code, 'Count:', len(r_alerts.json()))
for al in r_alerts.json():
    print(f"  * [{al['severity']}] {al['title']}: {al['message']}")

# 5. Forecasting
r_fc = requests.get(f'{BASE_URL}/businesses/{acme_id}/forecasts?horizon_days=30', headers=headers)
print('\nLatest 30d Forecast Status:', r_fc.status_code)
if r_fc.status_code == 200:
    fc = r_fc.json()
    print(f"  * Starting Cash: INR {float(fc.get('starting_cash', 0)):,.2f} | Ending Cash: INR {float(fc.get('ending_cash', 0)):,.2f} | Net change: INR {float(fc.get('net_change', 0)):,.2f}")

# 6. Monte Carlo Simulation
r_mc = requests.get(f'{BASE_URL}/businesses/{acme_id}/simulations/latest?horizon_days=30', headers=headers)
print('\nLatest Simulation Status:', r_mc.status_code)
if r_mc.status_code == 200:
    mc = r_mc.json()
    print(f"  * P50 Ending Cash: INR {float(mc.get('p50_ending_cash', 0)):,.2f} | Breach Probability: {float(mc.get('reserve_breach_probability', 0))*100:.1f}%")

# 7. Conversational AI Assistant grounded query
r_chat = requests.post(
    f'{BASE_URL}/businesses/{acme_id}/assistant/query',
    headers=headers,
    json={"query": "What is our current actual cash balance and do we have any overdue invoices?"}
)
print('\nConversational Assistant Status:', r_chat.status_code)
if r_chat.status_code == 200:
    chat = r_chat.json()
    print('  * Assistant Answer:\n', chat.get('answer'))
    print('  * Evidence Citations:', [e.get('source') for e in chat.get('evidence', [])])
