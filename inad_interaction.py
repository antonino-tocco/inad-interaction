import datetime
import os

import dotenv
import json
import numpy as np
import pandas as pd
import requests

from argparse import ArgumentParser
from jose import jwt
from jose.constants import Algorithms
from uuid import uuid4


dotenv.load_dotenv()


def client_assertion_constants(priv_key_path: str):
    KID = os.environ.get("KID")
    ALG = "RS256"
    TYP = "JWT"
    ISSUER = os.environ.get("ISSUER")
    SUBJECT = os.environ.get("SUBJECT")
    AUDIENCE = "auth.interop.pagopa.it/client-assertion"
    PURPOSE_ID = os.environ.get("PURPOSE_ID")
    KEY_PATH = priv_key_path
    return KID, ALG, TYP, ISSUER, SUBJECT, AUDIENCE, PURPOSE_ID, KEY_PATH

def get_private_key(key_path):
  with open(key_path, "rb") as private_key:
    encoded_string = private_key.read()
    return encoded_string

def retrieve_client_assertion(priv_key_path: str):
    issued = datetime.datetime.utcnow()
    delta = datetime.timedelta(minutes=43200)
    expire_in = issued + delta
    jti = uuid4()

    kid, alg, typ, issuer, subject, audience, purposeId, keyPath = client_assertion_constants(priv_key_path)

    headers_rsa = {
        "kid": kid,
        "alg": alg,
        "typ": typ
    }

    payload = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "purposeId": purposeId,
        "jti": str(jti),
        "iat": issued,
        "exp": expire_in
    }

    rsaKey = get_private_key(keyPath)

    client_assertion = jwt.encode(payload, rsaKey, algorithm=Algorithms.RS256, headers=headers_rsa)
    return client_assertion

def retrieve_voucher(priv_key_path: str):
    client_id = os.environ.get("CLIENT_ID")
    result = requests.post(
        "https://auth.interop.pagopa.it/token.oauth2",
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        data={
            'client_id': client_id,
            'client_assertion': retrieve_client_assertion(priv_key_path),
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'grant_type': 'client_credentials'
        }
    )
    if result.status_code == 200:
        token = result.json().get('access_token')
        return token
    else:
        raise Exception(f"Unable to retrieve voucher - Status code: {result.status_code}")


def retrieve_domicilio_digitale(voucher: str, fiscal_code: str):
    """
    Retrieve the digital domicile for a given fiscal code using the provided voucher.
    :param voucher:
    :param fiscal_code:
    :return:
    """
    assert(voucher is not None and fiscal_code is not None)
    url = f"https://api.inad.gov.it/rest/inad/v1/domiciliodigitale/extract/{fiscal_code}?practicalReference={uuid4()}"
    response = requests.get(url, headers={'Authorization': f'Bearer {voucher}'})
    if response.status_code == 200:
        result = response.json()
        data = result.get('digitalAddress', [])
        if not data:
            return 'No digital domicile found for this fiscal code'
        # Assuming the digital domicile is stored under the key 'domicilioDigitale'

        if len(data) > 0:
            domicilio_digitale = data[0].get('digitalAddress', 'N/A')
            return domicilio_digitale
    else:
        raise Exception(f"Unable to retrieve digital domicile data for {fiscal_code} - Status code: {response.status_code}")


def main(voucher: str = None, fiscal_codes_file: str = None, output_file: str = None, fiscal_code_field: str = 'codice fiscale', pec_field: str = 'PEC'):
    assert (voucher is not None and fiscal_codes_file is not None)
    if not os.path.exists(fiscal_codes_file):
        raise FileNotFoundError(f"The file {fiscal_codes_file} does not exist.")

    df = pd.read_excel(fiscal_codes_file, dtype=str)
    counter = 0
    for index, row in df.iterrows():
        fiscal_code = row[fiscal_code_field]
        pec = row[pec_field]
        # Check if PEC is empty or NaN
        if not pd.isna(fiscal_code) and pd.isna(pec):
            try:
                pec = retrieve_domicilio_digitale(voucher, fiscal_code)
                if pec is not None and pec != 'N/A':
                    df.at[index, pec_field] = pec
                    counter += 1
            except Exception as e:
                # print(f"Error retrieving PEC for fiscal code {fiscal_code}: {e}")
                df.at[index, pec_field] = ''
    print(f"Number of PECs retrieved: {counter}")
    if output_file is not None and os.path.exists(output_file) and os.path.isfile(output_file):
        os.remove(output_file)
    if output_file is None:
        base_output_file = os.path.splitext(fiscal_codes_file)[0]
        output_file = f"{base_output_file}_updated.xlsx"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_excel(output_file, index=False)


if __name__ == "__main__":
    parser = ArgumentParser(description="Retrieve Digital Domicile for given fiscal codes")
    parser.add_argument('--priv_key_path', type=str, required=True, help="Path to the private key file")
    parser.add_argument('--fiscal_code', type=str, required=False, help="Fiscal code to retrieve digital domicile for")
    parser.add_argument('--fiscal_codes_file', type=str, required=False, help="Path to a file containing fiscal codes (one per line)")
    parser.add_argument('--fiscal_code_field', type=str, default='codice fiscale', help="Column name for fiscal codes in the Excel file")
    parser.add_argument('--pec_field', type=str, default='PEC', help="Column name for PEC in the Excel file")
    parser.add_argument('--output_file', type=str, required=False, help="Path to save the output Excel file with updated PECs")
    args = parser.parse_args()
    voucher = retrieve_voucher(args.priv_key_path)
    if args.fiscal_code:
        domicilio = retrieve_domicilio_digitale(voucher, args.fiscal_code)
        print(f"Domicilio Digitale for {args.fiscal_code}: {domicilio}")
    else:
        fiscal_codes_file = args.fiscal_codes_file
        fiscal_code_field = args.fiscal_code_field
        pec_field = args.pec_field
        output_file = args.output_file
        main(voucher=voucher, fiscal_codes_file=fiscal_codes_file, output_file=output_file, fiscal_code_field=fiscal_code_field, pec_field=pec_field)