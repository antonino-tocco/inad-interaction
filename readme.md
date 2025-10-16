# INAD Interaction PA

> Strumento automatico per il recupero di indirizzi PEC tramite INAD e OpenAPI

## Descrizione

Questo tool consente di recuperare automaticamente gli indirizzi **PEC** (Posta Elettronica Certificata) di cittadini e aziende italiane, utilizzando due servizi integrati:

- **INAD** (Indice Nazionale dei Domicili Digitali) - Servizio GRATUITO per Codici Fiscali
- **OpenAPI SpA** - Servizio a PAGAMENTO per Partite IVA (30 richieste gratuite/mese)

### Caratteristiche principali

- Ricerca PEC tramite **Codice Fiscale** (16 caratteri) con INAD
- Ricerca PEC tramite **Partita IVA** (11 cifre) con OpenAPI
- Modalità **interattiva** per singole ricerche
- Modalità **batch** per elaborazione massiva da file Excel
- Gestione automatica delle priorità (INAD gratuito prima, OpenAPI a pagamento dopo)
- Validazione automatica dei codici fiscali e partite IVA
- Report dettagliato delle operazioni eseguite

---

## Prerequisiti

- Python 3.7 o superiore
- Chiave privata (formato PEM) per autenticazione INAD
- (Opzionale) API Key di OpenAPI per ricerca tramite Partita IVA

---

## Installazione

### 1. Clona o scarica il progetto

```bash
git clone <repository-url>
cd "inad interaction"
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Configura il file `.env`

Crea un file `.env` nella root del progetto con i seguenti parametri:

```env
# Configurazione INAD (OBBLIGATORIO)
KID=<your_key_id>
ISSUER=<your_issuer>
SUBJECT=<your_subject>
PURPOSE_ID=<your_purpose_id>
CLIENT_ID=<your_client_id>

# Configurazione OpenAPI (OPZIONALE - per ricerche tramite P.IVA)
OPENAPI_KEY=<your_openapi_key>
```

**Nota:** Per ottenere la chiave OpenAPI, registrati su [console.openapi.com](https://console.openapi.com/)

---

## Utilizzo

### Modalità Interattiva

Ricerca PEC per un **singolo Codice Fiscale**:

```bash
python inad_interaction.py --priv_key_path <percorso_chiave_privata> --fiscal_code <codice_fiscale>
```

**Esempio:**
```bash
python inad_interaction.py --priv_key_path ./keys/private_key.pem --fiscal_code RSSMRA80A01H501U
```

Ricerca PEC per una **singola Partita IVA**:

```bash
python inad_interaction.py --priv_key_path <percorso_chiave_privata> --p_iva <partita_iva>
```

**Esempio:**
```bash
python inad_interaction.py --priv_key_path ./keys/private_key.pem --p_iva 12485671007
```

---

### Modalità Batch

Elabora un **file Excel** contenente più codici fiscali e/o partite IVA:

```bash
python inad_interaction.py --priv_key_path <percorso_chiave_privata> \
  --input_file <percorso_file_input.xlsx> \
  --output_file <percorso_file_output.xlsx> \
  --fiscal_code_field "Codice Fiscale" \
  --p_iva_field "Partita IVA" \
  --pec_field "PEC"
```

**Esempio:**
```bash
python inad_interaction.py --priv_key_path ./keys/private_key.pem \
  --input_file ./data/clienti.xlsx \
  --output_file ./data/clienti_con_pec.xlsx \
  --fiscal_code_field "Codice Fiscale" \
  --p_iva_field "Partita IVA" \
  --pec_field "PEC"
```

**Requisiti del file Excel:**
- Formato: `.xlsx`
- Deve contenere almeno una colonna con codici fiscali O partite IVA
- Il tool aggiungerà/aggiornerà la colonna PEC specificata

---

### Test con OpenAPI

Per testare il servizio OpenAPI con una Partita IVA specifica:

```bash
python test_openapi.py <partita_iva>
```

**Esempio:**
```bash
python test_openapi.py 12485671007
```

---

## Parametri

| Parametro | Descrizione | Obbligatorio |
|-----------|-------------|--------------|
| `--priv_key_path` | Percorso alla chiave privata (formato PEM) | ✅ |
| `--fiscal_code` | Codice fiscale singolo da cercare | ❌ |
| `--p_iva` | Partita IVA singola da cercare | ❌ |
| `--input_file` | Percorso al file Excel di input | ❌ |
| `--output_file` | Percorso al file Excel di output | ❌ |
| `--fiscal_code_field` | Nome colonna Codici Fiscali (default: `codice fiscale`) | ❌ |
| `--p_iva_field` | Nome colonna Partite IVA (default: `codice fiscale`) | ❌ |
| `--pec_field` | Nome colonna PEC (default: `PEC`) | ❌ |

---

## Logica di Ricerca

Il tool utilizza una strategia **ottimizzata per costo**:

1. **PRIORITÀ 1 - INAD (GRATUITO):**
   - Cerca prima usando i codici fiscali a 16 caratteri tramite INAD
   - Verifica sia la colonna "Codice Fiscale" che "Partita IVA" (alcune P.IVA possono essere CF)

2. **PRIORITÀ 2 - OpenAPI (A PAGAMENTO):**
   - Solo se INAD non trova risultati, cerca con Partita IVA a 11 cifre tramite OpenAPI
   - Utilizza le 30 chiamate gratuite mensili prima di addebitare

3. **Skip automatico:**
   - Se la PEC è già presente, la riga viene saltata
   - Se mancano sia codice fiscale che partita IVA, la riga viene ignorata

---

## Output

Al termine dell'elaborazione in modalità batch, il tool fornisce un **report dettagliato**:

```
=== Summary ===
Total PECs retrieved: 87
  - From INAD (fiscal codes): 65
  - From OpenAPI (P.IVA): 22

Output saved to: ./data/clienti_con_pec.xlsx
```

---

## Note e Limitazioni

- **INAD**: Servizio gratuito, senza limiti di chiamate. Richiede autenticazione JWT con chiave privata.
- **OpenAPI**: 30 richieste gratuite al mese, poi servizio a pagamento. Richiede API Key.
- I codici fiscali devono essere **esattamente 16 caratteri** alfanumerici
- Le Partite IVA devono essere **esattamente 11 cifre** numeriche
- Il file Excel di output sovrascrive eventuali file esistenti con lo stesso nome

---

## Licenza

Questo progetto è fornito "as-is" per uso interno della Pubblica Amministrazione.

---

## Supporto

Per problemi o domande, consultare la documentazione ufficiale:
- [INAD - Indice Nazionale Domicili Digitali](https://www.inad.gov.it/)
- [OpenAPI SpA](https://console.openapi.com/)
