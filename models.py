import os, re, csv, tempfile, shutil, subprocess

class EmailProcessor:
    def __init__(self, pst_path, output_dir="."):
        self.pst_path = pst_path
        self.output_dir = output_dir
        self.raw_emails = []
        self.clean_emails = []

    def extract_from_pst(self):
        temp_dir = tempfile.mkdtemp(prefix='pst_extract_')
        try:
            subprocess.run(['readpst', '-M', '-o', temp_dir, self.pst_path], check=True)
            # Improved regex: no leading/trailing dots in local part
            pattern = r'[\w-]+(?:\.[\w-]+)*@[\w-]+(?:\.[\w-]+)*\.\w+'
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    path = os.path.join(root, file)
                    with open(path, 'r', errors='ignore') as f:
                        found = re.findall(pattern, f.read())
                        for addr in found:
                            addr = addr.lower().strip()
                            # Strip accidental leading/trailing dots
                            addr = addr.strip('.')
                            if len(addr) > 5 and '.' in addr.split('@')[-1]:
                                self.raw_emails.append(addr)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def filter_and_sort(self):
        # Domain-based system filters
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

        # Local-part heuristic filters
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
            r'^.{30,}$',  # ANY local part over 30 chars is almost certainly system
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
            r'^[a-z]{2,5}\d+pr\d+mb\d+',  # Exchange server naming
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
        for email in self.raw_emails:
            email = email.strip()
            local, _, domain = email.partition('@')

            # Domain-based filtering
            if any(re.search(p, domain) for p in system_domains):
                continue

            # Local-part filtering
            if any(re.search(p, local) for p in local_junk):
                continue

            # Gmail heuristic: filter purely numeric or long random alpha-only
            if domain == 'gmail.com':
                if re.search(r'^[a-z]{10,}$', local) or re.search(r'^\d+$', local):
                    continue

            if email not in seen:
                seen.add(email)
                self.clean_emails.append(email)

        self.clean_emails.sort()

    def save_to_csv(self, filename):
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email_address'])
            for e in self.clean_emails:
                writer.writerow([e])
        return path

    def get_stats(self):
        return {
            'raw': len(self.raw_emails),
            'unique_clean': len(self.clean_emails)
        }
