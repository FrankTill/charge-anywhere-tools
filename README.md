# Charge Anywhere Country Change Tool

A Flask web application for changing merchant country settings via the Charge Anywhere Partner Portal API.

## Features

- **Web Interface**: Clean, responsive UI for entering merchant information
- **Country Selection**: Dropdown with supported countries (US, Canada, Australia)
- **SOAP Integration**: Direct integration with Charge Anywhere API
- **Error Handling**: Comprehensive error handling and response parsing
- **Extensible Design**: Built to easily add more merchant update features
- **Docker Support**: Full containerization with Docker and Docker Compose

## Supported Countries

- United States (US) - Country Code: 840
- Canada (CA) - Country Code: 124
- Australia (AU) - Country Code: 036

## Installation

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd charge-anywhere-tools
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file and add your Charge Anywhere API credentials:
   ```env
   CHANNEL_NAME=your_actual_channel_name
   USERNAME=your_actual_username
   PASSWORD=your_actual_password
   ```

### Option 2: Docker Installation

The application can also be run using Docker for easy deployment and management.

#### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

#### Quick Start with Docker

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` file and add your Charge Anywhere API credentials.

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

1. **Run the application**
   
   **Local:**
   ```bash
   python app.py
   # or
   python run.py
   ```
   
   **Docker:**
   ```bash
   docker-compose up --build
   ```

2. **Access the web interface**
   Open your browser and navigate to `http://localhost:5000`

3. **Change merchant country**
   - Enter the Merchant ID (MID) in the text field
   - Select a country from the dropdown
   - Click "Change Country" button
   - View the API response

## Docker Commands

#### Build the Docker image only
```bash
docker build -t charge-anywhere-tool .
```

#### Run container from built image
```bash
docker run -p 5000:5000 --env-file .env charge-anywhere-tool
```

#### Run in detached mode
```bash
docker compose up -d --build
```

#### View logs
```bash
docker-compose logs -f charge-anywhere-app
```

#### Stop the application
```bash
docker-compose down
```

#### Remove containers and networks
```bash
docker-compose down --volumes --remove-orphans
```

## API Endpoints

- `GET /` - Main page with country change form
- `POST /update_country` - API endpoint for country changes
- `GET /health` - Health check endpoint

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CHANNEL_NAME` | Charge Anywhere channel name | Yes |
| `USERNAME` | API username | Yes |
| `PASSWORD` | API password | Yes |

### SOAP Request Structure

The application sends SOAP requests with the following structure:

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Body>
        <Create_Update_MerchantInfo xmlns="http://www.chargeanywhere.com/">
            <channelCredentials>
                <ChannelName>{CHANNEL_NAME}</ChannelName>
                <UserName>{USERNAME}</UserName>
                <Password>{PASSWORD}</Password>
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
</soap12:Envelope>
```

## Response Handling

The application handles two types of responses:

### Success Response (ResponseCode: 1)
```xml
<ResponseCode>1</ResponseCode>
<ResponseText>SUCCESS. Update Merchant Info.</ResponseText>
```

### Error Response (ResponseCode: ≠ 1)
```xml
<ResponseCode>175</ResponseCode>
<ResponseText>An open batch exists for this device. Please close the batch then try again!.</ResponseText>
```

## Error Handling

- **Form Validation**: Client-side and server-side validation for required fields
- **API Errors**: Handles network timeouts, HTTP errors, and API response errors
- **XML Parsing**: Robust XML parsing with error handling for malformed responses
- **User Feedback**: Clear error messages displayed in the UI

## Development

### Project Structure
```
charge-anywhere-tools/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Docker build ignore file
├── .env.example          # Environment variables template
├── run.py                # Startup script with checks
├── README.md             # Documentation
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Custom styles
    └── js/
        └── app.js        # JavaScript functionality
```

### Docker Configuration

The Docker setup includes:
- **Health checks**: Automatic container health monitoring
- **Restart policy**: Containers automatically restart unless stopped
- **Network isolation**: Application runs in isolated network
- **Security**: Non-root user execution
- **Volume mounting**: Environment file mounted as read-only

### Adding New Features

The application is designed to be easily extensible:

1. **New Countries**: Add to the `COUNTRIES` dictionary in `app.py`
2. **New API Methods**: Add new routes and SOAP request functions
3. **New Form Fields**: Update the HTML template and form handling

## Security Notes

- **Credentials**: Never commit `.env` file to version control
- **HTTPS**: In production, ensure the application runs over HTTPS
- **Input Validation**: All user inputs are validated on both client and server side
- **Docker**: Container runs with non-root user for security

## Testing

### Local Testing
1. Set up the environment variables in `.env`
2. Run the Flask application
3. Test with valid merchant IDs for your account
4. Check the API responses in the web interface

### Docker Testing
```bash
# Test the container
docker-compose up --build

# Check health endpoint
curl http://localhost:5000/health

# View container logs
docker-compose logs -f charge-anywhere-app
```

## Troubleshooting

### Common Issues

#### Environment variables not loaded
```bash
# Verify .env file exists and has correct format
cat .env

# In Docker, check if variables are being read
docker-compose config
```

#### Container won't start
```bash
# Check container logs
docker-compose logs charge-anywhere-app

# Check if port is already in use
lsof -i :5000
```

#### Health check failures
```bash
# Manually test health endpoint
curl http://localhost:5000/health
```

## Production Deployment

For production deployment, consider:

1. **Use environment-specific .env files**
   ```bash
   cp .env.production .env
   ```

2. **Reverse proxy with Nginx**
   Configure Nginx to proxy requests to the container

3. **SSL/HTTPS**
   Terminate SSL at the load balancer or reverse proxy

4. **Database** (if needed)
   Add database services to docker-compose.yml

5. **Monitoring**
   Add monitoring services like Prometheus/Grafana

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For Charge Anywhere API support, contact their technical support team.