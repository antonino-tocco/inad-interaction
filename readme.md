# INAD INTERACTION PA

This package provide tool to INAD (Indice Nazionale dei Domicili Digitali).

It allows to interact with INAD API to manage digital addresses.

## Installation

You can install dependencies with pip:

```bash
pip install -r requirements.txt
```

## Usage

You can use the script provided in interactive or batch mode.

### Interactive Mode

Run the script with:

```bash
python inad_interaction.py --priv_key_path <path_to_private_key> --fiscal_code <fiscal_code>
```


### Batch Mode

Run the script with:

```bash
python inad_interaction.py --priv_key_path <path_to_private_key> --fiscal_codes_file <path_to_file> --output_file <path_to_output_file> --fiscal_code_field <field_name> --pec_field <field_name>
```

The input file should be a XLSX file with a column containing fiscal codes and another column containing PEC addresses.
The output file will be a XLSX file with the results of the operations.

### Arguments

- `--priv_key_path`: Path to the private key file (PEM format).
- `--fiscal_code`: Fiscal code of the user (for interactive mode).
- `--fiscal_codes_file`: Path to the input file containing fiscal codes (for batch mode).
- `--output_file`: Path to the output file to save results (for batch mode).
- `--fiscal_code_field`: Name of the column containing fiscal codes in the input file (for batch mode).
- `--pec_field`: Name of the column containing PEC addresses in the input file (for batch mode).

