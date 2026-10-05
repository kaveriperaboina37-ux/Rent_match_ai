from dotenv import load_dotenv
load_dotenv()

import json, os, uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr

from db import get_conn, init_db
from auth import hash_password, verify_password, make_token, read_token
from agent import run_agent, AREAS

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="RentMatch AI", version="5.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# A broad Hyderabad rental knowledge base. These are starter listings for the application;
# owner-created listings are persisted in the same database and appear alongside them.
PROPERTY_SEED = [
(1,"Lakeview Residency","KPHB",17500,2,1.8,1,1,1,2,["Lift","24x7 Water","Security","Balcony"],"/images/flat1.svg",["/images/flat1.svg","/images/flat3.svg"],"Ananya Rao","+91 90000 10001","ananya@rentmatch.in",17.4847,78.3930,"Bright 2 BHK apartment near KPHB metro with balcony and reliable water supply."),
(2,"Metro Nest","KPHB",14500,1,2.2,0,1,1,1,["Lift","Security","Power Backup"],"/images/flat2.svg",["/images/flat2.svg"],"Rahul Mehta","+91 90000 10002","rahul@rentmatch.in",17.4880,78.3975,"Budget-friendly 1 BHK with parking and internet connectivity."),
(3,"Urban Heights","KPHB",19500,2,1.2,1,1,0,2,["Gym","Lift","Security","Balcony"],"/images/flat3.svg",["/images/flat3.svg","/images/flat1.svg"],"Priya Sharma","+91 90000 10003","priya@rentmatch.in",17.4920,78.4010,"Furnished 2 BHK with gym access and a large balcony."),
(4,"Miyapur Green Homes","Miyapur",16000,2,2.5,1,1,1,2,["Lift","Garden","Security"],"/images/flat4.svg",["/images/flat4.svg"],"Arjun Kumar","+91 90000 10004","arjun@rentmatch.in",17.4968,78.3565,"Family-friendly 2 BHK in a gated community with garden."),
(5,"Madhapur Central","Madhapur",15500,1,1.0,1,1,1,1,["Lift","Security","Metro Access"],"/images/flat5.svg",["/images/flat5.svg"],"Neha Singh","+91 90000 10005","neha@rentmatch.in",17.4483,78.3915,"Compact furnished 1 BHK close to offices and metro access."),
(6,"Kondapur Comfort","Kondapur",23000,2,1.6,1,1,1,2,["Gym","Pool","Lift","Security"],"/images/flat6.svg",["/images/flat6.svg","/images/flat3.svg"],"Vikram Reddy","+91 90000 10006","vikram@rentmatch.in",17.4580,78.3700,"Premium furnished 2 BHK with pool and gym."),
(7,"Gachibowli Park View","Gachibowli",21000,2,2.0,0,1,1,2,["Gym","Lift","Security"],"/images/flat7.svg",["/images/flat7.svg"],"Sanjay Das","+91 90000 10007","sanjay@rentmatch.in",17.4400,78.3480,"Spacious 2 BHK near major IT campuses."),
(8,"Hitech City Studio","Hitech City",14000,1,1.4,1,0,1,1,["Lift","Security","Power Backup"],"/images/flat8.svg",["/images/flat8.svg"],"Meera Nair","+91 90000 10008","meera@rentmatch.in",17.4474,78.3762,"Furnished 1 BHK near Hitech City offices."),
(9,"KPHB Family Square","KPHB",18000,2,1.5,0,1,1,2,["Lift","Parking","Security","Balcony"],"/images/flat1.svg",["/images/flat1.svg"],"Karthik Rao","+91 90000 10009","karthik@rentmatch.in",17.4860,78.3900,"Well-maintained 2 BHK suited for small families."),
(10,"KPHB Pearl Homes","KPHB",17000,2,2.0,1,1,1,2,["Lift","Security","Wi-Fi","Balcony"],"/images/flat3.svg",["/images/flat3.svg"],"Divya Nair","+91 90000 10010","divya@rentmatch.in",17.4800,78.3990,"Fully furnished 2 BHK with Wi-Fi and reserved parking."),
(11,"Madhapur WorkNest","Madhapur",22000,2,1.3,1,1,1,2,["Lift","Co-working","Security","Wi-Fi"],"/images/flat5.svg",["/images/flat5.svg"],"Rohan Verma","+91 90000 10011","rohan@rentmatch.in",17.4520,78.3880,"Furnished 2 BHK designed for working professionals."),
(12,"Kondapur Garden View","Kondapur",18500,2,2.1,0,1,1,2,["Garden","Lift","Security","Parking"],"/images/flat4.svg",["/images/flat4.svg"],"Ishita Rao","+91 90000 10012","ishita@rentmatch.in",17.4620,78.3630,"Affordable 2 BHK with garden view and parking."),
(13,"Kukatpally City Homes","Kukatpally",13500,1,2.4,0,1,1,1,["Lift","Security","Water"],"/images/flat2.svg",["/images/flat2.svg"],"Suresh Kumar","+91 90000 10013","suresh@rentmatch.in",17.4849,78.4138,"Value-focused 1 BHK close to Kukatpally shopping areas."),
(14,"Kukatpally Urban Villa","Kukatpally",19500,2,2.0,1,1,1,2,["Lift","Balcony","Security","Wi-Fi"],"/images/flat6.svg",["/images/flat6.svg"],"Asha Reddy","+91 90000 10014","asha@rentmatch.in",17.4930,78.4100,"Modern furnished 2 BHK with parking and Wi-Fi."),
(15,"Nizampet Lake Homes","Nizampet",15000,2,3.1,0,1,1,2,["Lift","Parking","Security","Lake View"],"/images/flat4.svg",["/images/flat4.svg"],"Manoj Rao","+91 90000 10015","manoj@rentmatch.in",17.5180,78.3770,"Quiet 2 BHK with parking and open surroundings."),
(16,"Bachupally Family Nest","Bachupally",14500,2,4.8,0,1,1,2,["Security","Garden","Power Backup"],"/images/flat7.svg",["/images/flat7.svg"],"Lavanya R","+91 90000 10016","lavanya@rentmatch.in",17.5500,78.3710,"Family-oriented 2 BHK in a growing residential zone."),
(17,"Hafeezpet Metro Homes","Hafeezpet",16500,2,2.8,1,1,1,2,["Lift","Metro Access","Security","Wi-Fi"],"/images/flat5.svg",["/images/flat5.svg"],"Nikhil Jain","+91 90000 10017","nikhil@rentmatch.in",17.4860,78.3660,"Furnished 2 BHK with easy metro and road access."),
(18,"Manikonda Lake View","Manikonda",18500,2,4.1,1,1,1,2,["Lift","Gym","Security","Balcony"],"/images/flat6.svg",["/images/flat6.svg"],"Pooja Menon","+91 90000 10018","pooja@rentmatch.in",17.4010,78.3750,"Furnished 2 BHK in a peaceful Manikonda community."),
(19,"Moosapet Transit Homes","Moosapet",12500,1,3.0,0,1,1,1,["Metro Access","Security","Water"],"/images/flat2.svg",["/images/flat2.svg"],"Ravi Teja","+91 90000 10019","ravi@rentmatch.in",17.4680,78.4250,"Affordable 1 BHK with strong public transport connectivity."),
(20,"Ameerpet Prime Stay","Ameerpet",15000,1,4.5,1,0,1,1,["Metro Access","Lift","Security"],"/images/flat8.svg",["/images/flat8.svg"],"Kavya Shah","+91 90000 10020","kavya@rentmatch.in",17.4375,78.4483,"Furnished 1 BHK near Ameerpet metro and coaching hubs."),
(21,"Begumpet Garden Residence","Begumpet",20000,2,5.0,1,1,1,2,["Lift","Garden","Security","Wi-Fi"],"/images/flat1.svg",["/images/flat1.svg"],"Aditya Rao","+91 90000 10021","aditya@rentmatch.in",17.4435,78.4625,"Furnished 2 BHK in a central residential pocket."),
(22,"Jubilee Hills Signature","Jubilee Hills",32000,3,5.8,1,1,1,3,["Lift","Gym","Security","Balcony"],"/images/flat6.svg",["/images/flat6.svg"],"Sonia Kapoor","+91 90000 10022","sonia@rentmatch.in",17.4320,78.4070,"Spacious 3 BHK with premium amenities and parking."),
(23,"Hitech City Executive Home","Hitech City",26000,2,1.0,1,1,1,2,["Lift","Gym","Co-working","Wi-Fi"],"/images/flat7.svg",["/images/flat7.svg"],"Arun Patel","+91 90000 10023","arun@rentmatch.in",17.4490,78.3830,"Premium furnished 2 BHK for IT professionals."),
(24,"Miyapur Budget Corner","Miyapur",12000,1,2.9,0,0,1,1,["Security","Water","Wi-Fi"],"/images/flat8.svg",["/images/flat8.svg"],"Deepa Rao","+91 90000 10024","deepa@rentmatch.in",17.5050,78.3550,"Affordable 1 BHK with internet and essential utilities."),
(25,"Skyline Residency","Andheri West, Mumbai",28000,2,2.0,1,1,1,2,["Lift","Security","Metro Access","Balcony"],"/images/flat1.svg",["/images/flat1.svg","/images/flat3.svg"],"Riya Shah","+91 90000 10025","riya@rentmatch.in",19.1364,72.8296,"Modern 2 BHK close to metro and everyday conveniences."),
(26,"Powai Lake Homes","Powai, Mumbai",42000,2,1.5,1,1,1,2,["Lake View","Gym","Lift","Security"],"/images/flat6.svg",["/images/flat6.svg","/images/flat1.svg"],"Amit Mehra","+91 90000 10026","amit@rentmatch.in",19.1176,72.9060,"Premium furnished apartment near Powai Lake."),
(27,"Bandra Urban Nest","Bandra West, Mumbai",52000,3,1.2,1,1,1,3,["Gym","Lift","Parking","Security"],"/images/flat7.svg",["/images/flat7.svg"],"Nisha Kapoor","+91 90000 10027","nisha@rentmatch.in",19.0607,72.8362,"Spacious 3 BHK in a premium residential neighbourhood."),
(28,"Koramangala Comfort","Koramangala, Bengaluru",26000,2,1.4,1,1,1,2,["Lift","Wi-Fi","Security","Balcony"],"/images/flat3.svg",["/images/flat3.svg"],"Kiran Rao","+91 90000 10028","kiran@rentmatch.in",12.9352,77.6245,"Furnished 2 BHK near tech offices, cafes and transit."),
(29,"Whitefield Heights","Whitefield, Bengaluru",24000,2,2.3,1,1,1,2,["Gym","Pool","Lift","Security"],"/images/flat6.svg",["/images/flat6.svg"],"Megha Nair","+91 90000 10029","megha@rentmatch.in",12.9698,77.7499,"Gated community apartment close to IT parks."),
(30,"Indiranagar Studio","Indiranagar, Bengaluru",19000,1,1.0,1,0,1,1,["Metro Access","Lift","Wi-Fi"],"/images/flat8.svg",["/images/flat8.svg"],"Arjun Rao","+91 90000 10030","arjun@rentmatch.in",12.9784,77.6408,"Furnished 1 BHK with excellent metro connectivity."),
(31,"Salt Lake Smart Home","Salt Lake, Kolkata",18000,2,2.0,1,1,1,2,["Lift","Security","Parking","Balcony"],"/images/flat4.svg",["/images/flat4.svg"],"Soham Das","+91 90000 10031","soham@rentmatch.in",22.5726,88.4131,"Comfortable 2 BHK in a well-connected residential area."),
(32,"New Town Green View","New Town, Kolkata",15500,2,3.0,0,1,1,2,["Garden","Security","Power Backup"],"/images/flat7.svg",["/images/flat7.svg"],"Mita Roy","+91 90000 10032","mita@rentmatch.in",22.5875,88.4840,"Affordable family apartment near offices and transit."),
(33,"Anna Nagar Prime","Anna Nagar, Chennai",22000,2,1.7,1,1,1,2,["Lift","Parking","Security","Balcony"],"/images/flat1.svg",["/images/flat1.svg"],"Priya Iyer","+91 90000 10033","priya@rentmatch.in",13.0878,80.2080,"Furnished 2 BHK with parking and city access."),
(34,"OMR Tech Homes","OMR, Chennai",17000,2,2.6,0,1,1,2,["Security","Wi-Fi","Power Backup"],"/images/flat5.svg",["/images/flat5.svg"],"Vijay Kumar","+91 90000 10034","vijay@rentmatch.in",12.9150,80.2300,"Budget-friendly 2 BHK near technology parks."),
(35,"Hinjewadi Tech Park Home","Hinjewadi, Pune",19000,2,2.0,1,1,1,2,["Gym","Lift","Security","Wi-Fi"],"/images/flat6.svg",["/images/flat6.svg"],"Sneha Patil","+91 90000 10035","sneha@rentmatch.in",18.5913,73.7389,"Furnished 2 BHK near Hinjewadi technology parks."),
(36,"Kharadi Garden Flat","Kharadi, Pune",21000,2,1.8,1,1,1,2,["Garden","Lift","Parking","Security"],"/images/flat4.svg",["/images/flat4.svg"],"Rahul Patil","+91 90000 10036","rahul@rentmatch.in",18.5511,73.9470,"Modern gated-community flat close to offices."),
(37,"Gurgaon Golf Course Home","Golf Course Road, Gurugram",32000,2,1.5,1,1,1,2,["Gym","Pool","Lift","Security"],"/images/flat7.svg",["/images/flat7.svg"],"Neeraj Singh","+91 90000 10037","neeraj@rentmatch.in",28.4595,77.0720,"Premium 2 BHK with strong corporate connectivity."),
(38,"Noida Sector 62 Nest","Sector 62, Noida",23000,2,2.0,0,1,1,2,["Metro Access","Lift","Security","Parking"],"/images/flat2.svg",["/images/flat2.svg"],"Ankit Verma","+91 90000 10038","ankit@rentmatch.in",28.6270,77.3648,"Well-connected 2 BHK near offices and metro."),
(39,"Dwarka Family Home","Dwarka, New Delhi",26000,2,2.5,0,1,1,2,["Metro Access","Lift","Security","Balcony"],"/images/flat1.svg",["/images/flat1.svg"],"Pooja Sharma","+91 90000 10039","pooja@rentmatch.in",28.5921,77.0460,"Family-friendly apartment with excellent metro access."),
(40,"Indirapuram City View","Indirapuram, Ghaziabad",18000,2,2.2,0,1,1,2,["Lift","Security","Parking","Power Backup"],"/images/flat3.svg",["/images/flat3.svg"],"Rakesh Gupta","+91 90000 10040","rakesh@rentmatch.in",28.6412,77.3715,"Value-focused 2 BHK in a connected residential community."),
(41,"Gomti Nagar Modern Flat","Gomti Nagar, Lucknow",16000,2,2.8,1,1,1,2,["Lift","Security","Balcony","Wi-Fi"],"/images/flat5.svg",["/images/flat5.svg"],"Aarav Singh","+91 90000 10041","aarav@rentmatch.in",26.8467,81.0078,"Furnished 2 BHK near offices and shopping."),
(42,"Banjara Hills City Home","Banjara Hills, Hyderabad",28000,2,1.8,1,1,1,2,["Gym","Lift","Security","Parking"],"/images/flat6.svg",["/images/flat6.svg"],"Meghana Reddy","+91 90000 10042","meghana@rentmatch.in",17.4156,78.4347,"Premium 2 BHK in central Hyderabad."),
(43,"Panampilly Nagar Residence","Panampilly Nagar, Kochi",23000,2,2.0,1,1,1,2,["Lift","Security","Parking","Balcony"],"/images/flat4.svg",["/images/flat4.svg"],"Anu Thomas","+91 90000 10043","anu@rentmatch.in",9.9658,76.2920,"Furnished 2 BHK in a popular residential area."),
(44,"Viman Nagar Smart Flat","Viman Nagar, Pune",20000,1,1.5,1,1,1,1,["Lift","Security","Wi-Fi","Parking"],"/images/flat8.svg",["/images/flat8.svg"],"Rohit Kulkarni","+91 90000 10044","rohit@rentmatch.in",18.5679,73.9143,"Furnished 1 BHK close to airport and business hubs."),
(45,"Thane West Family Home","Thane West, Thane",24000,2,2.1,0,1,1,2,["Lift","Garden","Security","Parking"],"/images/flat1.svg",["/images/flat1.svg"],"Sonal Jain","+91 90000 10045","sonal@rentmatch.in",19.2183,72.9781,"Spacious 2 BHK in a family-friendly neighbourhood."),
(46,"Sector 17 Executive Flat","Sector 17, Chandigarh",22000,2,1.9,1,1,1,2,["Lift","Security","Balcony","Wi-Fi"],"/images/flat3.svg",["/images/flat3.svg"],"Harpreet Kaur","+91 90000 10046","harpreet@rentmatch.in",30.7333,76.7794,"Furnished 2 BHK near central Chandigarh."),
(47,"Vastrapur Lake Home","Vastrapur, Ahmedabad",17000,2,2.0,0,1,1,2,["Lake View","Lift","Security","Parking"],"/images/flat4.svg",["/images/flat4.svg"],"Dhruv Shah","+91 90000 10047","dhruv@rentmatch.in",23.0395,72.5293,"Comfortable 2 BHK near Vastrapur Lake and metro."),
(48,"Boring Road Residence","Boring Road, Patna",13000,2,2.5,0,1,1,2,["Security","Parking","Water"],"/images/flat2.svg",["/images/flat2.svg"],"Neha Kumari","+91 90000 10048","neha@rentmatch.in",25.6100,85.1235,"Affordable 2 BHK in a central Patna neighbourhood."),
(49,"Rajaji Nagar Comfort","Rajajinagar, Bengaluru",21000,2,2.0,0,1,1,2,["Metro Access","Lift","Security","Parking"],"/images/flat5.svg",["/images/flat5.svg"],"Manish Rao","+91 90000 10049","manish@rentmatch.in",13.0108,77.5548,"Connected 2 BHK close to metro and daily amenities."),
(50,"Vaishali Nagar Home","Vaishali Nagar, Jaipur",15000,2,2.5,0,1,1,2,["Security","Parking","Balcony","Water"],"/images/flat7.svg",["/images/flat7.svg"],"Kunal Sharma","+91 90000 10050","kunal@rentmatch.in",26.9124,75.7488,"Value-focused 2 BHK in a popular Jaipur locality.")
]

AREA_CENTERS = {
    "Ameerpet": (17.4375,78.4483), "Bachupally": (17.5500,78.3710), "Begumpet": (17.4435,78.4625),
    "Gachibowli": (17.4400,78.3480), "Hafeezpet": (17.4860,78.3660), "Hitech City": (17.4490,78.3830),
    "Jubilee Hills": (17.4320,78.4070), "Kondapur": (17.4580,78.3700), "KPHB": (17.4847,78.3930),
    "Kukatpally": (17.4930,78.4100), "Madhapur": (17.4483,78.3915), "Manikonda": (17.4010,78.3750),
    "Miyapur": (17.4968,78.3565), "Moosapet": (17.4680,78.4250), "Nizampet": (17.5180,78.3770),
    "Andheri West, Mumbai": (19.1364,72.8296), "Powai, Mumbai": (19.1176,72.9060), "Bandra West, Mumbai": (19.0607,72.8362),
    "Koramangala, Bengaluru": (12.9352,77.6245), "Whitefield, Bengaluru": (12.9698,77.7499), "Indiranagar, Bengaluru": (12.9784,77.6408), "Rajajinagar, Bengaluru": (13.0108,77.5548),
    "Salt Lake, Kolkata": (22.5726,88.4131), "New Town, Kolkata": (22.5875,88.4840),
    "Anna Nagar, Chennai": (13.0878,80.2080), "OMR, Chennai": (12.9150,80.2300),
    "Hinjewadi, Pune": (18.5913,73.7389), "Kharadi, Pune": (18.5511,73.9470), "Viman Nagar, Pune": (18.5679,73.9143),
    "Golf Course Road, Gurugram": (28.4595,77.0720), "Sector 62, Noida": (28.6270,77.3648), "Dwarka, New Delhi": (28.5921,77.0460),
    "Indirapuram, Ghaziabad": (28.6412,77.3715), "Gomti Nagar, Lucknow": (26.8467,81.0078),
    "Banjara Hills, Hyderabad": (17.4156,78.4347), "Panampilly Nagar, Kochi": (9.9658,76.2920),
    "Thane West, Thane": (19.2183,72.9781), "Sector 17, Chandigarh": (30.7333,76.7794), "Vastrapur, Ahmedabad": (23.0395,72.5293),
    "Boring Road, Patna": (25.6100,85.1235), "Vaishali Nagar, Jaipur": (26.9124,75.7488)
}

def seed():
    init_db()
    conn = get_conn()
    # Seed the built-in catalog on a fresh install and add any newer catalog
    # records when upgrading an older database. Owner-created listings are preserved.
    for p in PROPERTY_SEED:
        (pid,title,area,rent,bhk,dist,furn,park,wifi,bath,amenities,image,gallery,oname,ophone,oemail,lat,lng,desc)=p
        conn.execute("""INSERT OR IGNORE INTO properties
        (id,title,area,rent,bhk,distance_km,furnished,parking,wifi,bathrooms,amenities_json,image,gallery_json,owner_name,owner_phone,owner_email,lat,lng,description)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pid,title,area,rent,bhk,dist,furn,park,wifi,bath,json.dumps(amenities),image,json.dumps(gallery),oname,ophone,oemail,lat,lng,desc))
    conn.commit()
    conn.close()

seed()

def row_to_property(row):
    d = dict(row)
    for key in ["furnished", "parking", "wifi"]:
        d[key] = bool(d[key])
    d["amenities"] = json.loads(d.pop("amenities_json") or "[]")
    gallery = json.loads(d.pop("gallery_json") or "[]")
    if d.get("image") and d["image"] not in gallery:
        gallery.insert(0, d["image"])
    d["gallery"] = gallery
    d["owner"] = {"name": d.pop("owner_name"), "phone": d.pop("owner_phone"), "email": d.pop("owner_email")}
    return d

def current_user(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Login required")
    try:
        uid = read_token(authorization.split(" ",1)[1])
    except Exception:
        raise HTTPException(401, "Invalid or expired session")
    conn = get_conn(); row = conn.execute("SELECT id,name,email,role FROM users WHERE id=?", (uid,)).fetchone(); conn.close()
    if not row: raise HTTPException(401, "User not found")
    return dict(row)

def owner_user(authorization):
    user = current_user(authorization)
    if user["role"] != "owner":
        raise HTTPException(403, "Owner account required. Create an account with Owner selected to publish a property.")
    return user

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "tenant"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SearchRequest(BaseModel):
    query: str

class FavoriteRequest(BaseModel):
    property_id: int

@app.get("/api/health")
def health():
    return {"status":"ok","service":"RentMatch AI","database":"SQLite","gemini_configured":bool(os.getenv("GEMINI_API_KEY","" ).strip())}

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if len(req.password) < 6: raise HTTPException(400, "Password must contain at least 6 characters")
    role = "owner" if req.role == "owner" else "tenant"
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)", (req.name.strip(), req.email.lower(), hash_password(req.password), role))
        conn.commit(); uid = cur.lastrowid
    except Exception as e:
        conn.close()
        if "UNIQUE" in str(e).upper(): raise HTTPException(409, "An account with this email already exists")
        raise HTTPException(400, "Could not create account")
    conn.close()
    return {"token": make_token(uid), "user": {"id": uid, "name": req.name.strip(), "email": req.email.lower(), "role": role}}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_conn(); row = conn.execute("SELECT id,name,email,password_hash,role FROM users WHERE email=?", (req.email.lower(),)).fetchone(); conn.close()
    if not row or not verify_password(req.password, row["password_hash"]): raise HTTPException(401, "Invalid email or password")
    return {"token": make_token(row["id"]), "user": {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"]}}

@app.get("/api/auth/me")
def me(authorization: Optional[str] = Header(default=None)):
    return {"user": current_user(authorization)}

@app.get("/api/areas")
def areas():
    conn = get_conn(); rows = conn.execute("SELECT DISTINCT area FROM properties ORDER BY area").fetchall(); conn.close()
    return {"areas":[r["area"] for r in rows]}

@app.get("/api/properties")
def properties():
    conn = get_conn(); rows = conn.execute("SELECT * FROM properties WHERE status='available' ORDER BY created_at DESC, area, rent").fetchall(); conn.close()
    return {"properties":[row_to_property(r) for r in rows]}

@app.get("/api/properties/{property_id}")
def property_details(property_id: int):
    conn=get_conn(); row=conn.execute("SELECT * FROM properties WHERE id=?",(property_id,)).fetchone(); conn.close()
    if not row: raise HTTPException(404,"Property not found")
    return {"property":row_to_property(row)}

@app.post("/api/search")
def search(req: SearchRequest, authorization: Optional[str] = Header(default=None)):
    user = current_user(authorization)
    conn = get_conn(); rows = conn.execute("SELECT * FROM properties WHERE status='available'").fetchall(); props = [row_to_property(r) for r in rows]
    result = run_agent(req.query, props)
    conn.execute("INSERT INTO searches(user_id,query,requirements_json) VALUES(?,?,?)", (user["id"], req.query, json.dumps(result["requirements"])))
    conn.commit(); conn.close()
    result["query"] = req.query; result["strict_area"] = bool(result["requirements"].get("area")); result["total"] = len(result["results"])
    return result

@app.get("/api/favorites")
def get_favorites(authorization: Optional[str] = Header(default=None)):
    user=current_user(authorization); conn=get_conn(); rows=conn.execute("SELECT p.* FROM properties p JOIN favorites f ON f.property_id=p.id WHERE f.user_id=? ORDER BY f.created_at DESC",(user["id"],)).fetchall(); conn.close()
    return {"properties":[row_to_property(r) for r in rows]}

@app.post("/api/favorites")
def add_favorite(req: FavoriteRequest, authorization: Optional[str] = Header(default=None)):
    user=current_user(authorization); conn=get_conn()
    if not conn.execute("SELECT id FROM properties WHERE id=?",(req.property_id,)).fetchone(): conn.close(); raise HTTPException(404,"Property not found")
    conn.execute("INSERT OR IGNORE INTO favorites(user_id,property_id) VALUES(?,?)",(user["id"],req.property_id)); conn.commit(); conn.close(); return {"status":"saved"}

@app.delete("/api/favorites/{property_id}")
def delete_favorite(property_id:int, authorization: Optional[str] = Header(default=None)):
    user=current_user(authorization); conn=get_conn(); conn.execute("DELETE FROM favorites WHERE user_id=? AND property_id=?",(user["id"],property_id)); conn.commit(); conn.close(); return {"status":"removed"}

@app.get("/api/history")
def history(authorization: Optional[str] = Header(default=None)):
    user=current_user(authorization); conn=get_conn(); rows=conn.execute("SELECT id,query,requirements_json,created_at FROM searches WHERE user_id=? ORDER BY id DESC LIMIT 30",(user["id"],)).fetchall(); conn.close()
    return {"history":[{"id":r["id"],"query":r["query"],"requirements":json.loads(r["requirements_json"]),"created_at":r["created_at"]} for r in rows]}

@app.get("/api/owner/properties")
def owner_properties(authorization: Optional[str] = Header(default=None)):
    user=owner_user(authorization); conn=get_conn(); rows=conn.execute("SELECT * FROM properties WHERE owner_user_id=? ORDER BY id DESC",(user["id"],)).fetchall(); conn.close()
    return {"properties":[row_to_property(r) for r in rows]}

ALLOWED_IMAGE_TYPES={"image/jpeg","image/png","image/webp","image/gif"}

@app.post("/api/owner/properties")
async def create_owner_property(
    title: str = Form(...), area: str = Form(...), rent: int = Form(...), bhk: int = Form(...), bathrooms: int = Form(1),
    furnished: bool = Form(False), parking: bool = Form(False), wifi: bool = Form(False), description: str = Form(...),
    phone: str = Form(...), amenities: str = Form(""), lat: Optional[float] = Form(None), lng: Optional[float] = Form(None),
    files: list[UploadFile] = File(default=[]), authorization: Optional[str] = Header(default=None)
):
    user=owner_user(authorization)
    if area not in AREAS: raise HTTPException(400, "Please choose a supported Indian city/locality")
    if rent < 1000 or bhk < 1 or bathrooms < 1: raise HTTPException(400,"Enter valid rent, BHK and bathroom values")
    if not files: raise HTTPException(400,"Upload at least one flat photo")
    if len(files)>8: raise HTTPException(400,"Upload up to 8 photos")
    center=AREA_CENTERS[area]; lat=lat if lat is not None else center[0]; lng=lng if lng is not None else center[1]
    saved=[]
    for f in files:
        if f.content_type not in ALLOWED_IMAGE_TYPES: raise HTTPException(400,"Only JPG, PNG, WEBP or GIF photos are allowed")
        ext=Path(f.filename or "photo.jpg").suffix.lower() or ".jpg"
        name=f"{uuid.uuid4().hex}{ext}"
        target=UPLOAD_DIR/name
        data=await f.read()
        if len(data)>6*1024*1024: raise HTTPException(400,"Each photo must be 6 MB or smaller")
        target.write_bytes(data); saved.append(f"/uploads/{name}")
    amenities_list=[x.strip() for x in amenities.split(",") if x.strip()]
    conn=get_conn()
    cur=conn.execute("""INSERT INTO properties(title,area,rent,bhk,distance_km,furnished,parking,wifi,bathrooms,amenities_json,image,gallery_json,owner_name,owner_phone,owner_email,owner_user_id,lat,lng,description)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (title.strip(),area,rent,bhk,0,bool(furnished),bool(parking),bool(wifi),bathrooms,json.dumps(amenities_list),saved[0],json.dumps(saved),user["name"],phone.strip(),user["email"],user["id"],lat,lng,description.strip()))
    conn.commit(); pid=cur.lastrowid; row=conn.execute("SELECT * FROM properties WHERE id=?",(pid,)).fetchone(); conn.close()
    return {"property":row_to_property(row),"message":"Property published successfully"}

@app.delete("/api/owner/properties/{property_id}")
def delete_owner_property(property_id:int, authorization: Optional[str] = Header(default=None)):
    user=owner_user(authorization); conn=get_conn(); row=conn.execute("SELECT * FROM properties WHERE id=? AND owner_user_id=?",(property_id,user["id"])).fetchone()
    if not row: conn.close(); raise HTTPException(404,"Your property was not found")
    conn.execute("DELETE FROM properties WHERE id=?",(property_id,)); conn.commit(); conn.close(); return {"status":"deleted"}
