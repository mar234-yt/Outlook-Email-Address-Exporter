import os, re, csv, tempfile, shutil, subprocess, glob, time, threading, sys

class EmailProcessor:
    def __init__(self, pst_path, output_dir="."):
        self.pst_path = pst_path
        self.output_dir = output_dir
        self.raw_emails = []
        self.clean_emails = []
        self._temp_dir = None
        self._stop_monitor = threading.Event()

    def _cleanup_old_temp(self):
        for old in glob.glob('/tmp/pst_extract_*'):
            try:
                shutil.rmtree(old, ignore_errors=True)
            except Exception:
                pass

    def _count_files(self, directory):
        return sum(1 for _, _, files in os.walk(directory) for _ in files)

    def _monitor_extraction(self):
        """Background thread: prints file count to stderr every 3 seconds."""
        while not self._stop_monitor.is_set():
            if self._temp_dir and os.path.exists(self._temp_dir):
                count = self._count_files(self._temp_dir)
                sys.stderr.write(f"\r  [extract] Files extracted so far: {count}   ")
                sys.stderr.flush()
            time.sleep(3)
        sys.stderr.write("\n")
        sys.stderr.flush()

    def _print_progress_bar(self, current, total, prefix='Progress', suffix='Complete', length=40):
        if total == 0:
            return
        filled = int(length * current // total)
        bar = '█' * filled + '-' * (length - filled)
        percent = f"{100 * current / total:.1f}%"
        sys.stdout.write(f'\r{prefix} |{bar}| {percent} {suffix}')
        sys.stdout.flush()
        if current == total:
            sys.stdout.write('\n')
            sys.stdout.flush()

    def extract_from_pst(self):
        self._cleanup_old_temp()
        self._temp_dir = tempfile.mkdtemp(prefix='pst_extract_')
        partial = False

        print(f"\nExtracting PST to: {self._temp_dir}")
        print("Running readpst... (this may take 10-30 minutes for large mailboxes)")
        print("Press Ctrl+C to abort.\n")

        # Start background monitor
        self._stop_monitor.clear()
        monitor = threading.Thread(target=self._monitor_extraction, daemon=True)
        monitor.start()

        try:
            # STABLE approach: inherited stdout/stderr — readpst talks directly to terminal
            subprocess.run(
                ['readpst', '-M', '-o', self._temp_dir, self.pst_path],
                check=True
            )
        except subprocess.CalledProcessError as e:
            extracted = self._count_files(self._temp_dir)
            if extracted > 100:
                print(f"\n[WARNING] readpst crashed (exit {e.returncode}) but {extracted} files were already extracted.")
                print("Processing partial data — most unique addresses are already captured.")
                partial = True
            else:
                raise RuntimeError(
                    f"readpst failed with exit {e.returncode} and only extracted {extracted} files. "
                    f"Try: readpst -M -o /tmp/manual_extract '{self.pst_path}'"
                ) from e
        finally:
            self._stop_monitor.set()
            monitor.join(timeout=2)

        # --- Scan extracted files with progress bar ---
        try:
            pattern = r'[\w-]+(?:\.[\w-]+)*@[\w-]+(?:\.[\w-]+)*\.\w+'
            total_files = self._count_files(self._temp_dir)
            print(f"\nScanning {total_files} extracted files for email addresses...")
            if partial:
                print("NOTE: Partial extraction — some emails were skipped due to PST corruption.")

            file_count = 0
            email_count = 0

            for root, _, files in os.walk(self._temp_dir):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', errors='ignore') as f:
                            found = re.findall(pattern, f.read())
                            for addr in found:
                                addr = addr.lower().strip().strip('.')
                                if len(addr) > 5 and '.' in addr.split('@')[-1]:
                                    self.raw_emails.append(addr)
                                    email_count += 1
                    except Exception:
                        pass
                    file_count += 1
                    if total_files > 0 and (file_count % 50 == 0 or file_count == total_files):
                        self._print_progress_bar(
                            file_count, total_files,
                            prefix='Scanning',
                            suffix=f'({email_count} addresses found)'
                        )

            print(f"\nDone. Scanned {file_count} files, extracted {email_count} raw addresses.")
        finally:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def filter_and_sort(self):
        system_domains = [
            r'prod\.outlook\.com$',
            r'prod\.exchangelabs\.com$',
            r'prod\.protection\.outlook\.com$',
            r'eurprd\d+\.prod\.outlook\.com$',
            r'namprd\d+\.prod\.outlook\.com$',
            r'eurp\d+\.prod\.outlook\.com$',
            r'arep\d+\.prod\.outlook\.com$',
            r'xt\.local$',
            r'ec2\.internal$',
            r'email\.apple\.com$',
            r'linkedin\.com$',
            r'activehosted\.com$',
            r'foxitinfo\.com$',
            r'pd25\.com$',
            r'qemailserver\.com$',
            r'tm1\.openai\.com$',
            r'm\.letsenhance\.io$',
            r'infoemails\.microsoft\.com$',
            r'wix\.com$',
            r'omptrans\.emails\.wix\.com$',
            r'salesforce\.com$',
            r'pdfleader\.com$',
            r'minewtech\.com$',
            r'fixably\.istyle\.bg$',
            r'microsoft\.com$',
            r'microsoftonline\.com$',
            r'openai\.com$',
            r'anthropic\.com$',
            r'adobe\.com$',
            r'dell\.com$',
            r'printbyxerox\.com$',
            r'welisten\.dell\.com$',
            r'email\.foxitinfo\.com$',
            r'email\.anthropic\.com$',
            r'hubspotemail\.net$',
            r'organimi\.com$',
            r'signin\.autodesk\.com$',
            r'3cx\.net$',
            r'autodesk\.com$',
            r'xerox\.com$',
            r'borica\.bg$',
            r'registryagency\.bg$',
            r'smtp3\.registryagency\.bg$',
            r'navtech\.net$',
            r'webex\.com$',
            r'mail\.gmail\.com$',
            r'customer\.io$',
            r'leave\.email\.foxitinfo\.com$',
            r'bounce\.email\.foxitinfo\.com$',
            r'bounce\.s11\.mc\.pd25\.com$',
            r'unsubscribe\.qemailserver\.com$',
            r'az\.[a-z]+\.microsoft\.com$',
            r'vi\d+eur\d+bg\d+\.eop-eur\d+\.prod\.protection\.outlook\.com$',
            r'db\d+eur\d+bg\d+\.eop-eur\d+\.prod\.protection\.outlook\.com$',
            r'am\d+eur\d+bg\d+\.eop-eur\d+\.prod\.protection\.outlook\.com$',
            r'cdg\d+s\d+mta\d+\.xt\.local$',
            r'atl\d+s\d+mta\d+\.xt\.local$',
            r'ip-172-\d+-\d+-\d+\.ec2\.internal$',
        ]

        local_junk = [
            r'^image\d+\.(jpg|jpeg|png|gif|bmp)',
            r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            r'^[a-f0-9]{20,}$',
            r'^bounce[-_.]',
            r'^leave[-_.]',
            r'^unsubscribe',
            r'^donotreply$',
            r'^noreply$',
            r'^no-reply$',
            r'^postmaster$',
            r'^abuse$',
            r'^mailer-daemon',
            r'^fbl-report',
            r'^notifications',
            r'^message$',
            r'^maccount',
            r'^msonlineservicesteam',
            r'^azure$',
            r'^otp$',
            r'^mixpanelincident',
            r'^case-',
            r'^badactor',
            r'^ctr_',
            r'^null$',
            r'^help\.dell',
            r'^part\d+\.',
            r'^icloud_footer_signoff',
            r'^0{5,}',
            r'^\d{6,}$',
            r'^.{30,}$',
            r'^\d{8,}\.',
            r'^\d{6,}@',
            r'^\d{4,}-\d{4,}-\d{4,}',
            r'^\d+\.\d+\.\d+\.\d+',
            r'^cr-',
            r'^crmnotifications',
            r'^xeroxworkplacecloud',
            r'^printer\d*$',
            r'^getstarted$',
            r'^signin$',
            r'^info$',
            r'^apps$',
            r'^marketing$',
            r'^clientservices$',
            r'^operations$',
            r'^order$',
            r'^office$',
            r'^finance$',
            r'^chatths$',
            r'^cybersecuritytraining$',
            r'^migration$',
            r'^dms$',
            r'^crmadmin$',
            r'^allcompany',
            r'^itdocuments$',
            r'^it\.support$',
            r'^it$',
            r'^medical$',
            r'^notice$',
            r'^0\.\d+\.\d+\.\d+',
            r'^\d{4,}\.\d{4,}\.\d{4,}',
            r'^[a-z]{2,5}\d+pr\d+mb\d+',
            r'^db\d+pr\d+mb\d+',
            r'^am\d+pr\d+mb\d+',
            r'^as\d+pr\d+mb\d+',
            r'^du\d+pr\d+mb\d+',
            r'^pa\d+pr\d+mb\d+',
            r'^gv\d+pr\d+mb\d+',
            r'^pawpr\d+mb\d+',
            r'^co\d+pr\d+mb\d+',
            r'^bn\d+pr\d+mb\d+',
            r'^by\d+pr\d+mb\d+',
            r'^dm\d+pr\d+mb\d+',
            r'^ch\d+pr\d+mb\d+',
            r'^ia\d+pr\d+mb\d+',
            r'^lv\d+pr\d+mb\d+',
            r'^auzp\d+mb\d+',
            r'^frzp\d+mb\d+',
            r'^dbap\d+mb\d+',
            r'^dbbpr\d+mb\d+',
            r'^ambpr\d+mb\d+',
        ]

        seen = set()
        total = len(self.raw_emails)
        print(f"\nFiltering {total} raw addresses...")

        for i, email in enumerate(self.raw_emails, 1):
            email = email.strip()
            local, _, domain = email.partition('@')
            if any(re.search(p, domain) for p in system_domains):
                continue
            if any(re.search(p, local) for p in local_junk):
                continue
            if domain == 'gmail.com':
                if re.search(r'^[a-z]{10,}$', local) or re.search(r'^\d+$', local):
                    continue
            if email not in seen:
                seen.add(email)
                self.clean_emails.append(email)

            if i % 500 == 0 or i == total:
                self._print_progress_bar(i, total, prefix='Filtering', suffix=f'({len(self.clean_emails)} kept)')

        self.clean_emails.sort()
        print(f"\nResult: {total} raw -> {len(self.clean_emails)} clean unique addresses")

    def save_to_csv(self, filename):
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email_address'])
            for e in self.clean_emails:
                writer.writerow([e])
        print(f"Saved to: {path}")
        return path

    def get_stats(self):
        return {
            'raw': len(self.raw_emails),
            'unique_clean': len(self.clean_emails)
        }