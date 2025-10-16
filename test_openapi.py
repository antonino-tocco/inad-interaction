"""
Test script for OpenAPI PEC retrieval
Usage: python test_openapi.py <partita_iva>
Example: python test_openapi.py 12485671007
"""

import os
import sys
import dotenv
from helpers import retrieve_pec_from_openapi, validate_partita_iva

# Load environment variables
dotenv.load_dotenv()


def test_openapi_pec_retrieval(p_iva: str):
    """
    Test OpenAPI PEC retrieval for a single Partita IVA.
    :param p_iva: Partita IVA to test (11 digits)
    """
    print("=" * 60)
    print("OpenAPI PEC Retrieval Test")
    print("=" * 60)
    print(f"\nTesting P.IVA: {p_iva}")
    print("-" * 60)

    # Validate format
    if not validate_partita_iva(p_iva):
        print(f"ERROR: Invalid Partita IVA format!")
        print(f"  - Must be exactly 11 digits")
        print(f"  - Provided: '{p_iva}' (length: {len(p_iva)})")
        return False

    print(f"✓ Format validation: PASSED")

    # Check API key
    api_key = os.environ.get("OPENAPI_KEY")
    if not api_key or api_key == "your_openapi_key_here":
        print(f"\nERROR: OpenAPI key not configured!")
        print(f"  - Please set OPENAPI_KEY in .env file")
        print(f"  - Get your key from: https://console.openapi.com/")
        return False

    print(f"✓ API key configured: {api_key[:10]}...")

    # Test retrieval
    print(f"\nAttempting to retrieve PEC...")
    try:
        pec = retrieve_pec_from_openapi(p_iva)

        if pec:
            print(f"\n{'=' * 60}")
            print(f"SUCCESS!")
            print(f"{'=' * 60}")
            print(f"Partita IVA: {p_iva}")
            print(f"PEC Address: {pec}")
            print(f"{'=' * 60}")
            return True
        else:
            print(f"\nINFO: No PEC found for P.IVA {p_iva}")
            print(f"  - The P.IVA may not be registered")
            print(f"  - Or it may not have a public PEC address")
            return False

    except Exception as e:
        print(f"\nERROR: Failed to retrieve PEC")
        print(f"  - Error: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_openapi.py <partita_iva>")
        print("Example: python test_openapi.py 12485671007")
        sys.exit(1)

    p_iva = sys.argv[1].strip()
    success = test_openapi_pec_retrieval(p_iva)

    sys.exit(0 if success else 1)
