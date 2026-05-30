import os, re, csv, tempfile, shutil, subprocess

class EmailProcessor:
    def __init__(self, pst_path, output_dir="."):
        self.pst_path = pst_path
        self.output_dir = output_dir
        self.raw_emails = []
        self.clean_emails = []

    def extract_from_pst(self):
        """Извлича имейли от PST файла чрез readpst."""
        temp_dir = tempfile.mkdtemp(prefix='pst_extract_')
        try:
            subprocess.run(['readpst', '-M', '-o', temp_dir, self.pst_path], check=True)
            pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    path = os.path.join(root, file)
                    with open(path, 'r', errors='ignore') as f:
                        found = re.findall(pattern, f.read())
                        for addr in found:
                            if len(addr) > 5 and '.' in addr.split('@')[-1]:
                                self.raw_emails.append(addr.lower())
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def filter_and_sort(self):
        """Филтрира системните имейли и сортира."""
        exclude = [
            r'noreply|no-reply|postmaster|abuse',
            r'[a-f0-9]{32}',
            r'0{10,}',
            r'^.{50,}@',
        ]
        seen = set()
        for email in self.raw_emails:
            email = email.strip()
            if any(re.search(p, email) for p in exclude):
                continue
            if email not in seen:
                seen.add(email)
                self.clean_emails.append(email)
        self.clean_emails.sort()   # ← сортиране, както изискват

    def save_to_csv(self, filename):
        """Записва резултата в CSV."""
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email_address'])
            for e in self.clean_emails:
                writer.writerow([e])
        return path

    def get_stats(self):
        """Връща статистика."""
        return {
            'raw': len(self.raw_emails),
            'unique_clean': len(self.clean_emails)
        }