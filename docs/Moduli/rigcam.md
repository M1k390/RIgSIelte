# Modulo rigcam

_Ultima revisione: 15 luglio 2022_

## Panoramica

---

_rigcam_ è un modulo che si occupa di gestire gli scatti prodotti dalle fotocamere connesse all'impianto.

L'attuale implementazione di _rigcam_ è compatibile con alcuni modelli di fotocamere **Manta**, del produttore **AlliedVision**, che utilizzano le **API Vimba**.

_rigcam_ utilizza [asyncio](https://docs.python.org/3/library/asyncio.html) per gestire la concorrenza delle diverse operazioni, fatta eccezione per la gestione diretta delle fotocamere tramite API.\
_asyncio_ utilizza dei _task_, invece dei thread, come entità fondamentali della concorrenza. Di seguito, è riportata una lista dei task e dei thread di _rigcam_, con collegamenti ai file in cui sono contenute le rispettive implementazioni:

- [main_task](../../src/rigcam/main.py): task principale, è il primo ad essere lanciato;
- [pole_task](../../src/rigcam/pole.py): task di gestione delle attività di un palo: ad ogni palo (corrispondente al palo fisico) possono corrispondere fino a 6 fotocamere;
- [camera_task](../../src/rigcam/camera.py): task di gestione della singola fotocamera;
- [camera_thread](../../src/rigcam/vimba_cam.py): thread di gestione della fotocamera tramite le API Vimba;

Il task del palo, il task della fotocamera e il thread della fotocamera hanno ciascuno, al proprio interno, un **ciclo infinito** che ne governa le logiche e che si coordina con il proprio "task superiore" (il thread camera riferisce il proprio stato al task camera, che a sua volta lo riferisce al task palo; il task palo, a sua volta, regola l'esecuzione del task camera, che regola quella del thread camera).

## Funzionamento basilare

---

Gli scatti catturati dalle fotocamere sono organizzati in **eventi passaggio treno**.\
Ciascun evento identifica un **singolo pantografo**. Pertanto, a dispetto del nome, ad un singolo treno possono essere associati più "eventi passaggio treno", se questo possiede più di un pantografo.

Quando le fotocamere segnalano l'avvenuta esecuzione di uno scatto, viene **inizializzato** un _evento passaggio treno_.\
Possono essere inizializzati fino a **3 eventi nell'arco di 5 secondi**.\
Terminato questo periodo, _rigcam_ **scarica gli scatti** effettuati dalle fotocamere, un certo numero di fotocamere per volta, a seconda della configurazione del RIG.\
Durante lo scaricamento, vengono scartati eventuali _eventi passaggio treno_ successivi.
Infine, _rigcam_ **scrive su disco** gli scatti ottenuti ed **invia un report** dell'evento a _rigproc_ tramite **Redis**.

## Entità

---

Le seguenti entità sono implementate in [entities.py](../../src/rigproc/commons/entities.py) e sono alla base di ciascun **evento passaggio treno**.\
Le stesse entità vengono utilizzate da _rigproc_ per la gestione dell'evento e, pertanto, queste vengono serializzate e inviate da _rigcam_ nel report dell'evento.

### CameraEvent

Identifica l'evento di passaggio di un singolo pantografo.\
Un singolo treno può possedere più di un pantografo, quindi può essere associato a più eventi camera.\
Viene caratterizzato dal palo corrispondente e produce un singolo report.

### CameraShootArray

Insieme di scatti corrispondente ad uno shoot event.\
Possiede un timestamp unico per tutti gli scatti.

### CameraShoot

Singolo scatto caratterizzato dall'ID della fotocamera e il percorso del file.\
Il timestamp è quello del shoot array di appartenenza.

## Interfaccia con _rigproc_

---

La comunicazione con _rigproc_ avviene tramite messaggi scambiati su Redis. I messaggi possono essere delle strutture dati serializzate in un json.

Molti messaggi vengono codificati e decodificati tramite [interpreter.py](../../src/rigproc/commons/interpreter.py).

### PROTOCOLLO DI COMUNICAZIONE

#### **Messaggio di setup**

| Direzione             | Chiave Redis   |
| --------------------- | -------------- |
| _rigproc_ -> _rigcam_ | `rigcam_setup` |

```json
{
    "proc_conf": {
        "local_path": ...,
        "simultaneous_dls": ...,
        "trigger_timeout": ...,
        "max_frame_dl_time": ...,
        "event_timeout": ...
    },
    "logging_conf": {
        "format_code": ...,
        "formatter": ...,
        "level": ...,
        "file_dir": ...,
        "file_name": ...,
        "file_mode": ...,
        "log_to_root": ...,
        "root_file_dir": ...,
        "root_file_name": ...
    },
    "camera_conf": {
        "cameras": [
            {
                "id": ...,
                "ip": ...,
                "pole": ...,
                "num": ...,
                "xml": ...
            }
        ]
    }
}
```

#### **Richiesta di uscita**

| Direzione             | Chiave Redis |
| --------------------- | ------------ |
| _rigproc_ -> _rigcam_ | `cam_exit`   |

```json
1
```

#### **Report di avvio**

| Direzione             | Chiave Redis     |
| --------------------- | ---------------- |
| _rigcam_ -> _rigproc_ | `startup_report` |

```json
{
    "running": ...,
    "opened_cameras": ...,
    "errors": ...
}
```

#### **Segnalazione errore camera**

| Direzione             | Prefisso chiave Redis                   |
| --------------------- | --------------------------------------- |
| _rigcam_ -> _rigproc_ | `cam_error_` (segue un uid dell'errore) |

```json
{
    "cam_id": ...,
    "running": ...,
    "error_msg": ...
}
```

#### **Segnalazione crash rigcam**

| Direzione             | Chiave Redis |
| --------------------- | ------------ |
| _rigcam_ -> _rigproc_ | `cam_crash`  |

```json
${STR_ERRORE}
```

#### **Report nuovo evento**

| Direzione             | Prefisso chiave Redis                   |
| --------------------- | --------------------------------------- |
| _rigcam_ -> _rigproc_ | `cam_event_` (segue un uid dell'evento) |

```json
{
    "pole": ...,
    "shoot_arrays": [
        {
            "timestamp": ...,
            "shoots": [
                {
                    "cam_id": ...,
                    "cam_num": ...,
                    "img_path": ...,
                }
            ],
            "trans_id": ...
        }
    ]
}
```

#### **Avviso rinnovo session timestamp**

| Direzione             | Chiave Redis     |
| --------------------- | ---------------- |
| _rigproc_ -> _rigcam_ | `log_session_ts` |

```json
${SESSION_TS}
```
