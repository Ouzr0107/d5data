import requests
import csv
from datetime import datetime, timedelta
import time

base_url = "https://pultegroup.wd1.myworkdayjobs.com"
endpoint = "/wday/cxs/pultegroup/PGI/jobs"
url = base_url + endpoint

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}


def fetch_jobs(offset):
    payload["offset"] = offset
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data at offset {offset}: {e}")
        return None


def parse_posted_date(posted_on):
    posted_on = posted_on.lower()
    today = datetime.now()

    if "yesterday" in posted_on:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "days ago" in posted_on:
        try:
            days = int(posted_on.split()[1])
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            return posted_on
    return posted_on


def scrape_jobs():
    jobs = []
    offset = 0
    total_jobs = 0

    data = fetch_jobs(offset)
    if not data:
        print("Failed to fetch initial data. Exiting.")
        return

    total_jobs = data.get("total", 0)
    print(f"Total jobs to scrape: {total_jobs}")

    for job in data.get("jobPostings", []):
        job_id = job.get("bulletFields", [""])[0]
        title = job.get("title", "")
        job_data = {
            "job_id": job_id,
            "title": title,
            "location": job.get("locationsText", ""),
            "posted_on": parse_posted_date(job.get("postedOn", "")),
            "url": f"{base_url}/wday/cxs/pultegroup/PGI" + job.get("externalPath", ""),
        }
        jobs.append(job_data)

    while offset + payload["limit"] < total_jobs:
        offset += payload["limit"]
        print(
            f"Fetching jobs {offset + 1} to {min(offset + payload['limit'], total_jobs)}"
        )
        data = fetch_jobs(offset)
        if not data:
            print(
                f"Failed to fetch jobs at offset {offset}. Continuing with collected data."
            )
            break

        for job in data.get("jobPostings", []):
            job_id = job.get("bulletFields", [""])[0]
            title = job.get("title", "")
            job_data = {
                "job_id": job_id,
                "title": title,
                "location": job.get("locationsText", ""),
                "posted_on": parse_posted_date(job.get("postedOn", "")),
                "url": f"{base_url}/wday/cxs/pultegroup/PGI"
                + job.get("externalPath", ""),
            }
            jobs.append(job_data)

        time.sleep(1)

    csv_filename = f"pultegroup_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=["job_id", "title", "location", "posted_on", "url"]
        )
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)

    print(f"Saved {len(jobs)} jobs to {csv_filename}")


if __name__ == "__main__":
    scrape_jobs()
