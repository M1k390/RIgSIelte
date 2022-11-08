# RIG

_Ultima revisione: 15 luglio 2022_

## Glossario

---

- **RIG**: il software presente in questa repository;
- **RIP**: il sistema hardware su cui viene eseguito il RIG;
- **IVIP**: impianto locale con cui il RIG si interfaccia;
- **STG**: server remoto in collegamento con il RIG.

## Introduzione

---

Il **RIG** è un software eseguito su sistemi a bordo binario, destinati alla cattura di immagini per la ricostruzione tridimensionale dei **pantografi** dei treni in transito, a fini diagnostici.

Il sistema su cui viene eseguito il RIG viene definito **RIP** e consiste in una scheda x86 che esegue Ubuntu Linux.

Il compito principale del RIP è di **ricevere le immagini** scattate dalle fotocamere presenti nell'impianto **IVIP** e **inviarle ad un server**, chiamato **STG**, insieme ad altre informazioni diagnostiche.

Altre funzioni svolte dal RIP sono:

- la raccolta di informazioni aggiuntive agli scatti, interrogando dei sensori;
- l'invio di eventuali anomalie all'STG, di qualsiasi componente all'interno dell'impianto;
- il salvataggio di un certo numero di scatti in mancanza di connessione con l'STG.

Il software RIG è scritto principalmente in **Python**.

## Panoramica della documentazione

---

In questa repository, è presente la cartella `docs`, che contiene la documentazione necessaria a comprendere il funzionamento del RIG e a mettere mano al codice.

Quando si fa riferimento ad un _documento_, si intende un file nella cartella `docs`, omettendo una eventuale estensione. Per esempio, il documento _Requisiti_ fa riferimento al file `docs/Requisiti.md`. Alcuni riferimenti ad un documento potrebbero essere provvisti di collegamento.

**N.B.: per una fruzione migliore della documentazione, si consiglia di visualizzare i file con estensione `.md` utilizzando un visualizzatore MarkDown.**

### Indice

- [Configurazione](docs/Configurazione.md): come funziona e come viene letto il file di configurazione.
- [Distribuzione](docs/Distribuzione.md): come generare dei file eseguibili ed effettuare degli aggiornamenti da remoto.
- [Impianto](docs/Impianto.md): com'è strutturato l'impianto IVIP.
- [Installazione](docs/Installazione.md): preparazione del sistema per la produzione.
- [Requisiti](docs/Requisiti.md): requisiti software da soddisfare per usufruire delle funzioni del RIG.
- _Moduli_: descrizione dei moduli del RIG e panoramica del codice
  - [rigboot](docs/Moduli/rigboot.md)
  - [rigcam](docs/Moduli/rigcam.md)
  - [rigman](docs/Moduli/rigman.md)
  - [rigproc](docs/Moduli/rigproc.md)

## Quickstart

---

### Installazione

Il software è scritto in Python, pertanto può essere eseguito **senza compilazione o installazione**.

Tuttavia, è necessario installare alcune dipendenze e strumenti aggiuntivi descritti nel documento [Requisiti](docs/Requisiti.md).

### MODULI

Il RIG è composto da quattro moduli:

- **rigboot** (RIG booter) si occupa di avviare _rigproc_ e controllare la sua corretta esecuzione;
- **rigcam** (RIG camera) gestisce le telecamere tramite le API Vimba;
- **rigman** (RIG manager) fornisce un'interfaccia per testare e configurare il Rig;
- **rigproc** (RIG process) controlla il flusso di operazioni del Rig e la comunicazione coi moduli hardware e software; è in grado di avviare autonomamente _rigcam_.

### ESECUZIONE

Dopo aver installato i componenti necessari, è possibile avviare il software.

Il metodo più rapido è avviare direttamente i singoli moduli tramite l'interprete Python e i file "di accesso" di ciascun modulo. Essi sono:

- **rigboot**: `src/rigboot/rigboot.py`;
- **rigcam**: `src/rigcam/main.py`;
- **rigman**: `src/rigman/main.py`;
- **rigproc**: `src/rigproc/central/__main__.py`.

Inoltre, è disponibile un file di accesso per eseguire un client della _console_, uno strumento in grado di comunicare con _rigproc_. Tale file è il seguente: `src/rigproc/console/client.py`.

_Per **file di accesso** si intende un file di scripting Python, con estensione `.py`, in grado di cominciare l'esecuzione di un determinato software, in questo caso uno dei moduli del RIG._

Per eseguire un file con Python, generalmente si utilizza `python $FILE`. La sintassi del comando potrebbe variare a seconda della versione di Python e del sistema in uso. Maggiori informazioni sono disposibili sul sito ufficiale: [https://www.python.org/](https://www.python.org/).

Alcuni file potrebbero aver bisogno di argomenti aggiuntivi per essere eseguiti: fare riferimento alla loro documentazione specifica o al codice.
