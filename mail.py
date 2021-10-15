import os
import sys
import logging
import json


from dotenv import load_dotenv

from fastapi.param_functions import Header
from fastapi import (
    Security,
    FastAPI,
    Body,
    HTTPException,
    Depends,
    Response,
    status,
)
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from pydantic.class_validators import validator

from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse

# from starlette.testclient import TestClient

from pydantic import BaseModel, ValidationError, MissingError

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from lib.read_template import read_template
from lib.send_mail import send_mail

load_dotenv()

DEPLOYMENT_ENVIRONMENT = os.getenv("ENVIRONMENT")

API_KEY_NAME = os.getenv("API_KEY_NAME")
API_KEY = os.getenv("API_KEY")

API_KEY_QUERY = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
API_KEY_COOKIE = APIKeyCookie(name=API_KEY_NAME, auto_error=False)


async def get_api_key(
    api_key_query: str = Security(API_KEY_QUERY),
    api_key_header: str = Security(API_KEY_HEADER),
    api_key_cookie: str = Security(API_KEY_COOKIE),
):

    if api_key_query == API_KEY:
        return api_key_query
    elif api_key_header == API_KEY:
        return api_key_header
    elif api_key_cookie == API_KEY:
        return api_key_cookie
    else:
        logging.debug("Credential Validation Failed")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


if DEPLOYMENT_ENVIRONMENT is None:
    loglevel = "INFO"
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
if DEPLOYMENT_ENVIRONMENT == "DEVELOPMENT":
    loglevel = "DEBUG"
    app = FastAPI()
if DEPLOYMENT_ENVIRONMENT == "PRODUCTION":
    loglevel = "INFO"
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
    # filename=log_file,
    # encoding=log_encoding,
    level=getattr(logging, loglevel.upper()),
)
logger = logging.getLogger(__name__)


class EmailData(BaseModel):
    mail_connection_parameters: dict
    mail_headers: dict
    app_data: dict


@app.get("/ping", status_code=status.HTTP_200_OK, description="Liveliness Check")
async def ping():
    return {"ping": "pong"}


@app.post(
    "/send_email",
    status_code=status.HTTP_200_OK,
    description="Sends email with specified credentials and application data using a specified template.",
)
async def send_email(
    data: EmailData,
    response: Response,
    api_key: APIKey = Depends(get_api_key),
):
    if not (
        all(
            key in data.mail_connection_parameters
            for key in ("host", "port", "login", "password")
        )
        and all(
            key in data.mail_headers for key in ("From", "To", "Subject", "Reply-To")
        )
        and "email_template" in data.app_data
    ):
        logger.debug("Required number of arguments are not present")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"message": "Invalid number of arguments"}

    message_template = read_template("templates/" + data.app_data["email_template"])

    if message_template is False:
        logger.debug("Can not open message template")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": "Can not open message template"}

    # create a mime message
    msg = MIMEMultipart()

    # substitue the variables in the template
    message = message_template.substitute(
        CUSTOMER_NAME=data.app_data["customer_name"],
        ORDER_NUMBER=data.app_data["order_number"],
    )

    # setup the parameters of the message
    msg["From"] = data.mail_headers["From"]
    msg["To"] = data.mail_headers["To"]
    msg["Subject"] = data.mail_headers["Subject"]
    msg["Reply-To"] = data.mail_headers["Reply-To"]

    # add in the message body
    # msg.attach(MIMEText(message, "plain"))
    msg.attach(MIMEText(message, "html"))

    if send_mail(
        data.mail_connection_parameters["host"],
        data.mail_connection_parameters["port"],
        data.mail_connection_parameters["login"],
        data.mail_connection_parameters["password"],
        msg,
    ):
        logger.debug("Mail Sent Successfully...")
        return {
            "message": f'Email sent successfully to {data.mail_headers["To"]} for order number {data.app_data["order_number"]}'
        }
    else:
        logger.debug("Error sending email...")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            "message": f'Email could not be send to {data.mail_headers["To"]} for order number {data.app_data["order_number"]}'
        }
