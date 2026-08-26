import re
from dotenv import load_dotenv
load_dotenv() # Load env vars before local modules that rely on them

from typing import List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
from models import UrlList, ScrapeResult, Lead, LeadBatch, JobStartResponse, JobStatusResponse
from scraper import scrape_website

import uuid
from routers import auth, google

app = FastAPI(title="Email Crawler API")
app.include_router(auth.router)
app.include_router(google.router)

jobs = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/extract-emails", response_model=List[ScrapeResult])
async def extract_emails(request: UrlList):
    if not request.urls:
        raise HTTPException(status_code=400, detail="The list of URLs cannot be empty.")
    
    results = []
    
    # Initialize Playwright
    async with async_playwright() as p:
        # Launch browser in headful mode
        browser = await p.chromium.launch(headless=True)
        
        # Process each URL one by one sequentially
        for url in request.urls:
            # Add basic validation for scheme
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
                
            result = await scrape_website(url, browser, proxy=request.proxy)
            results.append(result)
            
        await browser.close()
        
    return results

@app.post("/process-leads", response_model=JobStartResponse)
async def process_leads(request: LeadBatch, background_tasks: BackgroundTasks):
    if not request.leads:
        raise HTTPException(status_code=400, detail="The list of leads cannot be empty.")
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "total_leads": len(request.leads),
        "completed_leads": 0,
        "results": []
    }
    
    background_tasks.add_task(run_scraping_job, job_id, request)
    return {"job_id": job_id, "message": "Job started in the background."}

async def run_scraping_job(job_id: str, request: LeadBatch):
    try:
        enriched_leads = []
        for lead in request.leads:
            if lead.website:
                url = lead.website
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url
                
                try:
                    # Launch and close browser for each website
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        result = await scrape_website(url, browser, proxy=request.proxy)
                        await browser.close()
                    
                    if result.emails:
                        lead.email = ", ".join(result.emails)
                    if result.phones and not lead.phone:
                        lead.phone = ", ".join(result.phones)
                    if result.facebook:
                        lead.facebook = ", ".join(result.facebook)
                    if result.instagram:
                        lead.instagram = ", ".join(result.instagram)
                    if result.twitter:
                        lead.twitter = ", ".join(result.twitter)
                except Exception as scrape_err:
                    lead.error = f"Scraping failed: {str(scrape_err)}"
                    
            enriched_leads.append(lead)
            jobs[job_id]["completed_leads"] += 1
            jobs[job_id]["results"] = enriched_leads

        jobs[job_id]["status"] = "completed"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.get("/job-status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found.")
    return jobs[job_id]

@app.get("/")
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Lead scraper backend is running"}


if __name__ == "__main__":
    import asyncio

    async def main():
        test_request = UrlList(urls=["https://www.daraz.pk", "https://lawyersofpakistan.pk/"])
        results = await extract_emails(test_request)
        
        # Print results in a table format
        print("\n" + "="*185)
        print(f"{'URL / Name':<35} | {'Business Name':<20} | {'Emails':<25} | {'Phones':<20} | {'Instagram':<15} | {'Facebook':<15} | {'Twitter':<15} | {'Addresses'}")
        print("-" * 185)
        
        for r in results:
            url_display = r.url[:32] + "..." if len(r.url) > 35 else r.url
            business_name_display = (r.business_name[:17] + "...") if (r.business_name and len(r.business_name) > 20) else (r.business_name or "")
            emails_display = ", ".join(r.emails)[:22] + "..." if len(", ".join(r.emails)) > 25 else ", ".join(r.emails)
            phones_display = ", ".join(r.phones)[:17] + "..." if len(", ".join(r.phones)) > 20 else ", ".join(r.phones)
            instagram_display = ", ".join(r.instagram)[:12] + "..." if len(", ".join(r.instagram)) > 15 else ", ".join(r.instagram)
            facebook_display = ", ".join(r.facebook)[:12] + "..." if len(", ".join(r.facebook)) > 15 else ", ".join(r.facebook)
            twitter_display = ", ".join(r.twitter)[:12] + "..." if len(", ".join(r.twitter)) > 15 else ", ".join(r.twitter)
            addresses_display = ", ".join(r.addresses)[:30] + "..." if len(", ".join(r.addresses)) > 30 else ", ".join(r.addresses)
            
            print(f"{url_display:<35} | {business_name_display:<20} | {emails_display:<25} | {phones_display:<20} | {instagram_display:<15} | {facebook_display:<15} | {twitter_display:<15} | {addresses_display}")
                
        print("="*185 + "\n")

        # Save to CSV and Excel
        import os
        import pandas as pd
        
        os.makedirs("reports", exist_ok=True)
        
        # Define which fields the user wants in the report
        # You can remove any field from this list (e.g., remove "Facebook") to exclude it from the Excel/CSV
        selected_fields = [
            "URL", "Business Name", "Emails", "Phones", 
            "Instagram", "Facebook", "Twitter", "Addresses"
        ]
        
        data = []
        for r in results:
            # Create a full dictionary for the row
            row_data = {
                "URL": r.url,
                "Business Name": r.business_name or "",
                "Emails": ", ".join(r.emails),
                "Phones": ", ".join(r.phones),
                "Instagram": ", ".join(r.instagram),
                "Facebook": ", ".join(r.facebook),
                "Twitter": ", ".join(r.twitter),
                "Addresses": ", ".join(r.addresses)
            }
            # Filter the row data to only include the selected fields
            filtered_row = {field: row_data[field] for field in selected_fields if field in row_data}
            data.append(filtered_row)
            
        df = pd.DataFrame(data)
        df.to_csv("reports/results.csv", index=False)
        df.to_excel("reports/results.xlsx", index=False)
        print("Results successfully saved to 'reports/results.csv' and 'reports/results.xlsx'.")

    asyncio.run(main())
