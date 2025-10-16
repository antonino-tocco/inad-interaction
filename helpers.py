import os
import requests
from uuid import uuid4


def validate_partita_iva(p_iva: str) -> bool:
    """
    Validate Italian Partita IVA format (11 digits).
    :param p_iva: Partita IVA to validate
    :return: True if valid, False otherwise
    """
    if not p_iva or not isinstance(p_iva, str):
        return False

    # Remove any spaces or special characters
    p_iva = p_iva.strip().replace(" ", "")

    # Must be exactly 11 digits
    if len(p_iva) != 11 or not p_iva.isdigit():
        return False

    return True


def validate_fiscal_code(fiscal_code: str) -> bool:
    """
    Validate Italian fiscal code format (16 characters).
    :param fiscal_code: Fiscal code to validate
    :return: True if valid, False otherwise
    """
    if not fiscal_code or not isinstance(fiscal_code, str):
        return False

    # Remove any spaces
    fiscal_code = fiscal_code.strip().replace(" ", "")

    # Must be exactly 16 alphanumeric characters
    if len(fiscal_code) != 16 or not fiscal_code.isalnum():
        return False

    return True


def retrieve_domicilio_digitale(voucher: str, fiscal_code: str):
    """
    Retrieve the digital domicile for a given fiscal code using INAD API (FREE).
    :param voucher: INAD authentication voucher
    :param fiscal_code: Italian fiscal code (16 characters)
    :return: PEC address or None/error message if not found
    """
    assert(voucher is not None and fiscal_code is not None)

    if not validate_fiscal_code(fiscal_code):
        raise Exception(f"Invalid fiscal code format: {fiscal_code}")

    url = f"https://api.inad.gov.it/rest/inad/v1/domiciliodigitale/extract/{fiscal_code}?practicalReference={uuid4()}"
    response = requests.get(url, headers={'Authorization': f'Bearer {voucher}'})

    if response.status_code == 200:
        result = response.json()
        data = result.get('digitalAddress', [])
        if not data:
            return None

        if len(data) > 0:
            domicilio_digitale = data[0].get('digitalAddress', None)
            return domicilio_digitale
    else:
        raise Exception(f"Unable to retrieve digital domicile data for {fiscal_code} - Status code: {response.status_code} {response.text}")


def retrieve_pec_from_openapi(p_iva: str) -> str:
    """
    Retrieve PEC address for a Partita IVA using OpenAPI SpA service (PAID - 30 free/month).
    :param p_iva: Partita IVA (11 digits)
    :return: PEC address or None if not found
    """
    api_key = os.environ.get("OPENAPI_KEY")
    if not api_key or api_key == "your_openapi_key_here":
        raise Exception("OpenAPI key not configured. Please set OPENAPI_KEY in .env file. Get your key from https://console.openapi.com/")

    if not validate_partita_iva(p_iva):
        raise Exception(f"Invalid Partita IVA format: {p_iva}")

    url = f"https://company.openapi.com/IT-pec/{p_iva}"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and result.get('data'):
                data = result['data']
                # Handle both list and dict responses
                if isinstance(data, list):
                    # If data is a list, get the first item
                    if len(data) > 0:
                        pec = data[0].get('pec') if isinstance(data[0], dict) else None
                    else:
                        pec = None
                elif isinstance(data, dict):
                    # If data is a dict, get pec directly
                    pec = data.get('pec')
                else:
                    pec = None
                return pec if pec else None
            else:
                return None
        elif response.status_code == 404:
            return None
        else:
            raise Exception(f"OpenAPI error - Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.Timeout:
        raise Exception(f"OpenAPI request timeout for P.IVA {p_iva}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenAPI request failed for P.IVA {p_iva}: {str(e)}")

