"""
Setup test data for Phase D testing.
Ingests sample documents from multiple domains.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.graph import run_extraction
from src.storage.qdrant_manager import get_qdrant_manager

print("=" * 70)
print("SETUP: Ingesting Test Documents for Phase D")
print("=" * 70)

# Medical document
medical_doc = """
HYPERTENSION CLINICAL REFERENCE

Overview
Hypertension (high blood pressure) is a cardiovascular condition affecting millions.

Pathophysiology
- Increased systemic vascular resistance
- Arterial wall thickening (atherosclerosis)
- Risk factor for myocardial infarction and stroke

Symptoms
- Often asymptomatic ("silent killer")
- Headaches
- Dizziness
- Shortness of breath

Diagnosis
- Blood pressure monitoring (>140/90 mmHg)
- ECG
- Laboratory tests (cholesterol, kidney function)

Treatment
- Pharmacological: ACE inhibitors, beta blockers, diuretics
- Lifestyle: Diet, exercise, stress management
"""

# HR document about sick leave
hr_doc = """
SICK LEAVE POLICY

Effective Date: January 1, 2025
Version: 2.0
Department: Human Resources

Purpose
This policy establishes guidelines for sick leave for all employees.

Eligibility
All full-time and part-time employees are eligible for sick leave from their first day.

Sick Leave Entitlement
- Full-time employees: 10 days per year
- Part-time employees: Pro-rated based on hours

Using Sick Leave
Sick leave may be used for:
- Personal illness or injury
- Medical appointments
- Care for immediate family members
- Mental health days

Notification Requirements
- Notify manager as soon as possible
- For absences over 3 days, medical documentation may be required

Serious Illnesses
For chronic conditions (diabetes, hypertension, cancer), employees should work with HR
for reasonable accommodations and extended leave options.
"""

# Engineering document
engineering_doc = """
KUBERNETES DEPLOYMENT GUIDE

Version: 3.1
Team: Platform Engineering

Overview
This guide covers deploying applications to our production Kubernetes cluster.

Prerequisites
- kubectl configured
- Access to container registry
- Deployment manifest ready

Deployment Process
1. Build container image
2. Push to registry
3. Apply Kubernetes manifests
4. Verify deployment
5. Monitor with Datadog

Configuration
All deployments must include:
- Resource limits (CPU/memory)
- Health checks (liveness/readiness probes)
- Environment variables from ConfigMaps
- Secrets from Vault

Scaling
- Use Horizontal Pod Autoscaler (HPA)
- Set min/max replicas
- Configure metrics for scaling triggers
"""

# Finance document
finance_doc = """
EXPENSE REIMBURSEMENT PROCEDURE

Effective Date: January 1, 2025
Version: 1.5
Department: Finance

Purpose
This procedure outlines how employees submit and receive reimbursement for business expenses.

Eligible Expenses
- Travel (airfare, hotels, ground transportation)
- Meals during business travel
- Office supplies
- Professional development (courses, conferences)

Submission Process
1. Log into expense system at expenses.company.com
2. Create new expense report
3. Upload receipts (required for expenses over $25)
4. Select expense category
5. Add business justification
6. Submit to manager for approval

Approval Workflow
- Manager reviews and approves
- Finance team processes
- Reimbursement via direct deposit within 5 business days

Budget Considerations
All expenses must be within approved budget limits.
Contact Finance if expense exceeds department budget.
"""

print("\n1. Ingesting Medical document...")
result1 = run_extraction(
    document_id="medical_hypertension",
    document_text=medical_doc,
    filename="hypertension_reference.txt",
)
print(f"   Status: {result1['status']}")
if result1['status'] == 'completed':
    print(f"   Domain: {result1.get('doc_metadata', {}).get('domain')}")
    print(f"   Topics: {result1.get('doc_metadata', {}).get('topics', [])[:3]}")
    print(f"   Chunks created: {len(result1.get('chunks', []))}")
    
    # Store chunks
    from src.storage.qdrant_manager import get_qdrant_manager
    qdrant = get_qdrant_manager()
    qdrant.add_chunks(result1['chunks'], 'medical_hypertension')
    print(f"   ✅ Chunks stored in Qdrant")
else:
    print(f"   ❌ Error: {result1.get('error')}")

print("\n2. Ingesting HR document...")
result2 = run_extraction(
    document_id="hr_sick_leave",
    document_text=hr_doc,
    filename="sick_leave_policy.txt",
)
print(f"   Status: {result2['status']}")
if result2['status'] == 'completed':
    print(f"   Domain: {result2.get('doc_metadata', {}).get('domain')}")
    print(f"   Topics: {result2.get('doc_metadata', {}).get('topics', [])[:3]}")
    print(f"   Chunks created: {len(result2.get('chunks', []))}")
    
    qdrant = get_qdrant_manager()
    qdrant.add_chunks(result2['chunks'], 'hr_sick_leave')
    print(f"   ✅ Chunks stored in Qdrant")
else:
    print(f"   ❌ Error: {result2.get('error')}")

print("\n3. Ingesting Engineering document...")
result3 = run_extraction(
    document_id="eng_kubernetes",
    document_text=engineering_doc,
    filename="kubernetes_guide.txt",
)
print(f"   Status: {result3['status']}")
if result3['status'] == 'completed':
    print(f"   Domain: {result3.get('doc_metadata', {}).get('domain')}")
    print(f"   Topics: {result3.get('doc_metadata', {}).get('topics', [])[:3]}")
    print(f"   Chunks created: {len(result3.get('chunks', []))}")
    
    qdrant = get_qdrant_manager()
    qdrant.add_chunks(result3['chunks'], 'eng_kubernetes')
    print(f"   ✅ Chunks stored in Qdrant")
else:
    print(f"   ❌ Error: {result3.get('error')}")

print("\n4. Ingesting Finance document...")
result4 = run_extraction(
    document_id="finance_expenses",
    document_text=finance_doc,
    filename="expense_reimbursement.txt",
)
print(f"   Status: {result4['status']}")
if result4['status'] == 'completed':
    print(f"   Domain: {result4.get('doc_metadata', {}).get('domain')}")
    print(f"   Topics: {result4.get('doc_metadata', {}).get('topics', [])[:3]}")
    print(f"   Chunks created: {len(result4.get('chunks', []))}")
    
    qdrant = get_qdrant_manager()
    qdrant.add_chunks(result4['chunks'], 'finance_expenses')
    print(f"   ✅ Chunks stored in Qdrant")
else:
    print(f"   ❌ Error: {result4.get('error')}")