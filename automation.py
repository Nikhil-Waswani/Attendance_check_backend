from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
from google import genai
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)   # ✅ enable CORS for Flutter Web

# 🔐 use env variable in production
API_KEY = 'AIzaSyC1Y4oDieZQnMFaV1gutHkeCpn62MTSGjg'


def countPresents(data):
    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=data + " count total presents and absents. return only two numbers separated by space"
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://sibagrades.iba-suk.edu.pk:86/Default.aspx")

        page.fill('input[name="txtuid"]', username)
        page.fill('input[name="txtpwd"]', password)

        page.click('input[type="submit"]')

        # ✅ wait properly after login
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('a[href="wpAttendance.aspx"]', timeout=60000)

        page.click('a[href="wpAttendance.aspx"]')

        page.select_option("#ContentPlaceHolder1_DpCmscourses", label=subjectName)
        page.click('input[name="ctl00$ContentPlaceHolder1$Button1"]')

        page.wait_for_timeout(3000)

        data = page.locator('#ctl00_ContentPlaceHolder1_RadGrid1_ctl00').inner_html()

        browser.close()

        return data


@app.route("/attendance", methods=["POST"])
def get_attendance():
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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # ✅ for Railway
    app.run(host="0.0.0.0", port=port)