# Modulo rigman/Console

_Ultima revisione: 15 luglio 2022_

_rigman_ è un modulo che serve al manutentore per interfacciarsi col RIG e ottenere informazioni diagnostiche.

Il software offre all'utente un'interfaccia da linea di comando guidata e intuitiva.

Le funzioni implementate da _rigman_ sfruttano la Console per comunicare con _rigproc_ via socket.\
L'implementazione di tali funzioni è contenuta nella cartella `utilities`.

## Operazioni rapide

_rigman_ offre alcune opzioni rapide, accessibili tramite l'aggiunta di opzioni all'avvio.\
Alucne opzioni, come `--stop`, che consente di inviare un segnale di arresto a _rigproc_, inibiscono l'avvio dell'interfaccia da linea di comando.
