import re
from typing import List
from urllib.parse import urljoin
from models import ScrapeResult

# Regex patterns
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
PHONE_REGEX = r'\+?(?:[0-9]\s*[-.()]\s){8,15}[0-9]'
# Basic heuristic for addresses: looks for number followed by words and Street/Avenue/Road/Boulevard/Lane/Drive
ADDRESS_REGEX = r'\b\d{1,5}\s+(?:[A-Za-z0-9#-]+\s+){1,4}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Square)\b'

def extract_emails(text: str) -> List[str]:
    emails = re.findall(EMAIL_REGEX, text)
    
    valid_emails = set()
    for email in emails:
        email = email.lower()
        # Filter out sentry logs and make absolutely sure there is an @
        if "@" in email and "sentry" not in email:
            valid_emails.add(email)
            
    return list(valid_emails)

def extract_phones(text: str) -> List[str]:
    found_phones = set(re.findall(PHONE_REGEX, text))
    cleaned_phones = [re.sub(r'[\(\)\-\.\s]', '', p) for p in found_phones]
    return list(set([p for p in cleaned_phones if len(p) >= 8]))

def extract_addresses(text: str) -> List[str]:
    return list(set(re.findall(ADDRESS_REGEX, text, re.IGNORECASE)))

async def extract_socials(page) -> dict:
    links = await page.locator("a").evaluate_all("elements => elements.map(e => e.href)")
    socials = {"instagram": set(), "facebook": set(), "twitter": set()}
    for link in links:
        if link:
            l = link.lower()
            if 'instagram.com' in l:
                socials["instagram"].add(link.rstrip('/'))
            elif 'facebook.com' in l:
                socials["facebook"].add(link.rstrip('/'))
            elif 'twitter.com' in l or 'x.com' in l:
                socials["twitter"].add(link.rstrip('/'))
    return {k: list(v) for k, v in socials.items()}

async def find_contact_url(page, base_url: str) -> str:
    contact_links = await page.locator("a", has_text=re.compile(r"contact", re.IGNORECASE)).all()
    for link in contact_links:
        href = await link.get_attribute("href")
        if href:
            return urljoin(base_url, href)
    return None

async def scrape_website(url: str, browser, proxy: str = None) -> ScrapeResult:
    try:
        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        if proxy:
            context_options["proxy"] = {"server": proxy}

        context = await browser.new_context(**context_options)
        page = await context.new_page()
        
        # Navigate to main URL
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        content = await page.content()
        business_name = await page.title()
        
        found_emails = set(extract_emails(content))
        found_phones = set(extract_phones(content))
        found_addresses = set(extract_addresses(content))
        
        socials_dict = await extract_socials(page)
        found_instagram = set(socials_dict["instagram"])
        found_facebook = set(socials_dict["facebook"])
        found_twitter = set(socials_dict["twitter"])

        # Check for contact page
        contact_url = await find_contact_url(page, url)
        if contact_url and contact_url != url:
            try:
                await page.goto(contact_url, wait_until="domcontentloaded", timeout=30000)
                contact_content = await page.content()
                
                found_emails.update(extract_emails(contact_content))
                found_phones.update(extract_phones(contact_content))
                found_addresses.update(extract_addresses(contact_content))
                
                contact_socials = await extract_socials(page)
                found_instagram.update(contact_socials["instagram"])
                found_facebook.update(contact_socials["facebook"])
                found_twitter.update(contact_socials["twitter"])
            except Exception as e:
                print(f"Failed to load contact page {contact_url}: {e}")

        await context.close()
        
        return ScrapeResult(
            url=url, 
            business_name=business_name,
            emails=list(found_emails), 
            phones=list(found_phones),
            addresses=list(found_addresses),
            instagram=list(found_instagram),
            facebook=list(found_facebook),
            twitter=list(found_twitter)
        )
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        # Return empty result since error field was removed
        return ScrapeResult(url=url)
