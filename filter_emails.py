#!/usr/bin/env python3
import csv
import re
import sys


def is_valid_conversation_email(email):
    """Filter out internal/system/generated emails."""
    email = email.lower().strip()

    # Patterns to exclude
    exclude_patterns = [
        r'[a-f0-9]{20,}@[a-z0-9]+\.prd\.prod\.outlook\.com',
        r'[a-f0-9]{20,}@.*\.prod\.outlook\.com',
        r'[a-z0-9]{10,}pr[0-9]{2}mb[0-9]+@',
        r'^(noreply|no-reply|do-not-reply|postmaster|mailer-daemon|system|admin|webmaster|hostmaster|root|abuse)@',
        r'@.*\.prod\.outlook\.com$',
        r'@.*\.mail\.protection\.outlook\.com$',
        r'@mail\.gmail\.com$',  # Gmail system/bounce addresses (not @gmail.com)
        r'[0-9a-f]{32}@',
        r'^[a-z0-9]{30,}@',
        # UUID format local parts (e.g., ded90d28-673a-4450-9f2f-1c85b70e3cf6@anything.com)
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}@',
        # Long strings of zeros (10+) - common in automated system emails
        r'0{10,}',
        # Very long local parts (50+ chars) - typically system-generated
        r'^.{50,}@',
    ]

    for pattern in exclude_patterns:
        if re.search(pattern, email):
            return False

    return True


def clean_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    original_count = len(rows)
    clean_rows = [row for row in rows if is_valid_conversation_email(row.get('email_address', ''))]
    removed_count = original_count - len(clean_rows)

    if clean_rows:
        fieldnames = list(clean_rows[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(clean_rows)

    print(f"Original: {original_count}")
    print(f"Removed: {removed_count} (system/internal emails)")
    print(f"Remaining: {len(clean_rows)} (likely human conversations)")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 filter_emails.py input.csv output_clean.csv")
        sys.exit(1)

    clean_csv(sys.argv[1], sys.argv[2])