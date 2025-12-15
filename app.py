import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pytz
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Country mapping
COUNTRIES = {
    "US": {"code": "840", "name": "United States"},
    "CA": {"code": "124", "name": "Canada"},
    "AU": {"code": "036", "name": "Australia"},
}


def get_ny_timezone():
    """Get New York timezone"""
    return pytz.timezone("America/New_York")


def format_ny_date(date_obj):
    """Format date in NY timezone as mm/dd/yyyy"""
    ny_tz = get_ny_timezone()
    ny_time = date_obj.astimezone(ny_tz)
    return ny_time.strftime("%m/%d/%Y")


def get_ny_dates():
    """Get current NY date and yesterday's NY date for batch export"""
    ny_tz = get_ny_timezone()
    now_utc = datetime.now(pytz.UTC)
    now_ny = now_utc.astimezone(ny_tz)

    # Current day in NY timezone
    today_ny = now_ny.date()

    # Yesterday in NY timezone
    yesterday_ny = today_ny - timedelta(days=1)
    tomorrow_ny = today_ny + timedelta(days=1)

    return {
        "date_from": format_ny_date(
            datetime.combine(yesterday_ny, datetime.min.time()).replace(tzinfo=ny_tz)
        ),
        "date_to": format_ny_date(
            datetime.combine(tomorrow_ny, datetime.min.time()).replace(tzinfo=ny_tz)
        ),
    }


def create_soap_request(merchant_id, country_code):
    """Create SOAP XML request for merchant update"""
    logger.info(
        f"Creating SOAP request for merchant {merchant_id} with country code {country_code}"
    )

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


def get_batch_export_data(terminal_id):
    """Get batch export data to extract EMID and identification"""
    logger.info(f"Calling batch export API for TID: {terminal_id}")

    try:
        # Get credentials from environment
        client_key = os.getenv("CLIENT_KEY")
        client_secret = os.getenv("CLIENT_SECRET")

        if not all([client_key, client_secret]):
            raise ValueError("Missing CLIENT_KEY or CLIENT_SECRET in .env file")

        # Get NY dates
        ny_dates = get_ny_dates()
        logger.info(
            f"Using NY dates - From: {ny_dates['date_from']}, To: {ny_dates['date_to']}"
        )

        # Prepare form data
        form_data = {
            "ClientKey": client_key,
            "ClientSecret": client_secret,
            "DateFrom": ny_dates["date_from"],
            "DateTo": ny_dates["date_to"],
            "Version": "1.7",
            "Fields": "EMID,TerminalId,Identification",
        }

        # Send request to batch export API
        export_url = "https://webtest.chargeanywhere.com/apis/Transactions_Export.aspx"
        logger.info(f"POST request to: {export_url}")

        response = requests.post(export_url, data=form_data, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Batch export API returned status code {response.status_code}"
            )

        logger.info("Batch export API call successful, parsing response")

        # Parse response - it's CSV format
        lines = response.text.strip().split("\n")
        logger.debug(f"First few lines of response: {lines[:5]}")  # Debug output
        if not lines:
            raise Exception("No data returned from batch export")

        # Iterate through all lines to find matching TID
        matching_record = None
        lines_processed = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse CSV: EMID,TerminalId,Identification
            parts = line.split(",")
            if len(parts) < 3:
                continue  # Skip invalid lines

            emid = parts[0].strip()
            returned_terminal_id = parts[1].strip()
            identification = parts[2].strip()
            lines_processed += 1

            logger.debug(
                f"Processing line {lines_processed}: EMID={emid}, TerminalId={returned_terminal_id}, Identification={identification}"
            )

            # Check if identification matches the terminal ID provided by user
            if identification == terminal_id:
                logger.info(f"Found matching record for TID {terminal_id}")
                matching_record = {
                    "emid": emid,
                    "terminal_id": returned_terminal_id,
                    "identification": identification,
                }
                break

        if matching_record is None:
            logger.error(
                f"No matching record found for TID: {terminal_id} after processing {lines_processed} lines"
            )
            raise Exception(f"No matching record found for TID: {terminal_id}")

        logger.info(
            f"Successfully retrieved batch data: EMID={matching_record['emid']}, TerminalId={matching_record['terminal_id']}"
        )
        return matching_record

    except Exception as e:
        logger.error(f"Batch export failed: {str(e)}")
        raise Exception(f"Batch export failed: {str(e)}")


def close_batch(emid, terminal_id, identification):
    """Close the batch using the Transaction API"""
    logger.info(f"Calling close batch API for EMID: {emid}, TID: {terminal_id}")

    try:
        # Prepare JSON payload
        payload = {
            "MerchantId": emid,
            "TerminalId": terminal_id,
            "Identification": identification,
            "TransactionType": "CloseBatch",
            "VersionNumber": "2.6",
        }

        # Send request to transaction API
        api_url = "https://webtest.chargeanywhere.com/apis/api/Transaction"
        headers = {"Content-Type": "application/json"}

        logger.info(f"POST request to: {api_url}")
        logger.info(f"Payload: {payload}")

        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Close batch API returned status code {response.status_code}"
            )

        # Parse JSON response
        result = response.json()
        response_code = result.get("ResponseCode", "")
        response_text = result.get("ResponseText", "")

        logger.info(
            f"Close batch response - Code: {response_code}, Text: {response_text}"
        )

        return {
            "success": response_code == "000",
            "response_code": response_code,
            "response_text": response_text,
        }

    except Exception as e:
        logger.error(f"Close batch failed: {str(e)}")
        raise Exception(f"Close batch failed: {str(e)}")


@app.route("/")
def index():
    """Main page with form"""
    logger.info("Serving main page")
    return render_template("index.html", countries=COUNTRIES)


@app.route("/update_country", methods=["POST"])
def update_country():
    """Handle country update request"""
    logger.info("Received country update request")

    try:
        # Get form data
        merchant_id = request.form.get("merchant_id", "").strip()
        terminal_id = request.form.get("terminal_id", "").strip()
        country_key = request.form.get("country", "").strip()

        logger.info(
            f"Request data - MID: {merchant_id}, TID: {terminal_id}, Country: {country_key}"
        )

        # Validate inputs
        if not merchant_id:
            return jsonify({"success": False, "error": "Merchant ID is required"}), 400

        if not terminal_id:
            return jsonify({"success": False, "error": "Terminal ID is required"}), 400

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

        logger.info(f"Calling merchant update API: {api_url}")

        response = requests.post(
            api_url, data=soap_request, headers=headers, timeout=30
        )

        # Parse response
        result = parse_soap_response(response.text)

        logger.info(
            f"Initial API response - Code: {result['response_code']}, Text: {result['response_text']}"
        )

        # Check if we got error code 175 (open batch exists)
        if result["response_code"] == "175":
            logger.info(
                "Received error code 175 - open batch exists. Initiating batch closing process."
            )
            batch_closed = False
            batch_close_error = None

            try:
                # Get batch export data
                logger.info("Step 1: Getting batch export data")
                export_data = get_batch_export_data(terminal_id)

                # Close the batch
                logger.info("Step 2: Closing batch")
                close_result = close_batch(
                    export_data["emid"],
                    export_data["terminal_id"],
                    export_data["identification"],
                )

                if close_result["success"]:
                    batch_closed = True
                    logger.info("Batch closed successfully. Retrying merchant update.")
                    # Retry the original country update
                    retry_response = requests.post(
                        api_url, data=soap_request, headers=headers, timeout=30
                    )
                    result = parse_soap_response(retry_response.text)
                    logger.info(
                        f"Retry API response - Code: {result['response_code']}, Text: {result['response_text']}"
                    )
                else:
                    batch_close_error = f"Batch close failed: {close_result['response_code']} - {close_result['response_text']}"
                    logger.error(f"Batch close failed: {batch_close_error}")

            except Exception as e:
                batch_close_error = str(e)
                logger.error(f"Batch closing process failed: {batch_close_error}")

            return jsonify(
                {
                    "success": True,
                    "merchant_id": merchant_id,
                    "terminal_id": terminal_id,
                    "country": COUNTRIES[country_key]["name"],
                    "response_code": result["response_code"],
                    "response_text": result["response_text"],
                    "is_success": result["response_code"] == "1",
                    "batch_closed": batch_closed,
                    "batch_close_error": batch_close_error,
                }
            )

        # Normal response (not error code 175)
        logger.info("No batch closing needed - normal response")
        return jsonify(
            {
                "success": True,
                "merchant_id": merchant_id,
                "terminal_id": terminal_id,
                "country": COUNTRIES[country_key]["name"],
                "response_code": result["response_code"],
                "response_text": result["response_text"],
                "is_success": result["response_code"] == "1",
            }
        )

    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return (
            jsonify({"success": False, "error": f"API request failed: {str(e)}"}),
            500,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


@app.route("/health")
def health():
    """Health check endpoint"""
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
