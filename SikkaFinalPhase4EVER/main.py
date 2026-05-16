from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, hashlib, os
from datetime import date, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "sikka_heritage_2026_secure"
app.config.update(
    SESSION_COOKIE_HTTPONLY  = True,
    SESSION_COOKIE_SAMESITE  = "Lax",
    PERMANENT_SESSION_LIFETIME = 86400,
)
DB = "sikka.db"

# Passenger-type discount only — base price already reflects class (DB stores correct value)
PRICING = {"adult": 1.0, "child": 0.5}

TR = {
  "en":{
    "app_name":"Sikka","tagline":"Connecting the Kingdom",
    "home":"Home","dashboard":"Dashboard","trains":"Trains",
    "passengers":"Passengers","reservations":"Reservations","reports":"Reports",
    "about":"About Us","help":"Help & Support","logout":"Logout","login":"Sign In",
    "book_now":"Book Now","cancel":"Cancel","save":"Save Changes",
    "add":"Add","edit":"Edit","delete":"Delete",
    "confirmed":"Confirmed","cancelled":"Cancelled",
    "business":"Business Class","economy":"Economy Class",
    "adult":"Adult","child":"Child (−50%)",
    "seat_class":"Seat Class","passenger_type":"Passenger Type",
    "price":"Price (SAR)","base_price":"Base Price",
    "destinations":"Destinations","route_map":"Train Network",
    "welcome":"Travel around Saudi Arabia",
    "welcome_sub":"Book your journey across the Kingdom on Sikka — Saudi Arabia's modern rail experience.",
    "select_train":"Select Train","select_seat":"Select Seat",
    "select_passenger":"Select Passenger","confirm_booking":"Confirm Booking",
    "total_trains":"Active Trains","total_bookings":"Bookings",
    "total_passengers":"Passengers","total_revenue":"Revenue (SAR)",
    "route":"Route","departure":"Departure","arrival":"Arrival",
    "capacity":"Capacity","booked":"Booked","available":"Available",
    "train_name":"Train","actions":"Actions",
    "full_name":"Full Name","national_id":"National ID",
    "email":"Email","phone":"Phone",
    "passenger":"Passenger","seat":"Seat","date":"Date",
    "report_type":"Report Type","date_from":"From","date_to":"To",
    "generate":"Generate","daily":"Daily","monthly":"Monthly",
    "no_data":"No data for the selected period.",
    "new_reservation":"New Booking","add_train":"Add Train",
    "add_passenger":"Add Passenger","my_reservations":"My Bookings",
    "search_title":"Search Trains","from_city":"From",
    "to_city":"To","travel_date":"Travel Date","search_btn":"Search",
    "results_title":"Available Trains",
    "no_results":"No trains found for this route and date.",
    "select_this":"Select","trip_date":"Trip Date",
    "price_paid":"Paid","legend_free":"Available",
    "legend_taken":"Taken","legend_selected":"Selected",
    "username":"Username","password":"Password",
    "signin_sub":"Saudi Arabia's Railway","credentials":"Test Accounts",
    "calc_title":"Price Breakdown",
    "faq_title":"Frequently Asked Questions",
    "faq_book_q":"How do I book a ticket?",
    "faq_book_a":"Log in, go to Book Now, search your route, pick a train, choose class and seat, then confirm.",
    "faq_cancel_q":"Can I cancel my reservation?",
    "faq_cancel_a":"Yes. Go to My Bookings, find the reservation, and click Cancel.",
    "faq_child_q":"What is the child discount?",
    "faq_child_a":"Children receive a 50% discount on both Economy and Business class.",
    "faq_class_q":"What is the difference between Economy and Business?",
    "faq_class_a":"Business Class has wider premium seats and superior service.",
    "faq_id_q":"What ID do I need?",
    "faq_id_a":"A valid Saudi National ID (10 digits, starts with 1 or 2) or Iqama.",
    "policy_title":"Travel Policies",
    "policy_1":"Passengers must arrive at least 15 minutes before departure.",
    "policy_2":"Cancellations are free up to 2 hours before departure.",
    "policy_3":"Children under 2 years travel free on a parent's lap.",
    "policy_4":"No smoking in any train car.",
    "contact_title":"Contact Us","contact_email":"support.sikka@gmail.com",
    "contact_phone":"+966 56 474 5505",
    "about_title":"About Sikka",
    "about_desc":"Sikka is a university project by four CS students at Imam Mohammad Ibn Saud Islamic University, built for CS1350 Software Engineering 1.",
    "about_vision_title":"Our Vision",
    "about_vision":"To create a fast, bilingual, and accessible rail booking platform for the Kingdom, inspired by Vision 2030.",
    "about_team":"Our Team","about_tech":"Built With",
    "manage_schedules":"Manage Dates","avail_dates":"Available Dates",
    "manage_images":"Manage Images",
  },
  "ar":{
    "app_name":"سِكَّة","tagline":"تربط المملكة",
    "home":"الرئيسية","dashboard":"لوحة التحكم","trains":"القطارات",
    "passengers":"المسافرون","reservations":"الحجوزات","reports":"التقارير",
    "about":"من نحن","help":"المساعدة","logout":"خروج","login":"دخول",
    "book_now":"احجز الآن","cancel":"إلغاء","save":"حفظ",
    "add":"إضافة","edit":"تعديل","delete":"حذف",
    "confirmed":"مؤكد","cancelled":"ملغي",
    "business":"درجة رجال الأعمال","economy":"الدرجة الاقتصادية",
    "adult":"بالغ","child":"طفل (−50٪)",
    "seat_class":"درجة المقعد","passenger_type":"نوع المسافر",
    "price":"السعر (ريال)","base_price":"السعر الأساسي",
    "destinations":"الوجهات","route_map":"شبكة القطارات",
    "welcome":"سافر عبر المملكة بأناقة",
    "welcome_sub":"احجز رحلتك عبر المملكة على سِكَّة.",
    "select_train":"اختر القطار","select_seat":"اختر المقعد",
    "select_passenger":"اختر المسافر","confirm_booking":"تأكيد الحجز",
    "total_trains":"القطارات النشطة","total_bookings":"الحجوزات",
    "total_passengers":"المسافرون","total_revenue":"الإيرادات (ريال)",
    "route":"المسار","departure":"المغادرة","arrival":"الوصول",
    "capacity":"السعة","booked":"محجوز","available":"متاح",
    "train_name":"القطار","actions":"الإجراءات",
    "full_name":"الاسم الكامل","national_id":"رقم الهوية",
    "email":"البريد","phone":"الجوال",
    "passenger":"المسافر","seat":"المقعد","date":"التاريخ",
    "report_type":"نوع التقرير","date_from":"من","date_to":"إلى",
    "generate":"إنشاء","daily":"يومي","monthly":"شهري",
    "no_data":"لا توجد بيانات للفترة المحددة.",
    "new_reservation":"حجز جديد","add_train":"إضافة قطار",
    "add_passenger":"إضافة مسافر","my_reservations":"حجوزاتي",
    "search_title":"ابحث عن قطار","from_city":"من",
    "to_city":"إلى","travel_date":"تاريخ السفر","search_btn":"بحث",
    "results_title":"الرحلات المتاحة",
    "no_results":"لا توجد رحلات لهذا المسار في التاريخ المحدد.",
    "select_this":"اختر","trip_date":"تاريخ الرحلة",
    "price_paid":"المدفوع","legend_free":"متاح",
    "legend_taken":"محجوز","legend_selected":"مختار",
    "username":"اسم المستخدم","password":"كلمة المرور",
    "signin_sub":"سكك حديد المملكة","credentials":"حسابات تجريبية",
    "calc_title":"تفاصيل السعر",
    "faq_title":"الأسئلة الشائعة",
    "faq_book_q":"كيف أحجز تذكرة؟",
    "faq_book_a":"سجل دخولك، اذهب إلى البحث، اختر الوجهة والتاريخ، ثم القطار والمقعد.",
    "faq_cancel_q":"هل يمكنني إلغاء الحجز؟",
    "faq_cancel_a":"نعم، اذهب إلى حجوزاتي واضغط إلغاء.",
    "faq_child_q":"ما هو خصم الأطفال؟",
    "faq_child_a":"يحصل الأطفال على خصم 50٪ في جميع الدرجات.",
    "faq_class_q":"ما الفرق بين الدرجتين؟",
    "faq_class_a":"درجة رجال الأعمال أرحب وتوفر خدمة متميزة.",
    "faq_id_q":"ما الهوية المطلوبة؟",
    "faq_id_a":"هوية وطنية سارية (10 أرقام تبدأ بـ 1 أو 2).",
    "policy_title":"سياسات السفر",
    "policy_1":"يجب الوصول قبل 15 دقيقة من المغادرة.",
    "policy_2":"الإلغاء مجاني قبل ساعتين من المغادرة.",
    "policy_3":"الأطفال دون سنتين يسافرون مجاناً.",
    "policy_4":"ممنوع التدخين في جميع عربات القطار.",
    "contact_title":"تواصل معنا","contact_email":"support@sikka.sa",
    "contact_phone":"+966 11 000 0000",
    "about_title":"عن سِكَّة",
    "about_desc":"سِكَّة مشروع جامعي لأربعة طلاب في جامعة الإمام محمد بن سعود الإسلامية لمادة CS1350.",
    "about_vision_title":"رؤيتنا",
    "about_vision":"إنشاء منصة حجز قطارات سريعة وثنائية اللغة مستوحاة من رؤية 2030.",
    "about_team":"فريق العمل","about_tech":"التقنيات المستخدمة",
    "manage_schedules":"إدارة التواريخ","avail_dates":"التواريخ المتاحة",
    "manage_images":"إدارة الصور",
  }
}

CITIES = [
  {"key":"riyadh",  "img":"images/city_riyadh.jpg",  "en_name":"Riyadh",  "ar_name":"الرياض",         "en_desc":"The capital and economic heart of Saudi Arabia.", "ar_desc":"عاصمة المملكة العربية السعودية.","color":"#006C35"},
  {"key":"jeddah",  "img":"images/city_jeddah.jpg",  "en_name":"Jeddah",  "ar_name":"جدة",            "en_desc":"Red Sea port city, home of UNESCO-listed Al-Balad.","ar_desc":"مدينة ساحلية تشتهر بحي البلد التاريخي.","color":"#0D4A6B"},
  {"key":"madinah", "img":"images/city_madinah.jpg", "en_name":"Madinah", "ar_name":"المدينة المنورة", "en_desc":"The second holiest city in Islam.","ar_desc":"ثاني أقدس مدينة في الإسلام.","color":"#5C3A1E"},
  {"key":"mecca",   "img":"images/city_mecca.jpg",   "en_name":"Mecca",   "ar_name":"مكة المكرمة",    "en_desc":"The holiest city in Islam, destination of Hajj.","ar_desc":"أقدس مدينة في الإسلام وقبلة الحج.","color":"#6B3A2A"},
  {"key":"dammam",  "img":"images/city_dammam.jpg",  "en_name":"Dammam",  "ar_name":"الدمام",         "en_desc":"Gateway to the Eastern Province.","ar_desc":"بوابة المنطقة الشرقية.","color":"#3D1F00"},
  {"key":"tabuk",   "img":"images/city_tabuk.jpg",   "en_name":"Tabuk",   "ar_name":"تبوك",           "en_desc":"Northwestern jewel, home of NEOM.","ar_desc":"جوهرة الشمال الغربي ومنطقة نيوم.","color":"#4A3728"},
  {"key":"abha",    "img":"images/city_abha.jpg",    "en_name":"Abha",    "ar_name":"أبها",           "en_desc":"Cool mountain city of Asir Region.","ar_desc":"مدينة الجبال في منطقة عسير.","color":"#1A472A"},
  {"key":"hail",    "img":"images/city_hail.jpg",    "en_name":"Hail",    "ar_name":"حائل",           "en_desc":"Historic city known for ancient rock art.","ar_desc":"مدينة تاريخية تشتهر بنقوشها الصخرية القديمة.","color":"#7B5E2A"},
]

TEAM = [
  {"name":"Naif Alotaibi",   "id":"446001599","role_en":"Team Leader",      "role_ar":"قائد الفريق",          "bio_en":"Project management and system architecture.","bio_ar":"إدارة المشروع والبنية العامة للنظام.","img":"images/member1.jpg"},
  {"name":"Adeeb Alqahtani", "id":"446013621","role_en":"Backend Developer", "role_ar":"مطوّر الواجهة الخلفية", "bio_en":"Database design, Flask routes, and security.","bio_ar":"تصميم قاعدة البيانات ومسارات Flask والأمان.","img":"images/member2.jpg"},
  {"name":"Bader Albader",   "id":"446013730","role_en":"UI/UX Designer",    "role_ar":"مصمم واجهات المستخدم",  "bio_en":"Heritage theme, CSS architecture, and seat map.","bio_ar":"ثيم التراث وبنية CSS وخريطة المقاعد.","img":"images/member3.jpg"},
  {"name":"Nawaf Nawfal",    "id":"446003561","role_en":"QA & Documentation", "role_ar":"ضمان الجودة والتوثيق", "bio_en":"Test cases, documentation, and GitHub management.","bio_ar":"حالات الاختبار والتوثيق وإدارة GitHub.","img":"images/member4.jpg"},
]

SITE_IMAGES = {
  "hero_bg":    "images/hero_bg.jpg",
  "login_bg":   "images/login_bg.jpg",
  "about_hero": "images/about_hero.jpg",
  "map":        "",
}

# ─── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def sha(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = get_db(); c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','staff','customer')),
            full_name TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            national_id TEXT DEFAULT '');

        CREATE TABLE IF NOT EXISTS trains(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            route TEXT NOT NULL,
            departure TEXT NOT NULL,
            arrival TEXT NOT NULL,
            capacity_economy INTEGER NOT NULL DEFAULT 60,
            capacity_business INTEGER NOT NULL DEFAULT 20,
            price_economy REAL NOT NULL,
            price_business REAL NOT NULL,
            status TEXT DEFAULT 'active');

        CREATE TABLE IF NOT EXISTS schedules(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_id INTEGER NOT NULL,
            travel_date TEXT NOT NULL,
            UNIQUE(train_id, travel_date),
            FOREIGN KEY(train_id) REFERENCES trains(id));

        CREATE TABLE IF NOT EXISTS passengers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            national_id TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT,
            created_by INTEGER DEFAULT NULL,
            FOREIGN KEY(created_by) REFERENCES users(id));

        CREATE TABLE IF NOT EXISTS reservations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id INTEGER NOT NULL,
            train_id INTEGER NOT NULL,
            travel_date TEXT NOT NULL DEFAULT '',
            seat_no TEXT NOT NULL,
            seat_class TEXT NOT NULL DEFAULT 'economy',
            passenger_type TEXT NOT NULL DEFAULT 'adult',
            price_paid REAL NOT NULL DEFAULT 0,
            final_paid_price REAL NOT NULL DEFAULT 0,
            booked_by INTEGER,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(passenger_id) REFERENCES passengers(id),
            FOREIGN KEY(train_id) REFERENCES trains(id),
            FOREIGN KEY(booked_by) REFERENCES users(id));
    """)

    # Safe migrations for existing databases
    for sql in [
        "ALTER TABLE reservations ADD COLUMN travel_date TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE reservations ADD COLUMN final_paid_price REAL NOT NULL DEFAULT 0",
        "ALTER TABLE passengers ADD COLUMN created_by INTEGER DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN full_name TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN email TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''",
        "ALTER TABLE users ADD COLUMN national_id TEXT DEFAULT ''",
    ]:
        try: c.execute(sql)
        except: pass

    # ── System users ───────────────────────────────────────────────────────────
    for u in [
        ("addmin",   "admin123",    "admin"),
        ("Staff",    "staff123",    "staff"),
        ("Costumer", "costumer123", "customer"),
    ]:
        try: c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", (u[0], sha(u[1]), u[2]))
        except: pass

    # ── 20 pre-defined Saudi passengers ───────────────────────────────────────
    # (name, national_id, email, phone)
    passengers_seed = [
        # 10 Boys (IDs start with 1)
        ("Mohammed Al-Otaibi",      "1023456781", "mohammed.otaibi@sikka.sa",     "0512345601"),
        ("Abdulrahman Al-Shahrani", "1034567892", "abdulrahman.shahrani@sikka.sa", "0512345602"),
        ("Fahad Al-Qahtani",        "1045678903", "fahad.qahtani@sikka.sa",       "0512345603"),
        ("Khaled Al-Dossari",       "1056789014", "khaled.dossari@sikka.sa",      "0512345604"),
        ("Sultan Al-Anazi",         "1067890125", "sultan.anazi@sikka.sa",        "0512345605"),
        ("Youssef Al-Mutairi",      "1078901236", "youssef.mutairi@sikka.sa",     "0512345606"),
        ("Faisal Al-Subaie",        "1089012347", "faisal.subaie@sikka.sa",       "0512345607"),
        ("Abdullah Al-Ghamdi",      "1090123458", "abdullah.ghamdi@sikka.sa",     "0512345608"),
        ("Saud Al-Zahrani",         "1001234569", "saud.zahrani@sikka.sa",        "0512345609"),
        ("Turki Al-Harbi",          "1012345670", "turki.harbi@sikka.sa",         "0512345610"),
        # 10 Girls (IDs start with 2)
        ("Sarah Al-Ahmad",          "2023456781", "sarah.ahmad@sikka.sa",         "0552345601"),
        ("Noura Al-Dosari",         "2034567892", "noura.dosari@sikka.sa",        "0552345602"),
        ("Reem Al-Anazi",           "2045678903", "reem.anazi@sikka.sa",          "0552345603"),
        ("Maha Al-Shammari",        "2056789014", "maha.shammari@sikka.sa",       "0552345604"),
        ("Layla Al-Harbi",          "2067890125", "layla.harbi@sikka.sa",         "0552345605"),
        ("Hessa Al-Sudairy",        "2078901236", "hessa.sudairy@sikka.sa",       "0552345606"),
        ("Ghadah Al-Otaibi",        "2089012347", "ghadah.otaibi@sikka.sa",       "0552345607"),
        ("Mona Al-Qahtani",         "2090123458", "mona.qahtani@sikka.sa",        "0552345608"),
        ("Fatima Al-Zahrani",       "2001234569", "fatima.zahrani@sikka.sa",      "0552345609"),
        ("Joud Al-Bader",           "2012345670", "joud.bader@sikka.sa",          "0552345610"),
    ]
    for p in passengers_seed:
        try: c.execute("INSERT INTO passengers(name,national_id,email,phone) VALUES(?,?,?,?)", p)
        except: pass

    # ── Comprehensive train network — all city pairs with return routes ─────────
    # Format: (name, route, departure, arrival, cap_eco, cap_bus, price_eco, price_bus)
    trains_seed = [
        # ── Riyadh ↔ Jeddah ────────────────────────────────────────────────────
        ("SKK-101", "Riyadh – Jeddah",   "07:00", "11:00", 60, 20, 200, 380),
        ("SKK-102", "Jeddah – Riyadh",   "13:00", "17:00", 60, 20, 200, 380),
        # ── Riyadh ↔ Dammam ────────────────────────────────────────────────────
        ("SKK-103", "Riyadh – Dammam",   "08:00", "11:00", 60, 20, 150, 280),
        ("SKK-104", "Dammam – Riyadh",   "14:00", "17:00", 60, 20, 150, 280),
        # ── Riyadh ↔ Madinah ───────────────────────────────────────────────────
        ("SKK-105", "Riyadh – Madinah",  "06:00", "10:30", 60, 20, 210, 400),
        ("SKK-106", "Madinah – Riyadh",  "12:00", "16:30", 60, 20, 210, 400),
        # ── Riyadh ↔ Mecca ─────────────────────────────────────────────────────
        ("SKK-107", "Riyadh – Mecca",    "06:30", "11:00", 60, 20, 220, 420),
        ("SKK-108", "Mecca – Riyadh",    "13:00", "17:30", 60, 20, 220, 420),
        # ── Riyadh ↔ Tabuk ─────────────────────────────────────────────────────
        ("SKK-109", "Riyadh – Tabuk",    "07:00", "12:00", 60, 20, 240, 460),
        ("SKK-110", "Tabuk – Riyadh",    "13:30", "18:30", 60, 20, 240, 460),
        # ── Riyadh ↔ Abha ──────────────────────────────────────────────────────
        ("SKK-111", "Riyadh – Abha",     "08:00", "13:00", 60, 20, 230, 440),
        ("SKK-112", "Abha – Riyadh",     "14:00", "19:00", 60, 20, 230, 440),
        # ── Riyadh ↔ Hail ──────────────────────────────────────────────────────
        ("SKK-113", "Riyadh – Hail",     "08:30", "12:00", 60, 20, 180, 340),
        ("SKK-114", "Hail – Riyadh",     "13:30", "17:00", 60, 20, 180, 340),
        # ── Jeddah ↔ Mecca ─────────────────────────────────────────────────────
        ("SKK-201", "Jeddah – Mecca",    "06:00", "06:45", 80, 20,  80, 160),
        ("SKK-202", "Mecca – Jeddah",    "09:00", "09:45", 80, 20,  80, 160),
        # ── Jeddah ↔ Madinah ───────────────────────────────────────────────────
        ("SKK-203", "Jeddah – Madinah",  "09:00", "11:30", 60, 20, 180, 340),
        ("SKK-204", "Madinah – Jeddah",  "13:00", "15:30", 60, 20, 180, 340),
        # ── Jeddah ↔ Dammam ────────────────────────────────────────────────────
        ("SKK-205", "Jeddah – Dammam",   "07:30", "12:30", 60, 20, 260, 500),
        ("SKK-206", "Dammam – Jeddah",   "14:00", "19:00", 60, 20, 260, 500),
        # ── Jeddah ↔ Tabuk ─────────────────────────────────────────────────────
        ("SKK-207", "Jeddah – Tabuk",    "08:00", "12:00", 60, 20, 200, 380),
        ("SKK-208", "Tabuk – Jeddah",    "14:00", "18:00", 60, 20, 200, 380),
        # ── Jeddah ↔ Abha ──────────────────────────────────────────────────────
        ("SKK-209", "Jeddah – Abha",     "08:30", "12:00", 60, 20, 190, 360),
        ("SKK-210", "Abha – Jeddah",     "13:30", "17:00", 60, 20, 190, 360),
        # ── Jeddah ↔ Hail ──────────────────────────────────────────────────────
        ("SKK-211", "Jeddah – Hail",     "09:00", "13:30", 60, 20, 220, 420),
        ("SKK-212", "Hail – Jeddah",     "14:30", "19:00", 60, 20, 220, 420),
        # ── Mecca ↔ Madinah ────────────────────────────────────────────────────
        ("SKK-301", "Mecca – Madinah",   "07:00", "09:30", 60, 20, 140, 260),
        ("SKK-302", "Madinah – Mecca",   "11:00", "13:30", 60, 20, 140, 260),
        # ── Mecca ↔ Dammam ─────────────────────────────────────────────────────
        ("SKK-303", "Mecca – Dammam",    "07:30", "12:30", 60, 20, 250, 480),
        ("SKK-304", "Dammam – Mecca",    "14:00", "19:00", 60, 20, 250, 480),
        # ── Mecca ↔ Tabuk ──────────────────────────────────────────────────────
        ("SKK-305", "Mecca – Tabuk",     "08:00", "12:30", 60, 20, 210, 400),
        ("SKK-306", "Tabuk – Mecca",     "14:30", "19:00", 60, 20, 210, 400),
        # ── Mecca ↔ Abha ───────────────────────────────────────────────────────
        ("SKK-307", "Mecca – Abha",      "09:00", "12:30", 60, 20, 190, 360),
        ("SKK-308", "Abha – Mecca",      "14:00", "17:30", 60, 20, 190, 360),
        # ── Mecca ↔ Hail ───────────────────────────────────────────────────────
        ("SKK-309", "Mecca – Hail",      "08:30", "13:00", 60, 20, 220, 420),
        ("SKK-310", "Hail – Mecca",      "14:00", "18:30", 60, 20, 220, 420),
        # ── Madinah ↔ Dammam ───────────────────────────────────────────────────
        ("SKK-401", "Madinah – Dammam",  "08:00", "13:00", 60, 20, 240, 460),
        ("SKK-402", "Dammam – Madinah",  "14:30", "19:30", 60, 20, 240, 460),
        # ── Madinah ↔ Tabuk ────────────────────────────────────────────────────
        ("SKK-403", "Madinah – Tabuk",   "09:00", "12:30", 60, 20, 180, 340),
        ("SKK-404", "Tabuk – Madinah",   "14:00", "17:30", 60, 20, 180, 340),
        # ── Madinah ↔ Abha ─────────────────────────────────────────────────────
        ("SKK-405", "Madinah – Abha",    "08:30", "13:30", 60, 20, 230, 440),
        ("SKK-406", "Abha – Madinah",    "14:30", "19:30", 60, 20, 230, 440),
        # ── Madinah ↔ Hail ─────────────────────────────────────────────────────
        ("SKK-407", "Madinah – Hail",    "09:00", "12:00", 60, 20, 160, 300),
        ("SKK-408", "Hail – Madinah",    "13:30", "16:30", 60, 20, 160, 300),
        # ── Dammam ↔ Tabuk ─────────────────────────────────────────────────────
        ("SKK-501", "Dammam – Tabuk",    "08:00", "14:00", 60, 20, 280, 540),
        ("SKK-502", "Tabuk – Dammam",    "15:00", "21:00", 60, 20, 280, 540),
        # ── Dammam ↔ Abha ──────────────────────────────────────────────────────
        ("SKK-503", "Dammam – Abha",     "08:30", "14:00", 60, 20, 270, 520),
        ("SKK-504", "Abha – Dammam",     "15:00", "20:30", 60, 20, 270, 520),
        # ── Dammam ↔ Hail ──────────────────────────────────────────────────────
        ("SKK-505", "Dammam – Hail",     "09:00", "13:30", 60, 20, 220, 420),
        ("SKK-506", "Hail – Dammam",     "14:30", "19:00", 60, 20, 220, 420),
        # ── Tabuk ↔ Abha ───────────────────────────────────────────────────────
        ("SKK-601", "Tabuk – Abha",      "09:00", "14:30", 60, 20, 260, 500),
        ("SKK-602", "Abha – Tabuk",      "15:30", "21:00", 60, 20, 260, 500),
        # ── Tabuk ↔ Hail ───────────────────────────────────────────────────────
        ("SKK-603", "Tabuk – Hail",      "09:30", "13:00", 60, 20, 190, 360),
        ("SKK-604", "Hail – Tabuk",      "14:00", "17:30", 60, 20, 190, 360),
        # ── Abha ↔ Hail ────────────────────────────────────────────────────────
        ("SKK-701", "Abha – Hail",       "09:00", "14:00", 60, 20, 240, 460),
        ("SKK-702", "Hail – Abha",       "15:00", "20:00", 60, 20, 240, 460),
    ]

    for t in trains_seed:
        try:
            c.execute(
                "INSERT INTO trains(name,route,departure,arrival,capacity_economy,capacity_business,price_economy,price_business) VALUES(?,?,?,?,?,?,?,?)",
                t
            )
        except: pass

    # Seed schedules: next 30 days for every train
    today = date.today()
    tids = c.execute("SELECT id FROM trains").fetchall()
    for tid in tids:
        for i in range(30):
            d = (today + timedelta(days=i)).isoformat()
            try: c.execute("INSERT INTO schedules(train_id,travel_date) VALUES(?,?)", (tid[0], d))
            except: pass

    conn.commit(); conn.close()

# ─── DECORATORS ────────────────────────────────────────────────────────────────
def login_required(fn):
    @wraps(fn)
    def w(*a, **k):
        if "user_id" not in session: return redirect(url_for("login"))
        return fn(*a, **k)
    return w

def admin_required(fn):
    @wraps(fn)
    def w(*a, **k):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        role = session.get("user_role") or session.get("role", "")
        if role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("home"))
        return fn(*a, **k)
    return w

def staff_or_admin(fn):
    @wraps(fn)
    def w(*a, **k):
        if "user_id" not in session: return redirect(url_for("login"))
        role = session.get("user_role") or session.get("role", "")
        if role not in ("admin", "staff"):
            flash("Access denied.", "danger"); return redirect(url_for("home"))
        return fn(*a, **k)
    return w

def get_t():  return TR.get(session.get("lang", "en"), TR["en"])
def get_dir(): return "rtl" if session.get("lang", "en") == "ar" else "ltr"

def booked_seats(train_id, seat_class, travel_date=None):
    conn = get_db()
    if travel_date:
        rows = conn.execute(
            "SELECT seat_no FROM reservations WHERE train_id=? AND seat_class=? AND travel_date=? AND status='confirmed'",
            (train_id, seat_class, travel_date)).fetchall()
    else:
        rows = conn.execute(
            "SELECT seat_no FROM reservations WHERE train_id=? AND seat_class=? AND status='confirmed'",
            (train_id, seat_class)).fetchall()
    conn.close()
    return {r["seat_no"] for r in rows}

def calc_price(base, sc, pt):
    """base = DB price for the chosen class. Only apply passenger-type discount."""
    return round(base * PRICING.get(pt, 1.0), 2)

def city_names_list(lang):
    return [{"key": c["key"], "en_name": c["en_name"], "ar_name": c["ar_name"],
             "name": c["ar_name"] if lang == "ar" else c["en_name"]} for c in CITIES]

def _is_own_passenger(passenger, uid):
    cb = passenger["created_by"]
    return cb is None or cb == uid

# ─── LANGUAGE ──────────────────────────────────────────────────────────────────
@app.route("/lang/<code>")
def set_lang(code):
    if code in ("en", "ar"): session["lang"] = code
    return redirect(request.referrer or url_for("home"))

# ─── AUTH ──────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return redirect(url_for("home") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    t = get_t()
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if not u: flash("Username required.", "danger"); return render_template("login.html", t=t, dir=get_dir(), si=SITE_IMAGES)
        if not p: flash("Password required.", "danger"); return render_template("login.html", t=t, dir=get_dir(), si=SITE_IMAGES)
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, sha(p))).fetchone()
        conn.close()
        if user:
            session.permanent    = True
            session["user_id"]   = user["id"]
            session["username"]  = user["username"]
            session["role"]      = user["role"]
            session["user_role"] = user["role"]
            return redirect(url_for("home"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html", t=t, dir=get_dir(), si=SITE_IMAGES)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    t = get_t()
    if "user_id" in session: return redirect(url_for("home"))
    if request.method == "POST":
        full_name   = request.form.get("full_name",   "").strip()
        email       = request.form.get("email",       "").strip().lower()
        username    = request.form.get("username",    "").strip()
        password    = request.form.get("password",    "").strip()
        confirm     = request.form.get("confirm",     "").strip()
        national_id = request.form.get("national_id", "").strip()
        phone       = request.form.get("phone",       "").strip()
        errors = []
        if not full_name:  errors.append("Full name is required.")
        if not username:   errors.append("Username is required.")
        if not email or "@" not in email: errors.append("Valid email is required.")
        if not password:   errors.append("Password is required.")
        if len(password) < 6: errors.append("Password must be at least 6 characters.")
        if password != confirm: errors.append("Passwords do not match.")
        if national_id and (not national_id.isdigit() or len(national_id) != 10 or national_id[0] not in ("1", "2")):
            errors.append("National ID must be 10 digits starting with 1 or 2.")
        if phone and (not phone.isdigit() or len(phone) != 10 or not phone.startswith("05")):
            errors.append("Mobile must be 10 digits starting with 05.")
        if not errors:
            conn = get_db()
            if conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
                errors.append("Username already taken.")
            if email and conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                errors.append("Email already registered.")
            if national_id and conn.execute("SELECT id FROM users WHERE national_id=?", (national_id,)).fetchone():
                errors.append("National ID already registered.")
            conn.close()
        if errors:
            for e in errors: flash(e, "danger")
            return render_template("signup.html", t=t, dir=get_dir(), form=request.form)
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(username,password,role,full_name,email,phone,national_id) VALUES(?,?,?,?,?,?,?)",
                (username, sha(password), "customer", full_name, email, phone, national_id)
            )
            conn.commit()
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("login"))
        except Exception as ex:
            flash(f"Registration failed: {ex}", "danger")
        finally:
            conn.close()
    return render_template("signup.html", t=t, dir=get_dir(), form={})

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

# ─── HOME ──────────────────────────────────────────────────────────────────────
@app.route("/home")
@login_required
def home():
    t = get_t(); lang = session.get("lang", "en")
    conn = get_db()
    trains = conn.execute("SELECT * FROM trains WHERE status='active'").fetchall()
    conn.close()
    return render_template("home.html", t=t, dir=get_dir(), trains=trains,
                           cities=CITIES, lang=lang, si=SITE_IMAGES,
                           cnl=city_names_list(lang))

# ─── DASHBOARD ─────────────────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    t = get_t(); conn = get_db()
    stats = {
        "trains": conn.execute("SELECT COUNT(*) FROM trains").fetchone()[0],
        "res":    conn.execute("SELECT COUNT(*) FROM reservations WHERE status='confirmed'").fetchone()[0],
        "pass_":  conn.execute("SELECT COUNT(*) FROM passengers").fetchone()[0],
        "rev":    conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN final_paid_price>0 THEN final_paid_price ELSE price_paid END),0) "
            "FROM reservations WHERE status='confirmed'"
        ).fetchone()[0],
    }
    trains = conn.execute("SELECT * FROM trains WHERE status='active' LIMIT 5").fetchall()
    recent = conn.execute("""
        SELECT r.*, p.name AS pname, t.name AS tname
        FROM reservations r
        JOIN passengers p ON r.passenger_id=p.id
        JOIN trains t ON r.train_id=t.id
        WHERE r.status='confirmed' ORDER BY r.id DESC LIMIT 6
    """).fetchall()
    conn.close()
    return render_template("dashboard.html", t=t, dir=get_dir(), stats=stats, trains=trains, recent=recent)

# ─── API: available dates ───────────────────────────────────────────────────────
@app.route("/api/dates")
@login_required
def api_dates():
    fc = request.args.get("from", ""); tc = request.args.get("to", "")
    if not fc or not tc: return jsonify([])
    pattern = f"%{fc}%{tc}%"
    conn = get_db()
    rows = conn.execute("""
        SELECT DISTINCT s.travel_date FROM schedules s
        JOIN trains t ON s.train_id=t.id
        WHERE t.route LIKE ? AND t.status='active' AND s.travel_date>=?
        ORDER BY s.travel_date
    """, (pattern, date.today().isoformat())).fetchall()
    conn.close()
    return jsonify([r["travel_date"] for r in rows])

# ─── SEARCH ────────────────────────────────────────────────────────────────────
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    t = get_t(); lang = session.get("lang", "en")
    cn = city_names_list(lang)
    results = []; searched = False
    fc = (request.form.get("from_city")   or request.args.get("from_city",   "")).strip()
    tc = (request.form.get("to_city")     or request.args.get("to_city",     "")).strip()
    td = (request.form.get("travel_date") or request.args.get("travel_date", "")).strip()
    if request.method == "POST" or (fc and tc and td):
        searched = True
        if fc and tc and td:
            pattern = f"%{fc}%{tc}%"
            conn = get_db()
            rows = conn.execute("""
                SELECT t.* FROM trains t JOIN schedules s ON s.train_id=t.id
                WHERE t.route LIKE ? AND t.status='active' AND s.travel_date=?
                ORDER BY t.departure
            """, (pattern, td)).fetchall()
            enriched = []
            for tr in rows:
                be = len(booked_seats(tr["id"], "economy",  td))
                bb = len(booked_seats(tr["id"], "business", td))
                enriched.append({
                    "id": tr["id"], "name": tr["name"], "route": tr["route"],
                    "departure": tr["departure"], "arrival": tr["arrival"],
                    "price_economy": tr["price_economy"], "price_business": tr["price_business"],
                    "capacity_economy": tr["capacity_economy"], "capacity_business": tr["capacity_business"],
                    "avail_eco": tr["capacity_economy"] - be,
                    "avail_bus": tr["capacity_business"] - bb,
                    "img": "",
                })
            conn.close(); results = enriched
    return render_template("search.html", t=t, dir=get_dir(),
        city_names=cn, results=results, searched=searched,
        from_city=fc, to_city=tc, travel_date=td, today=date.today().isoformat())

# ─── BOOK ──────────────────────────────────────────────────────────────────────
@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    t = get_t(); conn = get_db()
    pax_list    = conn.execute("SELECT * FROM passengers ORDER BY name").fetchall()
    selected    = None; eco_seats = []; bus_seats = []
    train_id    = request.args.get("train_id")    or request.form.get("train_id")
    travel_date = request.args.get("travel_date") or request.form.get("travel_date", "")
    if train_id:
        selected = conn.execute("SELECT * FROM trains WHERE id=?", (train_id,)).fetchone()
        if selected:
            booked_eco = booked_seats(int(train_id), "economy",  travel_date)
            booked_bus = booked_seats(int(train_id), "business", travel_date)
            for r in range(1, selected["capacity_economy"] // 6 + 2):
                for l in ["A","B","C","D","E","F"]:
                    s = f"E{r}{l}"; eco_seats.append((s, s not in booked_eco))
                    if len(eco_seats) >= selected["capacity_economy"]: break
                if len(eco_seats) >= selected["capacity_economy"]: break
            for r in range(1, selected["capacity_business"] // 4 + 2):
                for l in ["A","B","C","D"]:
                    s = f"B{r}{l}"; bus_seats.append((s, s not in booked_bus))
                    if len(bus_seats) >= selected["capacity_business"]: break
                if len(bus_seats) >= selected["capacity_business"]: break
    if request.method == "POST":
        f     = request.form
        pid   = f.get("passenger_id"); tid   = f.get("train_id")
        seat  = f.get("seat_no", "").strip(); sc  = f.get("seat_class", "economy")
        pt    = f.get("passenger_type", "adult"); tdate = f.get("travel_date", "")
        if not pid or not tid or not seat:
            flash("Please complete all fields.", "danger")
        else:
            tr    = conn.execute("SELECT * FROM trains WHERE id=?", (tid,)).fetchone()
            taken = booked_seats(int(tid), sc, tdate)
            base  = tr["price_business"] if sc == "business" else tr["price_economy"]
            price = calc_price(base, sc, pt)
            if seat in taken:
                flash("Seat already taken, choose another.", "danger")
            else:
                conn.execute(
                    "INSERT INTO reservations(passenger_id,train_id,travel_date,seat_no,seat_class,passenger_type,price_paid,final_paid_price,booked_by) VALUES(?,?,?,?,?,?,?,?,?)",
                    (pid, tid, tdate, seat, sc, pt, price, price, session["user_id"])
                )
                conn.commit(); flash("Booking confirmed!", "success"); conn.close()
                return redirect(url_for("reservations"))
    conn.close()
    return render_template("book.html", t=t, dir=get_dir(),
        pax_list=pax_list, selected=selected, eco_seats=eco_seats, bus_seats=bus_seats,
        train_id=train_id, travel_date=travel_date, pricing=PRICING, train_img="")

# ─── TRAINS ────────────────────────────────────────────────────────────────────
@app.route("/trains")
@login_required
def trains():
    t = get_t(); conn = get_db()
    rows = conn.execute("SELECT * FROM trains").fetchall()
    bc = {tr["id"]: {
        "economy":  conn.execute("SELECT COUNT(*) FROM reservations WHERE train_id=? AND seat_class='economy'  AND status='confirmed'", (tr["id"],)).fetchone()[0],
        "business": conn.execute("SELECT COUNT(*) FROM reservations WHERE train_id=? AND seat_class='business' AND status='confirmed'", (tr["id"],)).fetchone()[0],
    } for tr in rows}
    conn.close()
    return render_template("trains.html", t=t, dir=get_dir(), trains=rows, bc=bc)

@app.route("/trains/add", methods=["GET", "POST"])
@admin_required
def add_train():
    t = get_t()
    if request.method == "POST":
        f = request.form; conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO trains(name,route,departure,arrival,capacity_economy,capacity_business,price_economy,price_business) VALUES(?,?,?,?,?,?,?,?)",
                (f["name"], f["route"], f["departure"], f["arrival"],
                 int(f.get("cap_eco", 60)), int(f.get("cap_bus", 20)),
                 float(f["price_eco"]), float(f["price_bus"]))
            )
            tid = cur.lastrowid
            today = date.today()
            for i in range(30):
                d = (today + timedelta(days=i)).isoformat()
                try: cur.execute("INSERT INTO schedules(train_id,travel_date) VALUES(?,?)", (tid, d))
                except: pass
            conn.commit(); flash("Train added.", "success"); return redirect(url_for("trains"))
        except Exception as e: flash(str(e), "danger")
        finally: conn.close()
    return render_template("train_form.html", t=t, dir=get_dir(), train=None)

@app.route("/trains/edit/<int:tid>", methods=["GET", "POST"])
@admin_required
def edit_train(tid):
    t = get_t(); conn = get_db()
    tr = conn.execute("SELECT * FROM trains WHERE id=?", (tid,)).fetchone()
    if not tr: conn.close(); return redirect(url_for("trains"))
    if request.method == "POST":
        f = request.form
        conn.execute(
            "UPDATE trains SET name=?,route=?,departure=?,arrival=?,capacity_economy=?,capacity_business=?,price_economy=?,price_business=? WHERE id=?",
            (f["name"], f["route"], f["departure"], f["arrival"],
             int(f.get("cap_eco", 60)), int(f.get("cap_bus", 20)),
             float(f["price_eco"]), float(f["price_bus"]), tid)
        )
        conn.commit(); conn.close(); flash("Train updated.", "success"); return redirect(url_for("trains"))
    conn.close(); return render_template("train_form.html", t=t, dir=get_dir(), train=tr)

@app.route("/trains/delete/<int:tid>", methods=["POST"])
@admin_required
def delete_train(tid):
    conn = get_db()
    conn.execute("DELETE FROM schedules WHERE train_id=?", (tid,))
    conn.execute("DELETE FROM trains WHERE id=?", (tid,))
    conn.commit(); conn.close(); flash("Train deleted.", "success"); return redirect(url_for("trains"))

@app.route("/trains/schedules/<int:tid>", methods=["GET", "POST"])
@admin_required
def manage_schedules(tid):
    t = get_t(); conn = get_db()
    tr = conn.execute("SELECT * FROM trains WHERE id=?", (tid,)).fetchone()
    if not tr: conn.close(); return redirect(url_for("trains"))
    if request.method == "POST":
        action = request.form.get("action"); d = request.form.get("sdate", "").strip()
        if action == "add" and d:
            try: conn.execute("INSERT INTO schedules(train_id,travel_date) VALUES(?,?)", (tid, d))
            except: flash("Date already exists.", "warning")
        elif action == "remove" and d:
            conn.execute("DELETE FROM schedules WHERE train_id=? AND travel_date=?", (tid, d))
        conn.commit()
    scheds = conn.execute("SELECT travel_date FROM schedules WHERE train_id=? ORDER BY travel_date", (tid,)).fetchall()
    conn.close()
    return render_template("manage_schedules.html", t=t, dir=get_dir(),
                           train=tr, schedules=scheds, today=date.today().isoformat())

# ─── PASSENGERS ────────────────────────────────────────────────────────────────
@app.route("/passengers")
@login_required
def passengers():
    t = get_t(); conn = get_db()
    role = session.get("user_role") or session.get("role", "")
    uid  = session["user_id"]
    if role in ("admin", "staff"):
        rows = conn.execute("SELECT * FROM passengers ORDER BY name").fetchall()
    else:
        rows = conn.execute("SELECT * FROM passengers WHERE created_by=? ORDER BY name", (uid,)).fetchall()
    conn.close()
    return render_template("passengers.html", t=t, dir=get_dir(), passengers=rows)

@app.route("/passengers/add", methods=["GET", "POST"])
@login_required
def add_passenger():
    t = get_t()
    if request.method == "POST":
        name  = request.form.get("name",        "").strip()
        nid   = request.form.get("national_id", "").strip()
        email = request.form.get("email",        "").strip()
        phone = request.form.get("phone",        "").strip()
        errors = []
        if not name: errors.append("Full name is required.")
        if not nid:  errors.append("National ID is required.")
        elif not nid.isdigit() or len(nid) != 10 or nid[0] not in ("1", "2"):
            errors.append("National ID must be 10 digits starting with 1 or 2.")
        if phone and (not phone.isdigit() or len(phone) != 10 or not phone.startswith("05")):
            errors.append("Mobile must be 10 digits starting with 05.")
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            errors.append("Enter a valid email address.")
        if errors:
            for e in errors: flash(e, "danger")
            return render_template("passenger_form.html", t=t, dir=get_dir(), passenger=None)
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO passengers(name,national_id,email,phone,created_by) VALUES(?,?,?,?,?)",
                (name, nid, email, phone, session["user_id"])
            )
            conn.commit(); conn.close(); flash("Passenger added.", "success")
            return redirect(url_for("passengers"))
        except sqlite3.IntegrityError:
            flash("National ID already exists.", "danger")
    return render_template("passenger_form.html", t=t, dir=get_dir(), passenger=None)

@app.route("/passengers/edit/<int:pid>", methods=["GET", "POST"])
@login_required
def edit_passenger(pid):
    t = get_t(); conn = get_db()
    p = conn.execute("SELECT * FROM passengers WHERE id=?", (pid,)).fetchone()
    if not p: conn.close(); return redirect(url_for("passengers"))
    role = session.get("user_role") or session.get("role", "")
    if role == "customer" and not _is_own_passenger(p, session["user_id"]):
        conn.close(); flash("Access denied.", "danger"); return redirect(url_for("passengers"))
    if request.method == "POST":
        conn.execute(
            "UPDATE passengers SET name=?,national_id=?,email=?,phone=? WHERE id=?",
            (request.form.get("name"), request.form.get("national_id"),
             request.form.get("email"), request.form.get("phone"), pid)
        )
        conn.commit(); conn.close(); flash("Passenger updated.", "success")
        return redirect(url_for("passengers"))
    conn.close()
    return render_template("passenger_form.html", t=t, dir=get_dir(), passenger=p)

@app.route("/passengers/delete/<int:pid>", methods=["POST"])
@login_required
def delete_passenger(pid):
    conn = get_db()
    p = conn.execute("SELECT * FROM passengers WHERE id=?", (pid,)).fetchone()
    if not p: conn.close(); flash("Not found.", "danger"); return redirect(url_for("passengers"))
    role = session.get("user_role") or session.get("role", "")
    if role == "customer" and not _is_own_passenger(p, session["user_id"]):
        conn.close(); flash("Access denied.", "danger"); return redirect(url_for("passengers"))
    conn.execute("DELETE FROM passengers WHERE id=?", (pid,))
    conn.commit(); conn.close(); flash("Passenger deleted.", "success")
    return redirect(url_for("passengers"))

# ─── RESERVATIONS ──────────────────────────────────────────────────────────────
@app.route("/reservations")
@login_required
def reservations():
    t = get_t(); conn = get_db()
    if session.get("role") == "customer":
        rows = conn.execute("""
            SELECT r.*, p.name AS pname, p.national_id, t.name AS tname, t.route
            FROM reservations r
            JOIN passengers p ON r.passenger_id=p.id
            JOIN trains t ON r.train_id=t.id
            WHERE r.booked_by=? ORDER BY r.id DESC
        """, (session["user_id"],)).fetchall()
    else:
        rows = conn.execute("""
            SELECT r.*, p.name AS pname, p.national_id, t.name AS tname, t.route
            FROM reservations r
            JOIN passengers p ON r.passenger_id=p.id
            JOIN trains t ON r.train_id=t.id
            ORDER BY r.id DESC
        """).fetchall()
    conn.close()
    return render_template("reservations.html", t=t, dir=get_dir(), reservations=rows)

@app.route("/cancel/<int:rid>", methods=["POST"])
@login_required
def cancel_reservation(rid):
    conn = get_db()
    r = conn.execute("SELECT * FROM reservations WHERE id=?", (rid,)).fetchone()
    if not r:
        flash("Not found.", "danger")
    elif session.get("role") == "customer" and r["booked_by"] != session["user_id"]:
        flash("Access denied.", "danger")
    else:
        conn.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (rid,))
        conn.commit(); flash("Reservation cancelled.", "success")
    conn.close(); return redirect(url_for("reservations"))

# ─── REPORTS ───────────────────────────────────────────────────────────────────
@app.route("/reports", methods=["GET", "POST"])
@admin_required
def reports():
    t   = get_t()
    rt  = request.form.get("report_type", "daily")
    df  = request.form.get("date_from", date.today().isoformat())
    dt_ = request.form.get("date_to",   date.today().isoformat())
    conn = get_db(); rows = []; rev = 0
    if request.method == "POST":
        q = """SELECT r.*, p.name AS pname, t.name AS tname, t.route
               FROM reservations r
               JOIN passengers p ON r.passenger_id=p.id
               JOIN trains t ON r.train_id=t.id
               WHERE r.status='confirmed'"""
        rows = conn.execute(
            q + (" AND DATE(r.created_at)=?" if rt == "daily" else " AND DATE(r.created_at) BETWEEN ? AND ?"),
            ((df,) if rt == "daily" else (df, dt_))
        ).fetchall()
        rev = sum(r["final_paid_price"] if r["final_paid_price"] else r["price_paid"] for r in rows)
    conn.close()
    return render_template("reports.html", t=t, dir=get_dir(),
        rows=rows, rev=rev, rt=rt, df=df, dt=dt_, submitted=(request.method == "POST"))

# ─── ABOUT & HELP ──────────────────────────────────────────────────────────────
@app.route("/about")
def about():
    t = get_t(); lang = session.get("lang", "en")
    return render_template("about.html", t=t, dir=get_dir(), team=TEAM, lang=lang, si=SITE_IMAGES)

@app.route("/help")
def help_page():
    return render_template("help.html", t=get_t(), dir=get_dir())

# ─── ADMIN PAGES ───────────────────────────────────────────────────────────────
@app.route("/admin/images", methods=["GET", "POST"])
@admin_required
def edit_site_images():
    t = get_t()
    global SITE_IMAGES
    if request.method == "POST":
        for k in list(SITE_IMAGES.keys()):
            SITE_IMAGES[k] = request.form.get(k, "").strip()
        flash("Site images updated.", "success"); return redirect(url_for("home"))
    return render_template("edit_site_images.html", t=t, dir=get_dir(), images=SITE_IMAGES)

@app.route("/admin/cities", methods=["GET", "POST"])
@admin_required
def edit_cities():
    t = get_t()
    global CITIES
    if request.method == "POST":
        updated = []
        for i, c in enumerate(CITIES):
            raw = request.form.get(f"img_{i}", "").strip()
            img = f"images/{raw}" if raw and not raw.startswith("images/") else (raw or c["img"])
            updated.append({**c, "img": img,
                "en_name": request.form.get(f"en_name_{i}", c["en_name"]),
                "ar_name": request.form.get(f"ar_name_{i}", c["ar_name"]),
                "en_desc": request.form.get(f"en_desc_{i}", c["en_desc"]),
                "ar_desc": request.form.get(f"ar_desc_{i}", c["ar_desc"]),
            })
        CITIES = updated; flash("Destinations updated.", "success"); return redirect(url_for("home"))
    return render_template("edit_cities.html", t=t, dir=get_dir(), cities=CITIES)

@app.route("/admin/team", methods=["GET", "POST"])
@admin_required
def edit_team():
    t = get_t()
    global TEAM
    if request.method == "POST":
        updated = []
        for i, m in enumerate(TEAM):
            updated.append({**m,
                "name":    request.form.get(f"name_{i}",    m["name"]),
                "role_en": request.form.get(f"role_en_{i}", m["role_en"]),
                "role_ar": request.form.get(f"role_ar_{i}", m["role_ar"]),
                "bio_en":  request.form.get(f"bio_en_{i}",  m.get("bio_en", "")),
                "bio_ar":  request.form.get(f"bio_ar_{i}",  m.get("bio_ar", "")),
            })
        TEAM = updated; flash("Team updated.", "success"); return redirect(url_for("about"))
    return render_template("edit_team.html", t=t, dir=get_dir(), team=TEAM)

# ─── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n" + "═" * 54)
    print("  SIKKA — Saudi Rail Booking System")
    print("  http://127.0.0.1:5000")
    print("  Admin:    addmin   / admin123")
    print("  Staff:    Staff    / staff123")
    print("  Customer: Costumer / costumer123")
    print("═" * 54 + "\n")
    app.run(debug=True)
