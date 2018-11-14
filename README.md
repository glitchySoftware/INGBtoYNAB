 INGBtoYNAB

 This tool can be used to convert Dutch ING transaction towards You Need a Budget (YNAB)
 The tool reads .csv files from ING and converts them to .csv files recognized by YNAB.

 In addition, categories can be automatically extracted based on payee or memo (omschrijving/mededelingen).

        Input Format:
        Datum,Naam / Omschrijving,Rekening,Tegenrekening,Code,Af Bij,Bedrag (EUR),MutatieSoort,Mededelingen

        Output Format:
        Date,Payee,Category,Memo,Outflow,Inflow
        07/25/10,Sample Payee,(Master)Category,Sample Memo for an outflow,100.00,
        07/25/10,Sample Payee,(Master)Category,Sample Memo for an inflow,,100.00

