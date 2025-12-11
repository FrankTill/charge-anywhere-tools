import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Country mapping
COUNTRIES = {
    "US": {"code": "840", "name": "United States"},
    "CA": {"code": "124", "name": "Canada"},
    "AU": {"code": "036", "name": "Australia"},
}


def create_soap_request(merchant_id, country_code):
    """Create SOAP XML request for merchant update"""
    # Get credentials from environment
    channel_name = os.getenv("CHANNEL_NAME")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    if not all([channel_name, username, password]):
        raise ValueError("Missing required credentials in .env file")

    # Build SOAP envelope
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Body>
        <Create_Update_MerchantInfo xmlns="http://www.chargeanywhere.com/">
            <channelCredentials>
                <ChannelName>{channel_name}</ChannelName>
                <UserName>{username}</UserName>
                <Password>{password}</Password>
            </channelCredentials>
            <merchantInfo xsi:type="ChargeAnyWhereMerchantInfo">
                <MerchantId>{merchant_id}</MerchantId>
                <IndustryTypeId>0</IndustryTypeId>
                <DuplicateCheck>0</DuplicateCheck>
                <CountryCode>{country_code}</CountryCode>
                <CurrencyCode>{country_code}</CurrencyCode>
                <SettlementOptions>2</SettlementOptions>
                <AutoSettle>1</AutoSettle>
                <SettlementTime>0</SettlementTime>
                <SupportsPinDebit>1</SupportsPinDebit>
                <EMV_App_Select_Opt>3</EMV_App_Select_Opt>
                <AutoSettleAuthOnly>0</AutoSettleAuthOnly>
            </merchantInfo>
        </Create_Update_MerchantInfo>
    </soap12:Body>
</soap12:Envelope>"""

    return soap_envelope


def parse_soap_response(response_text):
    """Parse SOAP response and extract response code and text"""
    try:
        # Parse XML response
        root = ET.fromstring(response_text)

        # Find the response elements using namespace
        namespace = {
            "soap": "http://www.w3.org/2003/05/soap-envelope",
            "ca": "http://www.chargeanywhere.com/",
        }

        response_code = root.find(".//ca:ResponseCode", namespace)
        response_text_elem = root.find(".//ca:ResponseText", namespace)

        if response_code is not None and response_text_elem is not None:
            return {
                "success": True,
                "response_code": response_code.text,
                "response_text": response_text_elem.text,
            }
        else:
            return {
                "success": False,
                "response_code": "Unknown",
                "response_text": "Could not parse response",
            }
    except Exception as e:
        return {
            "success": False,
            "response_code": "Parse Error",
            "response_text": f"Error parsing response: {str(e)}",
        }


@app.route("/")
def index():
    """Main page with form"""
    return render_template("index.html", countries=COUNTRIES)


@app.route("/update_country", methods=["POST"])
def update_country():
    """Handle country update request"""
    try:
        # Get form data
        merchant_id = request.form.get("merchant_id", "").strip()
        country_key = request.form.get("country", "").strip()

        # Validate inputs
        if not merchant_id:
            return jsonify({"success": False, "error": "Merchant ID is required"}), 400

        if country_key not in COUNTRIES:
            return (
                jsonify({"success": False, "error": "Invalid country selection"}),
                400,
            )

        country_code = COUNTRIES[country_key]["code"]

        # Create SOAP request
        soap_request = create_soap_request(merchant_id, country_code)

        # Send request to API
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://www.chargeanywhere.com/Create_Update_MerchantInfo",
        }

        api_url = "https://webtest.chargeanywhere.com/PartnerPortalAPI/PartnerPortalAPI.asmx?WSDL"

        response = requests.post(
            api_url, data=soap_request, headers=headers, timeout=30
        )

        # Parse response
        result = parse_soap_response(response.text)

        return jsonify(
            {
                "success": True,
                "merchant_id": merchant_id,
                "country": COUNTRIES[country_key]["name"],
                "response_code": result["response_code"],
                "response_text": result["response_text"],
                "is_success": result["response_code"] == "1",
            }
        )

    except requests.RequestException as e:
        return (
            jsonify({"success": False, "error": f"API request failed: {str(e)}"}),
            500,
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
