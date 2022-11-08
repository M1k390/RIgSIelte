# Modulo rigproc

_Ultima revisione: 15 luglio 2022_

_rigproc_ è il modulo centrale del RIG.\
Esso si occupa di svolgere le principali funzioni logiche del RIG.\
Tra queste, vi sono:

- gestione degli eventi passaggio treno;
- comunicazione, tramite bus seriale rs-485, con i moduli dell'impianto e diagnosi dello stesso (vedi [Impianto](../Impianto.md));
- comunicazione, tramite la piattaforma Apache Kafka, con l'STG;
- salvataggio degli scatti su un server remoto;
- operazioni di manutenzione e gestione del RIP.

### ESEMPIO

Al passaggio di un pantografo, _rigcam_ genera l'_evento passaggio treno_, salva in memoria gli scatti effettuati dalla fotocamera e notifica _rigproc_ dell'avvenuto evento.\
_rigproc_, a questo punto:

- interroga i moduli dell'impianto per raccogliere ulteriori informazioni sull'evento;
- copia gli scatti dalla memoria interna ad un server remoto;
- invia dei report tramite Kafka all'STG.

## Panoramica

---

_rigproc_ sfrutta il parallelismo offerto dai [thread di Python](https://docs.python.org/3/library/threading.html) per eseguire diverse operazioni in parallelo.

In generale, è possibile paragonare il funzionamento di _rigproc_ a quello di un web server: esso rimane in ascolto di eventuali input, pronto a eseguire le operazioni corrispondenti, e contemporaneamente esegue alcune operazioni periodiche programmate.

### ORGANIZZAZIONE DELLA DIRECTORY

Nella cartella di _rigproc_ sono presenti diverse sottocartelle:

- `central`: include tutti gli attori principali di _rigproc_, incluso il **mainprocess**, il thread che per primo viene inizializzato durante l'esecuzione;
- `commons`: contiene diversi strumenti utilizzati da diverse parti del programma, anche da altri moduli rispetto a _rigproc_;
- `console`: implementa server e client della Console, che funziona tramite socket;
- `fake_modules`: include oggetti che possono essere utilizzati, a fini di test, in mancanza di un attore reale, ad esempio _fake_bus_ può essere utilizzato quando non si ha a disposizione l'impianto o la connessione seriale;
- `flow`: contiene la definizione dei diversi _flow_, di cui si discuterà in seguito;
- `io`: contiene tutti gli strumenti necessari all'invio e alla ricezione di messaggi sul bus seriale;
- `param`: contiene le _keyword_ usate da _rigproc_, e non solo, divise per categoria;
- `routines`: contiene la definizione di alcune attività, svolte periodicamente.

## Interfacce

---

### REDIS

[Redis](https://redis.io/) è uno strumento per la memorizzazione di dati nella forma _chiave: valore_.\
Come specificato nel documento [Requisiti](../Requisiti.md), il RIG utilizza due istanze di Redis, tipicamente sulle porte 6379 e 6380.\
La **prima istanza**, detta **cache**, contiene **dati volatili**, che vengono eliminati ad ogni riavvio (o, in generale, ogni volta che l'istanza viene interrotta).\
La **seconda istanza**, detta **persistent**, contiene dati che vengono copiati nella memoria di archiviazione, rimanendo **disponibili anche dopo un riavvio**.

Redis viene utilizzato per **centralizzare** in memoria le informazioni, **mantenere i dati** salvati in memoria e **comunicare** con _rigcam_, sfruttando il sistema di notifica degli eventi di scrittura.\
Ad esempio, per inviare un report di evento treno a _rigproc_, _rigcam_ inserisce il dato su Redis e _rigproc_, in ascolto sulla stessa chiave in uso da _rigcam_, rileva immediatamente la scrittura del report.

L'implementazione della comunicazione con Redis è contenuta nel file [commons/redisi.py](../../src/rigproc/commons/redisi.py) ed utilizza la libreria Python [redis-py](https://github.com/redis/redis-py).

### BUS RS-485

_rigproc_ comunica con i moduli dell'impianto attraverso una porta seriale RS-485.

L'implementazione della comunicazione tramite porta seriale è contenuta nella cartella `io` ed utilizza la libreria Python [pyserial](https://github.com/pyserial/pyserial).

### BROKER KAFKA

[Apache Kafka](https://kafka.apache.org/) è una piattaforma di scambio di messaggi tra sistemi.\
Viene utilizzato da _rigproc_ per comunicare con l'STG.

L'implementazione della comunicazione tramite Kafka è contenuta nel file [central/kafka_broker.py](../../src/rigproc/central/kafka_broker.py) ed utilizza la libreria Python [confluent-kafka](https://github.com/confluentinc/confluent-kafka-python).

### CONSOLE

La console consente all'utente di interagire con _rigproc_ durante l'esecuzione.

Essa utilizza un socket e un protocollo di comunicazione molto primitivo, poiché il funzionamento della console non è un aspetto critico dell'applicazione.

L'implementazione è contenuta nella cartella `console` e si divide nelle parti **server** e **client**.

## Strategie di implementazione

---

### FLOW

I Flow sono oggetti Python contenenti una **sequenza di funzioni** eseguite in successione.\
La loro caratteristica principale è che **la sequenza può essere interrotta**, all'occorrenza, per attendere l'esito di un'operazione asincrona, tipicamente la risposta da parte di un modulo dell'impianto dal bus seriale, oppure l'esito dell'invio di un messaggio Kafka.

Esistono due implementazioni del Flow.

Quella originale è contenuta nel file [flow/eventtrigflow.py](../../src/rigproc/flow/eventtrigflow.py) e descrive l'oggetto EventTrigFlow. I file nella cartella `flow`, il cui nome inizia con l'underscore, contengono funzioni per questa prima implementazione.

La nuova implementazione è contenuta nel file [flow/flow.py](../../src/rigproc/flow/flow.py) e descrive l'oggetto Flow.\
Le differenze principali con la vecchia implementazione sono:

- il nuovo oggetto Flow può essere **ereditato** per definire un tipo particolare di flow (esempio: il _flow evento passaggio treno_ è definito come oggetto `FlowCameraEvent` nel file [flow/flow_camera_event.py](../../src/rigproc/flow/flow_camera_event.py));
- è possibile effetturare dei **cicli** nella sequenza di operazioni, attraverso le funzioni `start_looping`, `stop_looping` e `jump`;
- il dict interno ai vecchi flow `m_data` è stato sostituito da **attributi** specifici di ogni estensione del flow, per facilitare la manutenzione del codice.

La nuova implementazione presenta delle funzioni utili alla retrocompatibilità con quella vecchia, ed è da considerarsi l'implementazione da scegliere per i nuovi flow.

I file nella cartella `flow`, il cui nome iizia con `flow_`, contengono Flow specifici che estendono la nuova implementazione.

L'esecuzione di un flow deve essere **richiesta al mainprocess**, ossia il thread principale di _rigproc_, inserendo un messaggio di richiesta nella coda delle operazioni. Il _mainprocess_ avvierà il flow quando più opportuno.

### ROUTINE

Le routine sono operazioni eseguite periodicamente da _rigproc_.

Quando è il momento di eseguire una routine, nel caso in cui questa sia un'operazione semplice, essa viene eseguita immediatamente in un **thread dedicato**. Altrimenti, viene richiesto di eseguire un **Flow** al _mainprocess_.

L'implementazione centrale del meccanismo delle routine è contenuta nel file [central/routines_manager.py](../../src/rigproc/central/routines_manager.py), mentre le routine semplici sono implmentate nella cartella `routines`.

Una routine può essere eseguita a **intervalli regolari**, oppure **quotidianamente**, ad un orario programmabile.

### KEYWORD

In _rigproc_, vengono spesso utilizzate **stringhe** che identificano parametri, dati, stati e molto altro, chiamate _keyword_.

Originariamente, le keyword erano tutte contenute nel file [commons/keywords.py](../../src/rigproc/commons/keywords.py).

In seguito, data la grande quantità di keyword, si è scelto di organizzarle in **categorie** nella cartella `params`.\
La transizione alla nuova soluzione non è completa, pertanto è stato mantenuto il file `keywords.py`, che tuttavia non dovrebbe essere ulterioremente utilizzato in futuro, in favore della nuova soluzione.

Un _esempio_ di keyword sono le **chiavi** utilizzate per memorizzare i dati in **Redis**.

## Funzioni principali

---

### RECOVERY

#### **Salvataggio**

Il _Recovery_ è un meccanismo che consente di **salvare temporaneamente** gli scatti nella memoria di archiviazione del RIP in caso di **errore nell'invio degli scatti o delle informazioni** all'STG.

Se viene rilevato un errore durante il processing di un _evento passaggio treno_, tutti gli scatti relativi all'evento e le informazioni ad esso associate vengono memorizzate per il Recovery.

Se alcune immagini erano già state copiate nella cartella remota tramite SSHFS, le copie remote vengono eliminate.

Nel **file di configurazione** è possibile stabilire il **numero di eventi** da memorizzare per il Recovery.\
Superato tale numero, gli eventi non correttamente inviati **vengono persi**.

#### **Reinvio**

Periodicamente, il RIG tenta di recuperare gli eventi memorizzati per il Recovery, reinviandoli.\
Il recupero degli eventi avviene uno per volta.

Vengono distinti due **periodi** relativi al Recovery: **Massive** e **Normal**.\
Nel file di configurazione è possibile definire gli orari di passaggio, nel corso della giornata, da un periodo all'altro.

Durante il periodo **Normal**, ogni volta che viene eseguita la routine di Recovery, si cerca di inviare l'evento memorizzato più vecchio.

Durante il periodo **Massive**, invece, si cerca di recuperate tutti gli eventi, in sequenza, durante un singolo Recovery.

La frequenza con cui viene effettuato il Recovery durante i due periodi può essere definita nel file di configurazione.

### ANOMALIE

Le anomalie avvengono quando il RIG rileva un'errore, di varia natura, durante l'esecuzione.\
L'errore può essere legato, ad esempio, ad una mancata connessione con un modulo dell'impianto o con una risorsa remota, ad un parametro errato di configurazione o ad un errore di sistema.

Al verificarsi di un'ananomalia, questa viene **segnalata all'STG** tramite Kafka.

Le anomalie sono definite nel file [params/anomalies.py](../../src/rigproc/params/anomalies.py).

### RIGCAM

_rigproc_ si occupa anche dell'avvio di _rigcam_.\
Esso è in grado di **avviare** _rigcam_ sia tramite l'interprete Python, che eseguendo il file generato tramite Pyinstaller.

I parametri per l'avvio di _rigcam_ sono definiti nel file di configurazione.

_riproc_ **monitora**, inoltre, l'esecuzione di _rigcam_ e **riavvia** il processo in caso di necessità.\
Il riavvio avviene nei seguenti casi:

- se _rigcam_ non invia il messaggio di _startup_ dopo un periodo stabilito di tempo;
- se _rigcam_ segnala un errore generico o un crash di una camera;
- se _rigcam_ si chiude in maniera inaspettata.

_rigproc_ è in grado di chiedere a _rigcam_ di terminare l'esecuzione attraverso un messaggio scambiato tramite Redis.\
Se la terminazione non avviene entro un certo limite di tempo, _rigproc_ forza la chiusura del processo tramite un comando di sistema.

L'apertura e il riavvio di _rigcam_ sono codificati nel file [central/mainprocess](../../src/rigproc/central/mainprocess.py), rispettivamente nelle funzioni `proc_rigcam` e `proc_rigcam_manager`.
