"""
Split medical stress test document into section-based files.

This creates 10+ focused documents instead of 1 large document,
improving retrieval precision by giving each medical concept its own embedding.
"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("SPLITTING MEDICAL DOCUMENT INTO SECTIONS")
print("=" * 70)

# Load original document
medical_file = Path("data/raw/medical_rag_stress_test.txt")

with open(medical_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Create output directory
output_dir = Path("data/raw/medical_sections")
output_dir.mkdir(parents=True, exist_ok=True)

print(f"\nOriginal document: {len(content)} characters")
print(f"Output directory: {output_dir}")

# Define sections to extract
sections = {
    "01_cardiovascular_system.txt": {
        "start": "1.1 Cardiovascular System",
        "end": "1.2 Nervous System"
    },
    "02_nervous_system.txt": {
        "start": "1.2 Nervous System",
        "end": "2. Physiology and Homeostasis"
    },
    "03_cellular_metabolism.txt": {
        "start": "2.1 Cellular Metabolism",
        "end": "2.2 Endocrine Regulation"
    },
    "04_endocrine_regulation.txt": {
        "start": "2.2 Endocrine Regulation",
        "end": "3. Pathology"
    },
    "05_inflammation.txt": {
        "start": "3.1 Inflammation",
        "end": "3.2 Neoplasia"
    },
    "06_neoplasia.txt": {
        "start": "3.2 Neoplasia",
        "end": "4. Pharmacology"
    },
    "07_pharmacokinetics.txt": {
        "start": "4.1 Pharmacokinetics",
        "end": "4.2 Pharmacodynamics"
    },
    "08_pharmacodynamics.txt": {
        "start": "4.2 Pharmacodynamics",
        "end": "5. Diagnostics and Imaging"
    },
    "09_diagnostics_imaging.txt": {
        "start": "5. Diagnostics and Imaging",
        "end": "6. Infectious Diseases"
    },
    "10_infectious_diseases.txt": {
        "start": "6. Infectious Diseases",
        "end": "7. Public Health and Epidemiology"
    },
    "11_public_health.txt": {
        "start": "7. Public Health and Epidemiology",
        "end": "8. Medical Ethics"
    },
    "12_medical_ethics.txt": {
        "start": "8. Medical Ethics",
        "end": "9. Emerging Medical Technologies"
    },
    "13_emerging_tech.txt": {
        "start": "9. Emerging Medical Technologies",
        "end": "10. Long-Range Cross-Referencing"
    },
}

# Extract and save sections
sections_created = 0

for filename, markers in sections.items():
    start_marker = markers["start"]
    end_marker = markers["end"]
    
    # Find section boundaries
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1:
        print(f"⚠️  Skipping {filename} - start marker not found")
        continue
    
    if end_idx == -1:
        # Last section - go to end
        section_content = content[start_idx:]
    else:
        section_content = content[start_idx:end_idx]
    
    # Save section
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(section_content.strip())
    
    sections_created += 1
    
    print(f"✅ Created: {filename} ({len(section_content)} chars)")

print(f"\n" + "=" * 70)
print(f"✅ SPLIT COMPLETE: {sections_created} section files created")
print(f"=" * 70)
print(f"\nNext step: Run batch ingestion")
print(f"  python ingest_medical_sections.py")
print("=" * 70 + "\n")