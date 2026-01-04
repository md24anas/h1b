"""
Import OPT/STEM OPT Employer Data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Top 200 OPT/STEM OPT Employers
OPT_EMPLOYERS = [
    {"rank": 1, "name": "Amazon", "total": 10167, "opt": 5379, "stem_opt": 6679},
    {"rank": 2, "name": "University of California", "total": 2916, "opt": 2112, "stem_opt": 1278},
    {"rank": 3, "name": "Google", "total": 2454, "opt": 1110, "stem_opt": 1778},
    {"rank": 4, "name": "Microsoft", "total": 2143, "opt": 1066, "stem_opt": 1496},
    {"rank": 5, "name": "Meta", "total": 2032, "opt": 1081, "stem_opt": 1302},
    {"rank": 6, "name": "Arizona State University", "total": 1962, "opt": 1895, "stem_opt": 136},
    {"rank": 7, "name": "Goldman Sachs", "total": 1695, "opt": 1148, "stem_opt": 962},
    {"rank": 8, "name": "Intel", "total": 1641, "opt": 946, "stem_opt": 1023},
    {"rank": 9, "name": "Walmart", "total": 1623, "opt": 951, "stem_opt": 1140},
    {"rank": 10, "name": "Apple", "total": 1621, "opt": 1135, "stem_opt": 973},
    {"rank": 11, "name": "University of Texas", "total": 1618, "opt": 1305, "stem_opt": 536},
    {"rank": 12, "name": "Tesla", "total": 1548, "opt": 1170, "stem_opt": 901},
    {"rank": 13, "name": "Deloitte", "total": 1544, "opt": 1033, "stem_opt": 833},
    {"rank": 14, "name": "Ernst & Young", "total": 1413, "opt": 889, "stem_opt": 854},
    {"rank": 15, "name": "ByteDance", "total": 1362, "opt": 1045, "stem_opt": 642},
    {"rank": 17, "name": "JP Morgan Chase", "total": 1218, "opt": 675, "stem_opt": 887},
    {"rank": 18, "name": "McKinsey & Company", "total": 1169, "opt": 680, "stem_opt": 810},
    {"rank": 19, "name": "Harvard University", "total": 1036, "opt": 799, "stem_opt": 407},
    {"rank": 20, "name": "Johns Hopkins University", "total": 1013, "opt": 827, "stem_opt": 382},
    {"rank": 21, "name": "University of Michigan", "total": 977, "opt": 767, "stem_opt": 369},
    {"rank": 22, "name": "Stanford University", "total": 973, "opt": 617, "stem_opt": 541},
    {"rank": 24, "name": "University of Illinois", "total": 886, "opt": 714, "stem_opt": 276},
    {"rank": 25, "name": "Columbia University", "total": 854, "opt": 662, "stem_opt": 320},
    {"rank": 26, "name": "Tata Consultancy Services", "total": 851, "opt": 407, "stem_opt": 639},
    {"rank": 27, "name": "NVIDIA", "total": 815, "opt": 599, "stem_opt": 410},
    {"rank": 29, "name": "University of Pennsylvania", "total": 797, "opt": 623, "stem_opt": 314},
    {"rank": 30, "name": "University of Southern California", "total": 796, "opt": 717, "stem_opt": 171},
    {"rank": 31, "name": "Infosys Limited", "total": 788, "opt": 531, "stem_opt": 409},
    {"rank": 32, "name": "Qualcomm", "total": 713, "opt": 467, "stem_opt": 455},
    {"rank": 33, "name": "Boston Consulting Group", "total": 699, "opt": 445, "stem_opt": 412},
    {"rank": 35, "name": "University of Maryland", "total": 680, "opt": 553, "stem_opt": 214},
    {"rank": 36, "name": "Massachusetts Institute of Technology", "total": 673, "opt": 418, "stem_opt": 390},
    {"rank": 37, "name": "Citigroup", "total": 667, "opt": 326, "stem_opt": 517},
    {"rank": 38, "name": "Oracle", "total": 665, "opt": 382, "stem_opt": 445},
    {"rank": 39, "name": "Yale University", "total": 648, "opt": 468, "stem_opt": 303},
    {"rank": 40, "name": "University of Florida", "total": 640, "opt": 520, "stem_opt": 219},
    {"rank": 42, "name": "New York University", "total": 627, "opt": 626, "stem_opt": 1},
    {"rank": 43, "name": "Barclays", "total": 607, "opt": 471, "stem_opt": 406},
    {"rank": 44, "name": "CVS", "total": 598, "opt": 461, "stem_opt": 267},
    {"rank": 45, "name": "Bloomberg", "total": 596, "opt": 426, "stem_opt": 456},
    {"rank": 48, "name": "Cummins", "total": 571, "opt": 357, "stem_opt": 410},
    {"rank": 49, "name": "Bank of America", "total": 558, "opt": 400, "stem_opt": 299},
    {"rank": 50, "name": "Indiana University", "total": 550, "opt": 486, "stem_opt": 142},
    {"rank": 51, "name": "Texas A&M University", "total": 550, "opt": 429, "stem_opt": 187},
    {"rank": 52, "name": "Fidelity Investments", "total": 548, "opt": 342, "stem_opt": 377},
    {"rank": 53, "name": "Capital One", "total": 546, "opt": 292, "stem_opt": 345},
    {"rank": 55, "name": "University of Washington", "total": 532, "opt": 403, "stem_opt": 210},
    {"rank": 56, "name": "Northwestern University", "total": 527, "opt": 378, "stem_opt": 250},
    {"rank": 57, "name": "Morgan Stanley", "total": 511, "opt": 327, "stem_opt": 300},
    {"rank": 59, "name": "HCL Technologies", "total": 486, "opt": 315, "stem_opt": 277},
    {"rank": 60, "name": "University of North Carolina", "total": 483, "opt": 381, "stem_opt": 184},
    {"rank": 61, "name": "University of Chicago", "total": 474, "opt": 467, "stem_opt": 14},
    {"rank": 64, "name": "Advanced Micro Devices", "total": 465, "opt": 365, "stem_opt": 210},
    {"rank": 65, "name": "University of Minnesota", "total": 462, "opt": 352, "stem_opt": 182},
    {"rank": 68, "name": "PricewaterhouseCoopers", "total": 450, "opt": 271, "stem_opt": 273},
    {"rank": 69, "name": "Salesforce", "total": 449, "opt": 279, "stem_opt": 305},
    {"rank": 73, "name": "Applied Materials", "total": 439, "opt": 244, "stem_opt": 293},
    {"rank": 75, "name": "Cisco Systems", "total": 424, "opt": 230, "stem_opt": 289},
    {"rank": 76, "name": "Cornell University", "total": 423, "opt": 352, "stem_opt": 125},
    {"rank": 77, "name": "Purdue University", "total": 422, "opt": 323, "stem_opt": 157},
    {"rank": 78, "name": "Carnegie Mellon University", "total": 416, "opt": 416, "stem_opt": 0},
    {"rank": 79, "name": "Boston University", "total": 415, "opt": 342, "stem_opt": 131},
    {"rank": 80, "name": "Capgemini", "total": 413, "opt": 261, "stem_opt": 253},
    {"rank": 81, "name": "Duke University", "total": 403, "opt": 308, "stem_opt": 170},
    {"rank": 84, "name": "Northeastern University", "total": 399, "opt": 328, "stem_opt": 121},
    {"rank": 85, "name": "North Carolina State University", "total": 397, "opt": 340, "stem_opt": 108},
    {"rank": 89, "name": "Hewlett Packard", "total": 392, "opt": 301, "stem_opt": 222},
    {"rank": 90, "name": "Cognizant", "total": 388, "opt": 253, "stem_opt": 258},
    {"rank": 92, "name": "Micron Technology", "total": 376, "opt": 229, "stem_opt": 199},
    {"rank": 93, "name": "University of Utah", "total": 370, "opt": 302, "stem_opt": 124},
    {"rank": 94, "name": "Eli Lilly and Company", "total": 370, "opt": 258, "stem_opt": 227},
    {"rank": 95, "name": "University of Pittsburgh", "total": 362, "opt": 296, "stem_opt": 116},
    {"rank": 97, "name": "Emory University", "total": 353, "opt": 282, "stem_opt": 139},
    {"rank": 98, "name": "Adobe", "total": 351, "opt": 239, "stem_opt": 196},
    {"rank": 100, "name": "Bain & Company", "total": 346, "opt": 246, "stem_opt": 218},
    {"rank": 101, "name": "Rutgers University", "total": 345, "opt": 276, "stem_opt": 113},
    {"rank": 103, "name": "Georgia Institute of Technology", "total": 344, "opt": 278, "stem_opt": 116},
    {"rank": 104, "name": "Ohio State University", "total": 344, "opt": 258, "stem_opt": 137},
    {"rank": 105, "name": "University of Colorado", "total": 338, "opt": 254, "stem_opt": 139},
    {"rank": 106, "name": "Uber Technologies", "total": 338, "opt": 222, "stem_opt": 204},
    {"rank": 108, "name": "BlackRock", "total": 333, "opt": 208, "stem_opt": 222},
    {"rank": 110, "name": "ServiceNow", "total": 327, "opt": 254, "stem_opt": 170},
    {"rank": 111, "name": "Visa Inc", "total": 326, "opt": 143, "stem_opt": 250},
    {"rank": 113, "name": "Dell", "total": 321, "opt": 218, "stem_opt": 191},
    {"rank": 115, "name": "PayPal", "total": 318, "opt": 212, "stem_opt": 179},
    {"rank": 117, "name": "AECOM", "total": 315, "opt": 227, "stem_opt": 207},
    {"rank": 119, "name": "Discover Financial Services", "total": 314, "opt": 218, "stem_opt": 221},
    {"rank": 121, "name": "Pennsylvania State University", "total": 313, "opt": 247, "stem_opt": 105},
    {"rank": 123, "name": "Siemens", "total": 301, "opt": 220, "stem_opt": 162},
    {"rank": 127, "name": "University of Arizona", "total": 288, "opt": 236, "stem_opt": 93},
    {"rank": 132, "name": "FedEx", "total": 274, "opt": 193, "stem_opt": 136},
    {"rank": 133, "name": "Intuit", "total": 274, "opt": 172, "stem_opt": 192},
    {"rank": 137, "name": "Vanderbilt University", "total": 268, "opt": 188, "stem_opt": 131},
    {"rank": 140, "name": "IBM", "total": 267, "opt": 157, "stem_opt": 187},
    {"rank": 146, "name": "ADP", "total": 254, "opt": 183, "stem_opt": 177},
    {"rank": 147, "name": "MathWorks", "total": 252, "opt": 150, "stem_opt": 202},
    {"rank": 154, "name": "Merck", "total": 244, "opt": 165, "stem_opt": 151},
    {"rank": 165, "name": "American Express", "total": 226, "opt": 131, "stem_opt": 149},
    {"rank": 167, "name": "Thermo Fisher Scientific", "total": 220, "opt": 90, "stem_opt": 166},
    {"rank": 172, "name": "California Institute of Technology", "total": 218, "opt": 127, "stem_opt": 139},
    {"rank": 174, "name": "Rivian Automotive", "total": 217, "opt": 122, "stem_opt": 150},
    {"rank": 176, "name": "UBS", "total": 210, "opt": 114, "stem_opt": 148},
    {"rank": 177, "name": "Expedia Group", "total": 210, "opt": 90, "stem_opt": 175},
    {"rank": 179, "name": "Wayfair", "total": 206, "opt": 147, "stem_opt": 110},
    {"rank": 180, "name": "SAP", "total": 206, "opt": 142, "stem_opt": 109},
    {"rank": 181, "name": "Amgen", "total": 204, "opt": 110, "stem_opt": 135},
    {"rank": 185, "name": "Texas Instruments", "total": 201, "opt": 158, "stem_opt": 125},
    {"rank": 186, "name": "Deutsche Bank", "total": 201, "opt": 143, "stem_opt": 118},
    {"rank": 196, "name": "Ford Motor Company", "total": 196, "opt": 140, "stem_opt": 124},
    {"rank": 197, "name": "Wells Fargo", "total": 196, "opt": 136, "stem_opt": 113},
]

async def import_opt_employers():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("📊 Importing OPT/STEM OPT Employers...")
    
    # Update existing companies with OPT data
    updated = 0
    created = 0
    
    for employer in OPT_EMPLOYERS:
        # Try to find existing company
        existing = await db.companies.find_one(
            {"name": {"$regex": employer['name'], "$options": "i"}}
        )
        
        if existing:
            # Update with OPT data
            await db.companies.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "opt_total": employer['total'],
                    "opt_students": employer['opt'],
                    "stem_opt_students": employer['stem_opt'],
                    "opt_rank": employer['rank'],
                    "supports_opt": True,
                    "supports_stem_opt": employer['stem_opt'] > 0
                }}
            )
            updated += 1
        else:
            # Create new company
            await db.companies.insert_one({
                "company_id": f"opt_{employer['rank']}",
                "name": employer['name'],
                "opt_total": employer['total'],
                "opt_students": employer['opt'],
                "stem_opt_students": employer['stem_opt'],
                "opt_rank": employer['rank'],
                "supports_opt": True,
                "supports_stem_opt": employer['stem_opt'] > 0,
                "h1b_approvals": 0,
                "h1b_denials": 0
            })
            created += 1
    
    print(f"✅ OPT Employers imported:")
    print(f"   Updated: {updated}")
    print(f"   Created: {created}")
    
    # Stats
    total_opt = await db.companies.count_documents({"supports_opt": True})
    total_stem = await db.companies.count_documents({"supports_stem_opt": True})
    
    print(f"\n📊 Database totals:")
    print(f"   OPT companies: {total_opt}")
    print(f"   STEM OPT companies: {total_stem}")

if __name__ == "__main__":
    asyncio.run(import_opt_employers())
