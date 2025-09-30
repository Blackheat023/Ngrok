import requests
import os
import json
import re
import dns.resolver
import whois
import hashlib
import base64
import time
import urllib.parse
from email.utils import parseaddr
from datetime import datetime
import socket

class OSINTEmailInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.results = {}

    def osint_email_validator(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def osint_email_parser(self, email):
        if not self.osint_email_validator(email):
            return None
        
        parsed = parseaddr(email)
        local_part, domain = email.split('@')
        
        return {
            'email': email,
            'local_part': local_part,
            'mdomain': domain,
            'parsed_name': parsed[0],
            'parsed_email': parsed[1],
            'username': local_part.split('+')[0] if '+' in local_part else local_part
        }

    def osint_email_domain_info(self, domain):
        try:
            domain_info = whois.whois(domain)
            mx_records = []
            
            try:
                mx_query = dns.resolver.resolve(domain, 'MX')
                mx_records = [str(record) for record in mx_query]
            except:
                pass
            
            return {
                'domain': domain,
                'registrar': str(domain_info.registrar) if domain_info.registrar else 'Unknown',
                'creation_date': str(domain_info.creation_date) if domain_info.creation_date else 'Unknown',
                'expiration_date': str(domain_info.expiration_date) if domain_info.expiration_date else 'Unknown',
                'name_servers': domain_info.name_servers if domain_info.name_servers else [],
                'mx_records': mx_records,
                'status': domain_info.status if domain_info.status else []
            }
        except:
            return {'domain': domain, 'error': 'Domain information not available'}

    def osint_email_breach_check(self, email):
        breaches = []
        
        try:
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
            headers = {'hibp-api-key': 'YOUR_API_KEY', 'User-Agent': 'OSINT-Email-Tool'}
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                breaches = response.json()
            elif response.status_code == 404:
                breaches = []
        except:
            pass
        
        return {'email': email, 'breaches': breaches, 'breach_count': len(breaches)}

    def osint_email_social_media_check(self, email):
        social_platforms = {
            'gravatar': f'https://www.gravatar.com/avatar/{hashlib.md5(email.lower().encode()).hexdigest()}',
            'github': f'https://github.com/{email.split("@")[0]}',
            'twitter': f'https://twitter.com/{email.split("@")[0]}',
            'instagram': f'https://instagram.com/{email.split("@")[0]}',
            'linkedin': f'https://linkedin.com/in/{email.split("@")[0]}'
        }
        
        results = {}
        for platform, url in social_platforms.items():
            try:
                response = self.session.head(url, timeout=5)
                results[platform] = {
                    'url': url,
                    'exists': response.status_code == 200,
                    'status_code': response.status_code
                }
            except:
                results[platform] = {
                    'url': url,
                    'exists': False,
                    'status_code': 'timeout'
                }
        
        return results

    def osint_email_google_search(self, email):
        try:
            search_query = urllib.parse.quote(f'"{email}"')
            search_url = f'https://www.google.com/search?q={search_query}'
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'search_performed': True,
                    'query': email,
                    'url': search_url,
                    'content_length': len(response.text)
                }
        except:
            pass
        
        return {'search_performed': False, 'query': email}

    def osint_email_reputation_check(self, email):
        domain = email.split('@')[1]
        reputation_data = {
            'disposable_email': False,
            'suspicious_domain': False,
            'mx_valid': False,
            'domain_age_days': 0
        }
        
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', '0-mail.com', '10mail.org'
        ]
        
        reputation_data['disposable_email'] = domain in disposable_domains
        
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            reputation_data['mx_valid'] = len(mx_records) > 0
        except:
            pass
        
        return reputation_data

    def osint_email_format_analysis(self, email):
        local_part = email.split('@')[0]
        
        patterns = {
            'firstname_lastname': bool(re.match(r'^[a-z]+\.[a-z]+$', local_part.lower())),
            'firstname_initial': bool(re.match(r'^[a-z]+\.[a-z]$', local_part.lower())),
            'initial_lastname': bool(re.match(r'^[a-z]\.[a-z]+$', local_part.lower())),
            'numeric_included': bool(re.search(r'\d', local_part)),
            'underscore_format': '_' in local_part,
            'hyphen_format': '-' in local_part,
            'plus_format': '+' in local_part,
            'length': len(local_part)
        }
        
        return patterns

    def osint_email_dns_investigation(self, domain):
        dns_info = {}
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME']
        
        for record_type in record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                dns_info[record_type] = [str(record) for record in answers]
            except:
                dns_info[record_type] = []
        
        return dns_info

    def osint_email_generate_variations(self, email):
        local_part, domain = email.split('@')
        variations = []
        
        if '.' in local_part:
            parts = local_part.split('.')
            variations.extend([
                f"{parts[0]}{parts[1]}@{domain}",
                f"{parts[0]}_{parts[1]}@{domain}",
                f"{parts[0]}-{parts[1]}@{domain}",
                f"{parts[1]}.{parts[0]}@{domain}"
            ])
        
        variations.extend([
            f"{local_part}1@{domain}",
            f"{local_part}2@{domain}",
            f"{local_part}123@{domain}",
            f"admin@{domain}",
            f"info@{domain}",
            f"contact@{domain}"
        ])
        
        return list(set(variations))

    def osint_email_metadata_extract(self, email):
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'email_hash': hashlib.sha256(email.encode()).hexdigest(),
            'local_part_length': len(email.split('@')[0]),
            'domain_length': len(email.split('@')[1]),
            'contains_numbers': bool(re.search(r'\d', email)),
            'contains_special_chars': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', email.split('@')[0])),
            'tld': email.split('.')[-1]
        }
        
        return metadata

    def osint_email_comprehensive_investigation(self, email):
        if not self.osint_email_validator(email):
            return {'error': 'Invalid email format'}
        
        investigation_results = {
            'target_email': email,
            'timestamp': datetime.now().isoformat(),
            'parsed_info': self.osint_email_parser(email),
            'domain_info': self.osint_email_domain_info(email.split('@')[1]),
            'breach_check': self.osint_email_breach_check(email),
            'social_media': self.osint_email_social_media_check(email),
            'google_search': self.osint_email_google_search(email),
            'reputation': self.osint_email_reputation_check(email),
            'format_analysis': self.osint_email_format_analysis(email),
            'dns_investigation': self.osint_email_dns_investigation(email.split('@')[1]),
            'email_variations': self.osint_email_generate_variations(email),
            'metadata': self.osint_email_metadata_extract(email)
        }
        
        return investigation_results

    def osint_email_export_results(self, results, filename=None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"osint_email_investigation_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False, default=str)
            return f"Results exported to {filename}"
        except Exception as e:
            return f"Export failed: {str(e)}"

def osint_email_main_investigation(email_address):
    investigator = OSINTEmailInvestigator()
    results = investigator.osint_email_comprehensive_investigation(email_address)
    return results

def osint_email_quick_check(email_address):
    investigator = OSINTEmailInvestigator()
    if not investigator.osint_email_validator(email_address):
        return {'error': 'Invalid email format'}
    
    return {
        'email': email_address,
        'valid': True,
        'parsed': investigator.osint_email_parser(email_address),
        'reputation': investigator.osint_email_reputation_check(email_address),
        'format_analysis': investigator.osint_email_format_analysis(email_address)
    }

def osint_email_batch_investigation(email_list):
    investigator = OSINTEmailInvestigator()
    results = {}
    
    for email in email_list:
        print(f"Investigating: {email}")
        results[email] = investigator.osint_email_comprehensive_investigation(email)
        time.sleep(1)
    
    return results

if __name__ == "__main__"
    target_email = input("\033[1;32m─(\033[0m\033[1;31m?\033[0m\033[1;32m)─\033[0m\033[1;31m Masukkan Alamat Email Target\033[0m\033[1;32m :\033[0m\033[1;33m ")
    
    print("")
    results = osint_email_main_investigation(target_email)
    
    print("\033[101m\033[1;32mHASIL OSINTN EMAIL\033[0m")
    print("\033[1;33m" + json.dumps(results, indent=2, default=str) + "\033[0m")
    
    export_choice = input("\n\033[1;32m─(\033[0m\033[1;31mY\033[0m\033[1;32m)─\033[0m\033[1;31m Simpan Hasil\n\033[1;32m─(\033[0m\033[1;31mN\033[0m\033[1;32m)─\033[0m\033[1;31m Jangan Simpan Hasil\n\033[1;32m─(\033[0m\033[1;31m?\033[0m\033[1;32m)─\033[0m\033[1;31m Simpan Hasil Ke File? \033[1;32m:\033[1;33m ")
    if export_choice.lower() == 'y':
        investigator = OSINTEmailInvestigator()
        export_result = investigator.osint_email_export_results(results)
        print(export_result)
