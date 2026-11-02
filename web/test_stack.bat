@echo off
REM Test full stack through frontend proxy

REM Login and get token
for /f "tokens=*" %%i in ('curl -s -X POST "http://localhost:5173/api/auth/login" -H "Content-Type: application/json" -d @%~dp0login_test.json') do set LOGIN_RESP=%%i

REM Extract token using powershell
for /f %%i in ('powershell -Command "('%LOGIN_RESP%' | ConvertFrom-Json).access_token"') do set TOKEN=%%i

echo === Full Stack Test (via Vite proxy :5173 -> FastAPI :8001) ===
echo.

REM Test endpoints
for %%e in (/api/auth/me /api/inventory/products /api/crm/customers /api/sales /api/purchases /api/hr/employees /api/accounting/accounts /api/projects /api/payments/banks /api/settings/users) do (
    curl -s -o NUL -w "%%e : %%{http_code}\n" -H "Authorization: Bearer %TOKEN%" "http://localhost:5173%%e" --max-time 10
)

echo.
echo === All tests done ===
