import random
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from werkzeug.security import generate_password_hash

from database.db import get_db


FIRST_NAMES = [
    "Aarav", "Aditya", "Arjun", "Ayaan", "Dhruv", "Ishaan", "Kabir", "Karan",
    "Krishna", "Rahul", "Rohan", "Rohit", "Sahil", "Siddharth", "Vihaan",
    "Vikram", "Vivaan", "Yash", "Aniket", "Harsh", "Pranav", "Rishi", "Tarun",
    "Ananya", "Aanya", "Diya", "Ishita", "Kavya", "Meera", "Neha", "Pooja",
    "Priya", "Riya", "Saanvi", "Sakshi", "Shreya", "Sneha", "Tanvi", "Aditi",
    "Anjali", "Divya", "Nisha", "Radhika",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Shah", "Mehta",
    "Joshi", "Reddy", "Nair", "Iyer", "Menon", "Rao", "Pillai", "Chopra",
    "Kapoor", "Khanna", "Malhotra", "Bhatia", "Agarwal", "Mishra", "Tiwari",
    "Pandey", "Dubey", "Bose", "Chatterjee", "Banerjee", "Mukherjee", "Das",
    "Desai", "Mehra", "Saxena", "Trivedi", "Bansal", "Goyal",
]

DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]


def generate_user(existing_emails):
    while True:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        suffix = random.randint(10, 999)
        domain = random.choice(DOMAINS)
        email = f"{first.lower()}.{last.lower()}{suffix}@{domain}"
        if email not in existing_emails:
            return f"{first} {last}", email


def main():
    conn = get_db()
    try:
        rows = conn.execute("SELECT email FROM users").fetchall()
        existing_emails = {r["email"] for r in rows}

        name, email = generate_user(existing_emails)
        password_hash = generate_password_hash("password123")
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, created_at),
        )
        conn.commit()

        print(f"id:    {cursor.lastrowid}")
        print(f"name:  {name}")
        print(f"email: {email}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
