# Run this file once to create the database and tables: python init_db.py

import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "service_finder.db"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    region TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    phone TEXT,
    region TEXT,
    service_category TEXT,
    experience INTEGER DEFAULT 0,
    bio TEXT,
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    service_name TEXT,
    description TEXT,
    booking_date TEXT,
    booking_time TEXT,
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (provider_id) REFERENCES providers(id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id)
)
""")

conn.commit()

c.execute("SELECT * FROM admin WHERE email = ?", ("admin@servicefinder.com",))
if c.fetchone() is None:
    hashed_pw = generate_password_hash("admin123")
    c.execute("INSERT INTO admin (email, password) VALUES (?, ?)",
              ("admin@servicefinder.com", hashed_pw))
    print("Default admin created -> email: admin@servicefinder.com  password: admin123")

default_services = ["Plumbing", "Electrical", "Carpentry", "AC Repair",
                    "Painting", "Appliance Repair", "Cleaning", "Pest Control"]

for s in default_services:
    c.execute("SELECT * FROM services WHERE name = ?", (s,))
    if c.fetchone() is None:
        c.execute("INSERT INTO services (name) VALUES (?)", (s,))

conn.commit()
conn.close()

print("Database initialized successfully! (service_finder.db)")
