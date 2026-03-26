from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from flask_cors import CORS
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GEMINI_API_KEY")


def countPresents(data):
    print("Step 5: Calling Gemini")

    genai.configure(api_key=API_KEY)

    response = genai.GenerativeModel("gemini-2.5-flash").generate_content(
        data + " count total presents and absents. return only two numbers separated by space"
    )

    try:
        lis = response.text.split()
        return {
            "presents": lis[0],
            "absents": lis[1]
        }
    except:
        return {"error": "Failed to parse response"}


def scrape_attendance(username, password, subjectName):
    print("Step 1: Launching browser")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
            ]
        )

        page = browser.new_page()

        print("Step 2: Opening website")
        page.goto("http://sibagrades.iba-suk.edu.pk:86/Default.aspx")

        print("Step 3: Logging in")
        page.fill('input[name="txtuid"]', username)
        page.fill('input[name="txtpwd"]', password)
        page.click('input[type="submit"]')

        # Reduced wait time
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector('a[href="wpAttendance.aspx"]', timeout=15000)

        print("Step 4: Navigating to attendance")
        page.click('a[href="wpAttendance.aspx"]')

        page.select_option("#ContentPlaceHolder1_DpCmscourses", label=subjectName)
        page.click('input[name="ctl00$ContentPlaceHolder1$Button1"]')

        page.wait_for_timeout(2000)

        data = page.locator('#ctl00_ContentPlaceHolder1_RadGrid1_ctl00').inner_html()

        browser.close()
        return data


@app.route("/attendance", methods=["POST"])
def get_attendance():
    print("API HIT")

    body = request.json

    username = body.get("username")
    password = body.get("password")
    subject = body.get("subject")

    if not username or not password or not subject:
        return jsonify({"error": "Missing fields"}), 400

    try:
        html_data = scrape_attendance(username, password, subject)
        result = countPresents(html_data)
        return jsonify(result)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
