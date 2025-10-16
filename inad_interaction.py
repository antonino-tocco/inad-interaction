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
from helpers import (
    validate_partita_iva,
    validate_fiscal_code,
    retrieve_domicilio_digitale,
    retrieve_pec_from_openapi
)


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


def main(voucher: str = None, input_file: str = None, output_file: str = None, fiscal_code_field: str = None, p_iva_field: str = None, pec_field: str = 'PEC'):
    assert (voucher is not None and input_file is not None)
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"The file {input_file} does not exist.")

    df = pd.read_excel(input_file, dtype=str)
    counter = 0
    counter_inad = 0
    counter_openapi = 0
    print(f"Processing file: {input_file}, total rows: {len(df)}")

    for index, row in df.iterrows():
        fiscal_code = row[fiscal_code_field] if fiscal_code_field in df.columns and not pd.isna(row[fiscal_code_field]) else None
        p_iva = row[p_iva_field] if p_iva_field in df.columns and not pd.isna(row[p_iva_field]) else None
        pec = row[pec_field] if pec_field in df.columns and not pd.isna(row[pec_field]) else None

        # Skip if PEC already exists
        if pec:
            continue

        # Skip if both fiscal_code and p_iva are missing
        if not fiscal_code and not p_iva:
            continue

        try:
            retrieved_pec = None

            # Clean and validate fiscal code
            if fiscal_code:
                fiscal_code = str(fiscal_code).strip()

            # Clean and validate p_iva
            if p_iva:
                p_iva = str(p_iva).strip()

            # PRIORITY 1: Always try fiscal code first with INAD (FREE)
            # Try fiscal_code field if it's 16 characters
            if fiscal_code and validate_fiscal_code(fiscal_code):
                try:
                    retrieved_pec = retrieve_domicilio_digitale(voucher, fiscal_code)
                    if retrieved_pec:
                        df.at[index, pec_field] = retrieved_pec
                        print(f"[INAD/FREE] Retrieved PEC for fiscal code {fiscal_code}: {retrieved_pec}")
                        counter += 1
                        counter_inad += 1
                        continue
                except Exception as e:
                    print(f"[INAD] Lookup failed for {fiscal_code}: {str(e)}")

            # Try p_iva field if it's 16 characters (could be a fiscal code)
            if p_iva and validate_fiscal_code(p_iva):
                try:
                    retrieved_pec = retrieve_domicilio_digitale(voucher, p_iva)
                    if retrieved_pec:
                        df.at[index, pec_field] = retrieved_pec
                        print(f"[INAD/FREE] Retrieved PEC for fiscal code (from P.IVA field) {p_iva}: {retrieved_pec}")
                        counter += 1
                        counter_inad += 1
                        continue
                except Exception as e:
                    print(f"[INAD] Lookup failed for {p_iva}: {str(e)}")

            # PRIORITY 2: Try OpenAPI with Partita IVA (PAID - after free INAD attempts)
            # Try p_iva field if it's 11 digits
            if p_iva and validate_partita_iva(p_iva):
                try:
                    retrieved_pec = retrieve_pec_from_openapi(p_iva)
                    if retrieved_pec:
                        df.at[index, pec_field] = retrieved_pec
                        print(f"[OpenAPI/PAID] Retrieved PEC for P.IVA {p_iva}: {retrieved_pec}")
                        counter += 1
                        counter_openapi += 1
                        continue
                except Exception as e:
                    print(f"[OpenAPI] Lookup failed for {p_iva}: {str(e)}")

            # Try fiscal_code field if it's 11 digits (could be a P.IVA)
            if fiscal_code and validate_partita_iva(fiscal_code):
                try:
                    retrieved_pec = retrieve_pec_from_openapi(fiscal_code)
                    if retrieved_pec:
                        df.at[index, pec_field] = retrieved_pec
                        print(f"[OpenAPI/PAID] Retrieved PEC for P.IVA (from fiscal_code field) {fiscal_code}: {retrieved_pec}")
                        counter += 1
                        counter_openapi += 1
                        continue
                except Exception as e:
                    print(f"[OpenAPI] Lookup failed for {fiscal_code}: {str(e)}")

            # If nothing worked, mark as empty
            df.at[index, pec_field] = ''

        except Exception as e:
            print(f"Error processing row {index}: {str(e)}")
            df.at[index, pec_field] = ''

    print(f"\n=== Summary ===")
    print(f"Total PECs retrieved: {counter}")
    print(f"  - From INAD (fiscal codes): {counter_inad}")
    print(f"  - From OpenAPI (P.IVA): {counter_openapi}")

    if output_file is not None and os.path.exists(output_file) and os.path.isfile(output_file):
        os.remove(output_file)
    if output_file is None:
        base_output_file = os.path.splitext(input_file)[0]
        output_file = f"{base_output_file}_updated.xlsx"

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    df.to_excel(output_file, index=False)
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Retrieve Digital Domicile for given fiscal codes")
    parser.add_argument('--priv_key_path', type=str, required=True, help="Path to the private key file")
    parser.add_argument('--fiscal_code', type=str, required=False, help="Fiscal code to retrieve digital domicile for")
    parser.add_argument('--p_iva', type=str, required=False, help="P. Iva to retrieve digital domicile for")
    parser.add_argument('--input_file', type=str, required=False, help="Path to the input Excel file containing fiscal codes and/or partite IVA")
    parser.add_argument('--fiscal_code_field', type=str, default='codice fiscale', help="Column name for fiscal codes in the Excel file")
    parser.add_argument('--p_iva_field', type=str, default='codice fiscale',
                        help="Column name for partite IVA in the Excel file")
    parser.add_argument('--pec_field', type=str, default='PEC', help="Column name for PEC in the Excel file")
    parser.add_argument('--output_file', type=str, required=False, help="Path to save the output Excel file with updated PECs")
    args = parser.parse_args()
    voucher = retrieve_voucher(args.priv_key_path)
    if args.fiscal_code is not None:
        domicilio = retrieve_domicilio_digitale(voucher, args.fiscal_code)
        print(f"Domicilio Digitale for {args.fiscal_code}: {domicilio}")
    elif args.p_iva is not None:
        domicilio = retrieve_domicilio_digitale(voucher, args.p_iva)
        print(f"Domicilio Digitale for {args.p_iva}: {domicilio}")
    else:
        input_file = args.input_file
        fiscal_code_field = args.fiscal_code_field
        p_iva_field = args.p_iva_field
        pec_field = args.pec_field
        output_file = args.output_file
        main(voucher=voucher, input_file=input_file, output_file=output_file, fiscal_code_field=fiscal_code_field, p_iva_field=p_iva_field, pec_field=pec_field)