 # ING Bank to YNAB

 This tool can be used to convert Dutch ING transactions towards a format that can be handled by You Need a Budget (YNAB).
 The GUI (based on TKinter) reads .csv files from a directory and converts them to .csv files recognized by YNAB.

 In addition, categories can be automatically extracted based on payee or memo (omschrijving/mededelingen).
 A generic JSON (database.json) file is used to store payee/category information.

        Input Format:
        Datum,Naam / Omschrijving,Rekening,Tegenrekening,Code,Af Bij,Bedrag (EUR),MutatieSoort,Mededelingen

        Output Format:
        Date,Payee,Category,Memo,Outflow,Inflow
        07/25/10,Sample Payee,(Master)Category,Sample Memo for an outflow,100.00,
        07/25/10,Sample Payee,(Master)Category,Sample Memo for an inflow,,100.00

# How to use

1. Clone repository
2. Create database.json file
3. Run app
