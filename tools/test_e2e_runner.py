import asyncio
import httpx
import json
import uuid
import sys
import subprocess
import time
import socket

SERVICES = [
    ("intake-agent", "agents/intake_agent", 8000),
    ("kyc-agent", "agents/kyc_agent", 8001),
    ("dec-agent", "agents/decisioning_agent", 8002),
    ("disburse-agent", "agents/disbursment_agent", 8003),
    ("orchestrator", "orchestrator", 8004),
]

def wait_for_port(port: int, host: str = 'localhost', timeout: float = 60.0) -> bool:
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(1)
            if time.time() - start_time >= timeout:
                return False

async def run_e2e():
    processes = []
    print("🚀 Starting all agents in background...")
    for name, path, port in SERVICES:
        print(f"Starting {name} on port {port}...")
        p = subprocess.Popen(
            ["poetry", "run", "dev"],
            cwd=path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        processes.append((name, p))
    
    print("⏳ Waiting for all ports to be ready (up to 30s)...")
    for name, path, port in SERVICES:
        if not wait_for_port(port):
            print(f"❌ Error: {name} failed to start on port {port}")
            for n, p in processes: p.terminate()
            sys.exit(1)
    print("✅ All services started successfully.\n")

    application_id = str(uuid.uuid4())
    payload = {
        "raw_application": {
            "request_id": str(uuid.uuid4()),
            "callback_url": "https://example.com/callback",
            "loan_type": "personal",
            "credit_type": "individual",
            "loan_purpose": "debt_consolidation",
            "requested_amount": 50000.0,
            "requested_term_months": 36,
            "preferred_payment_day": 1,
            "origination_channel": "web",
            "applicants": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "date_of_birth": "1980-01-01",
                    "ssn_no": "000000000",
                    "email": "john.doe@example.com",
                    "phone_number": "555-0100",
                    "addresses": [
                        {
                            "address_type": "current",
                            "address_line1": "123 Main St",
                            "city": "Springfield",
                            "state": "IL",
                            "zip_code": "62701"
                        }
                    ],
                    "incomes": [
                        {
                            "monthly_amount": 12000.0,
                            "income_type": "base_salary"
                        }
                    ]
                }
            ]
        }
    }

    print(f"➡️ Triggering pipeline for {application_id}...")
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post("http://localhost:8004/trigger_pipeline", json=payload)
            resp.raise_for_status()
            data = resp.json()
            print("\n✔️ Pipeline execution complete. Output:")
            print(json.dumps(data, indent=2))
            
            # Simple assertion
            status = data.get("status")
            if status not in ["AWAITING_APPROVAL_CONFIRMATION", "COUNTER_OFFER_PENDING", "REJECTED_AT_KYC", "DECLINED"]:
                print(f"❌ Unexpected status: {status}")
                sys.exit(1)
            else:
                print(f"✨ Test passed: Status is {status}")
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        sys.exit(1)
    finally:
        print("\n🛑 Stopping all services...")
        for name, p in processes:
            p.terminate()
            p.wait()

if __name__ == "__main__":
    asyncio.run(run_e2e())
