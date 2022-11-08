# Requisiti

_Ultima revisione: 15 luglio 2022_

## Requisiti di sistema

---

Questo software è stato testato con il sistema operativo **Ubuntu Server 18.04**, con kernel **Linux HWE 5.4**, ed in parte con **Ubuntu Server 22.04**, con kernel **5.15.0-40-generic**, installato su un computer basato su architettura **Intel x86 a 64 bit**, con **8 GB** di memoria RAM e da **64 GB** a **256 GB** di memoria di archiviazione.

## Redis

---

Per installare Redis fare riferimento a [questa guida](https://redis.io/topics/quickstart).

Su Ubuntu 22.04, è consigliabile usare `apt` per l'installazione di Redis:

```bash
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

sudo apt-get update
sudo apt-get install redis
```

Devono essere avviate due istanze di Redis, tipicamente sulle porte 6379 e 6380. È consigliabile utilizzare un gestore di servizi come systemd per lanciare Redis all'avvio del sistema. Poiché le istanze sono due, saranno necessari due servizi e due file di configurazione distinti. Per esempio:

```bash
# Redis 6379
/lib/systemd/system/redis-server6379.service
/etc/redis/redis6379.conf

# Redis 6380
/lib/systemd/system/redis-server6380.service
/etc/redis/redis6380.conf
```

Dovranno anche essere indicati due file _pid_ distinti, che verranno sutomaticamente generati e gestiti dalle due istanze di Redis, per esempio:

```bash
# Redis 6379
/run/redis/redis-server6379.pid

# Redis 6380
/run/redis/redis-server6380.pid
```

Infine, dovranno anche essere separati i file di backup delle due istanze di Redis, nei rispettivi file di configurazione:

```bash
# redis6379.conf
dbfilename dump6379.rdb
appendfilename "appendonly6379.aof"

# redis6380.conf
dbfilename dump6380.rdb
appendfilename "appendonly6380.aof"
```

**N.B.: è importante tenere separati i file di backup anche quando la persistenza dei dati è disattivata, poiché Redis legge e recupera le informazioni di tali file ad ogni avvio.**

La differenza principale tra le due istanze è che quella sulla porta 6379 è "volatile" e perde le informazioni contenute al riavvio del sistema. L'altra, invece, sulla porta 6380, è persistente e mantiene le informazioni contenute anche dopo un riavvio del sistema.\
I due file di configurazione di esempio nella cartella `data` rispettano queste specifiche.

Un altro parametro della configurazione a cui prestare attenzione è il seguente:

```bash
notify-keyspace-events KEA
```

Questo parametro consente ad un processo di **rilevare eventi di modifica**, in tempo reale, effettuati su Redis da un altro processo.

Redis è **necessario per poter eseguire il Rig** ed è utilizzato a fini esclusivamente interni del programma, come la comunicazione tra i processi e il salvataggio di parametri di impianto aggiornati.

## Kafka

---

Kafka è uno strumento utilizzato esclusivamente per comunicare con il STG, pertanto se si intende eseguire il Rig a fini esclusivamente di test, non è necessario installare Kafka.

Per l'installazione seguire [questa guida](https://kafka.apache.org/quickstart).

Nel sistema reale, Kafka è installato su un host remoto. Può anche essere installato in localhost per fini di test.

L'assenza di Kafka non determina il mancato funzionamento del Rig. Tuttavia, alcune procedure, quale la gestione di un nuovo scatto delle fotocamere, potrebbero fallire.

## Vimba

---

Vimba fornisce un SDK che deve essere installato per poter utilizzare _rigcam_ e gestire delle telecamere collegate alla rete.
Alternativamente, è possibile configurare il Rig perché simuli il processo camera senza effettivamente utilizzare le API di Vimba. In questo caso non sarà possibile utilizzare le camere reali e la gestione di eventuali scatti simulati via software potrebbe fallire.

È possibile scaricare il SDK di Vimba dal [sito del profuttore](https://www.alliedvision.com/en/products/vimba-sdk).

In allegato è possibile trovare parte della documentazione di Vimba 4.2, la versione con cui è stato testato _rigcam_. Questi documenti contengono informazioni su come installare VimbaGigETL (per utilizzare le telecamere via Ethernet), VimbaPython, e per utilizzare il tool VimbaViewer.

## Cartella remota

---

Per montare la cartella remota, viene utilizzato sshfs. È necessario indicare la posizione della chiave SSH utilizzata.

Il Rig eseguirà automaticamente all'avvio i comandi necessari per montare la cartella remota su una directory locale in base ai parametri di configurazione. I comandi sono:

```bash
# Per smontare la cartella nel caso sia attualmente in uso
sudo umount $CARTELLA_LOCALE

# Per montare la cartella
sudo sshfs -o allow_other,default_permissions,nonempty,IdentityFile=$CHIAVE_SSH  $UTENTE@$INDIRIZZO_IP:$CARTELLA_REMOTA $CARTELLA_LOCALE
```

I parametri preceduti da "$" vengono sostituiti dal Rig coi dati contenuti nel file di configurazione.

## Bus seriale

---

L'impianto deve essere collegato alla scheda su cui viene eseguito il Rig tramite una porta seriale.

Se si esegue il rip su una scheda Aaeon EMB-APL1, fare riferimento al manuale allegato alla documentazione. In questo caso, i due cavi del bus possono essere collegati ai pin DCD e RXD della porta COM1. Accertarsi nelle impostazioni del BIOS che la porta COM1 utilizzi lo standard _485_ per la comunicazione seriale.

Si supponga che Ubuntu mappi la porta seriale utilizzata a `/dev/ttyS0`. Tale porta dovrà essere specificata nel file di configurazione del RIG, che le assegnerà i massimi privilegi per evitare problemi di accesso, con il seguente comando:

```bash
sudo chmod 777 /dev/ttyS0
```

## Python

---

Questo programma necessita di **Python == 3.7.4**. Non è stato testato con versioni superiori di Python. Si consiglia di utilizzare _Conda_ per l'installazione di un ambiente Python con una versione specifica. Conda consente di creare degli ambienti di lavoro con dipendenze e versioni di Python isolate.

Per l'installazione, consultare il [sito ufficiale](https://docs.conda.io/en/latest/). Per una tabella dei comandi più comuni, consultare [questo documento](https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf).

Conda genera un ambiente predefinito chiamato `base`.

Per attivare un ambiente di Conda, utilizzare il comando:

```bash
conda activate $NOME
```

Per cambiare la versione di Python utilizzata da un ambiente, dopo averlo attivato, usare il seguente comando:

```bash
conda install python=$VERSIONE
```

Oppure, per creare un nuovo ambiente con una versione specifica di Python, usare il comando:

```bash
conda create -n $NOME python=$VERSIONE
```

Esempio: `conda create -n rigenv python=3.7.4`

### DIPENDENZE

Sono necessari i seguenti moduli Python:

- confluent-kafka (>=1.3.0)
- psutil (>=5.7.0)
- pyserial (>=3.4)
- redis (>=3.4.1)
- VimbaPython (>=1.0.1)
- pytest (>= 5.4.2)
- setuptools (>=52.0.0)
- pyinstaller (>=3.6)

Installazione tramite **pip**:

```bash
pip install confluent-kafka psutil pyserial redis pytest pyinstaller setuptools
```

Installazione tramite **Conda**:

```bash
conda install -c conda-forge python-confluent-kafka=1.3.0 redis-py=3.4.1 psutil=5.7.0 pyserial=3.4 ntplib pytest=5.4.2 pyinstaller=3.6
conda install -c anaconda setuptools=52.0.0
```

Per l'installazione di VimbaPython fare riferimento al paragrafo _Vimba_.

### MODULO RIG

In ultimo, è necessario **installare rigproc**. È possibile installare questo software come modulo Python tramite `setup.py` in due modi diversi.

Per copiare il codice nella cartella dei moduli di Python:

```bash
python setup.py install
```

In questo caso il comando dovrà essere eseguito ogni volta che viene modificato il codice.\
Pertanto, si consiglia di utilizzare la seguente opzione, che collega la cartella della repository a Python, sincronizzando le modifiche:

```bash
python setup.py develop
```

**N.B.: se si utilizza _conda_, è necessario attivare l'ambiente che si intende utilizzare prima di installare qualsiasi modulo.**

## Configurazione

---

Il file di configurazione è un file json contenente tutti i parametri necessari per l'esecuzione del Rig.\
Per eseguire il software, è necessario fornire un file di configurazione valido.
Maggiori informazioni sono disponibili nel documento [Configurazione](./Configurazione.md).
