# Distribuzione

_Ultima revisione: 15 luglio 2022_

Il RIG può essere eseguito direttamente, senza compilazione o installazione, tramite Python.

Tuttavia, è possibile generare dei file eseguibili che non richiedono la presenza di Pytohn installato sul sistema in uso e nascondono (parzialmente) il codice scritto.

## Generazione di file esegubili

---

È possibile generare i file eseguibili di _rigboot_, _rigcam_, _rigman_ e _rigproc_ utilizzando **Pyinstaller**.

Per ciascun componente è necessario indicare lo script di accesso (vedi la sezione _Esecuzione_). Per esempio:

```bash
pyinstaller src/rigproc/central/__main__py -n rigproc --onefile --specpath build --distpath dist
```

Questo comando:

1. genera una cartella `build` e vi inserisce un file `.spec`;
2. inserisce nella cartella `build` altri file temporanei;
3. genera una cartella `dist` e vi inserisce il file eseguibile.

Si noti l'utilizzo delle seguenti opzioni:

- `-n NOMEFILE` per specificare il nome del file eseguibile;
- `--onefile`: consente di generare un unico file eseguibile; senza questa opzione, verrebbe generata una cartella contenente molteplici file;
- `--specpath`: consente di indicare la cartella in cui salvare il file spec;
- `--distpath`: consente di indicare la cartella in cui salvare il file eseguibile.

La descrizione di altre opzioni è disponibile nella [documentazione ufficiale](https://pyinstaller.org/en/stable/usage.html#options).

Nella cartella principale della repository è presente lo script `build.py` per facilitare la generazione di file eseguibili per la distribuzione. Lo script può essere utilizzato con diversi argomenti, consultabili tramite il comando:

```bash
python build.py --help
```

Di default, le cartelle `build` e `dist` all'interno della repository verranno ignorate da Git, e possono essere modificate senza problemi.

I file eseguibili generati supportano gli **stessi argomenti e opzioni** degli script Python.

## Aggiornamento remoto

Lo script `build.py` genera anche un **file zip** contente gli eseguibili di `rigproc` e `rigcam` e tutto il materiale necessario a effettuare un aggiornamento remoto.

L'STG è in grado di chiedere al RIG di effettuare un aggiornamento software, sostituendo i propri file eseguibili con quelli contenuti nel file zip.\
La richiesta di aggiornamento viene effettuata tramite Kafka, mentre il file zip viene condiviso sfruttando la cartella remota SSHFS.

Se non è necessario generare il file zip, è possibile usare l'opzione `--nozip`:

```bash
python build.py --nozip
```

## Patch di confluent-kafka

Se ci si trova in ambiente Windows, lo script `build.py` applica una modifica al codice sorgente del modulo Python di terze parti _confluent-kafka_ quando si genera il file eseguibile di _rigman_. La modifica riguarda il file `__init__.py` e la versione modificata del file si trova in patch/confluent_kafka. Tale file viene ripristinato alla sua versione originale al termine della generazione del file eseguibile di _rigman_.

Questa modifica è necessaria per poter eseguire _rigman_ in un file `.exe`.

La patch è stata testata con _confluent-kafka_ in versione 1.7.0.

### Dettagli tecnici sulla patch

La modifica riguarda il primo metodo del file `__init__.py`, ossia `_delvewheel_init_patch_60438943116`.

Questo metodo cerca e carica nel sistema le librerie Kafka integrate in _confluent-kafka_. Tali librerie vengono cercate in base ad una posizione relativa allo script `__init__.py`, la cui posizione è accessibile in Python tramite la variabile `__file__`.

Il problema nasce dal fatto che Pyinstaller integra all’interno del file eseguibile tutti gli script e i moduli di terze parti utilizzati dal programma. In questo modo, il valore della variabile `__file__` viene alterato, e la ricerca delle librerie di Kafka fallisce.

Per risolvere il problema, lo script `build.py` copia tali librerie all’interno del file eseguibile. Lo script `__init__.py` modificato cerca le librerie nella posizione corretta all’interno del file eseguibile, grazie ad un percorso fittizio fornito dalla variabile Python `sys._MEIPASS`, inizializzata secondo le istruzioni di Pyinstaller.
