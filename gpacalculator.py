#!/usr/bin/env python3
"""
Robust transcript term GPA aggregator.

- Parses term headers like:
    Term: Fall Qtr 2025
    Term: Sum Ses II 2024
    Winter Quarter 2023
- Looks for lines containing:
    Term Grade Points: 52.30
    Term GPA Credits: 16.00
- Shows terms in chronological order and computes cumulative GPA for a chosen range.
"""

import pdfplumber
import re
import sys

TERM_RE = re.compile(
    r"(?:Term:\s*)?((?:Fall|Winter|Spring|Summer|Sum\s+Ses\s+[IVXLC]+)"
    r"\s*(?:Qtr|Quarter|Ses)?\s*\d{4})",
    re.IGNORECASE
)

GP_RE = re.compile(r"Term\s+Grade\s+Points[:\s]*([\d\.,]+)", re.IGNORECASE)
CR_RE = re.compile(r"Term\s+GPA\s+Credits[:\s]*([\d\.,]+)", re.IGNORECASE)

def extract_text_from_pdf(path):
    try:
        with pdfplumber.open(path) as pdf:
            pages = []
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    pages.append(t)
            return "\n".join(pages)
    except Exception as e:
        print("Error opening PDF:", e)
        sys.exit(1)

def parse_terms_from_text(text, debug=False):
    terms = {}
    current_term = None

    for raw_line in text.splitlines():
        if not raw_line:
            continue
        line = raw_line.replace("\xa0", " ").strip()

        if debug and any(k.lower() in line.lower() for k in ("term", "qtr", "quarter", "sum ses", "grade points", "gpa credits")):
            print("DEBUG LINE:", repr(line))

        m = TERM_RE.search(line)
        if m:
            term_name = re.sub(r"\s+", " ", m.group(1).strip())
            base = term_name
            suffix = 1
            while term_name in terms:
                suffix += 1
                term_name = f"{base} ({suffix})"
            terms[term_name] = {"grade_points": None, "credits": None, "raw_lines": []}
            current_term = term_name
            continue

        if current_term:
            gp = GP_RE.search(line)
            if gp:
                val = gp.group(1).replace(",", "").strip()
                try:
                    terms[current_term]["grade_points"] = float(val)
                except ValueError:
                    print(f"Warning: could not parse grade points '{val}' for term {current_term}")
            cr = CR_RE.search(line)
            if cr:
                val = cr.group(1).replace(",", "").strip()
                try:
                    terms[current_term]["credits"] = float(val)
                except ValueError:
                    print(f"Warning: could not parse credits '{val}' for term {current_term}")

            terms[current_term]["raw_lines"].append(line)

    return terms

def compute_cumulative_gpa_for_term_list(terms_dict, chronological_terms):
    total_gp = 0.0
    total_cr = 0.0
    skipped_terms = []

    for term in chronological_terms:
        gp = terms_dict[term]["grade_points"]
        cr = terms_dict[term]["credits"]
        if gp is None or cr is None:
            skipped_terms.append(term)
            continue
        total_gp += gp
        total_cr += cr

    return total_gp, total_cr, skipped_terms


def prompt_for_missing_in_range(terms, selected_terms):
    """Ask user to manually fill missing values for selected terms only."""
    for t in selected_terms:
        for key in ("grade_points", "credits"):
            if terms[t][key] is None:
                while True:
                    user_in = input(f"{t} is missing {key.replace('_',' ')}. Enter value (or press Enter to skip): ").strip()
                    if not user_in:
                        break
                    try:
                        terms[t][key] = float(user_in)
                        break
                    except ValueError:
                        print("Invalid number. Try again.")

def main():
    pdf_path = input("Enter transcript PDF path: ").strip()
    text = extract_text_from_pdf(pdf_path)
    terms = parse_terms_from_text(text)
    if not terms:
        print("No terms found.")
        sys.exit(1)

    chronological_terms = list(terms.keys())[::-1]  # oldest -> newest

    print("\nDetected terms (chronological order):")
    for i, t in enumerate(chronological_terms, 1):
        gp = terms[t]["grade_points"]
        cr = terms[t]["credits"]
        gp_str = f"{gp:.2f}" if gp is not None else "MISSING"
        cr_str = f"{cr:.2f}" if cr is not None else "MISSING"
        print(f"{i}. {t} | Grade Points: {gp_str} | Credits: {cr_str}")

    try:
        start = int(input("\nEnter start term number: ").strip()) - 1
        end = int(input("Enter end term number: ").strip()) - 1
    except ValueError:
        print("Invalid input.")
        sys.exit(1)

    if start < 0 or end >= len(chronological_terms) or start > end:
        print("Invalid range.")
        sys.exit(1)

    selected_terms = chronological_terms[start:end+1]


    prompt_for_missing_in_range(terms, selected_terms)

    total_gp, total_cr, skipped = compute_cumulative_gpa_for_term_list(terms, selected_terms)

    print("\nSelected terms:")
    for t in selected_terms:
        gp = terms[t]["grade_points"]
        cr = terms[t]["credits"]
        print(f" - {t}: GP={gp if gp is not None else 'MISSING'}, Credits={cr if cr is not None else 'MISSING'}")

    if skipped:
        print("\nWARNING: Still missing values for these terms:")
        for t in skipped:
            print("  -", t)

    print(f"\nTotals -> Grade Points: {total_gp:.2f}   Credits: {total_cr:.2f}")
    if total_cr == 0:
        print("Cannot compute GPA: total credits = 0.")
    else:
        gpa = total_gp / total_cr
        print(f"CUMULATIVE GPA for selected range: {gpa:.4f}")

if __name__ == "__main__":
    main()
