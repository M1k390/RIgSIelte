# Configurazione

_Ultima revisione: 15 luglio 2022_

Tutti i moduli del RIG (rigboot, rigcam, rigman e rigproc) utilizzano un unico file di configurazione, in formato `json`. Possono essere utilizzati, opzionalmente, dei file di configurazione per le fotocamere, dipendenti dalle API utilizzate.

## Parsing della configurazione

---

Il **codice** responsabile della lettura e del parsing della configurazione è localizzato in `src/rigproc/common/config.py`. L'analisi del codice può fornire ulteriori dettagli sui tipi accettati per alcuni parametri e sulla gestione degli stessi.

L'intera configurazione del RIG viene trattata dal programma come un oggetto Python di tipo `Config`.

Se il software rileva degli **errori** nel file di configurazione, questo lo segnala nei log e. tramite un messaggio Kafka, all'STG. **L'esecuzione del RIG prosegue**, ma potrebbero verificarsi delle anomalie.\
Tra i possibili errori riscontrabili, vi sono:

- la mancanza di uno o più parametri di configurazione attesi;
- un valore associato ad un parametro di tipo sbagliato (es: stringhe di testo, numeri interi, booleani);
- un valore associato ad un parametro al di fuori dall'insieme dei valori ammessi.

Se, in una sessione precedente, alcuni parametri di configurazione sono stati _modificati a runtime_ (per esempio a seguito ad una _richiesta dell'STG_), questi potrebbero essere stati salvati sull'istanza persistente di Redis. In questo caso, **il RIG ignorerà i dati presenti nel file di configurazione** per quei parametri ed utilizzerà i dati disponibili in Redis.\
La console è provvista di una funzione per cancellare i parametri di configurazione nella cache di Redis, forzando il programma ad utilizzare i parametri presenti sul file di configurazione.

## Specificare un file di configurazione

---

Si può specificare un file di configurazione durante l'avvio dei moduli del RIG:

- **rigboot**: con l'opzione `--conf`. Esempio: `python src/rigboot/rigboot.py --conf conf.json`;
- **rigcam**: i parametri di configurazione vengono passati quando _rigcam_ viene avviato da _rigproc_;
- **rigman**: con l'opzione `--conf`. Esempio: `python src/rigman/main.py --conf conf.json`;
- **rigproc**: come argomento del comando di avvio. Esempio: `python src/rigproc/central/__main__.py conf.json`.

## Esempio e commenti

---

In questa repository, sono disponibili alcuni esempi di configurazione del RIG nella cartella `data`, anteceduti dal prefisso `conf_`.

Di seguito, viene riportato un **esempio** di configurazione con alcuni **commenti esplicativi**.

```json
{
    # Configurazione dei parametri principali
	"main": {
        # Configurazione di Redis
		"redis": {
			"cache": {
				"host": "localhost",
				"port": "6379",
				"io_expire_s": 60
			},
			"pers": {
				"host": "localhost",
				"port": "6380"
			}
		},
        # Recovery delle immagini (rigproc)
		"recovering": {
			"enabled": true,
			"remote_folder": "/home/sielte/code/imgs/real_remote/",
			"local_folder": "/home/sielte/code/imgs/local/",
			"massive_start": "02:00:00", # Inizio del periodo Massive
			"massive_finish": "03:00:00", # Fine del periodo Massive
			"timer_massive": 30, # Periodo di Recovery in Massive (in secondi)
			"timer_normal": 60, # Periodo di Recovery in Normal (in secondi)
			"recovery_timeout": 60, # Recovery annullato dopo X secondi
			"threshold": 300 # Numero di eventi salvabili in memoria
		},
        # Attivazione di moduli software di rigproc
		"modules_enabled": {
			"camera": "deploy",
			"485": "deploy",
			"broker": "deploy"
		},
        # Aggiornamento software
		"sw_update": {
			"package_remote_folder": "/home/sielte/code/imgs/real_remote/sw_upload/",
			"package_local_folder": "/home/sielte/code/sw_update/",
			"update_date_format": "%d-%m-%Y",
			"update_time_format": "%H:%M"
		},
        # Console per l'interazione con rigproc
		"console": {
			"server": {
				"ip": "192.168.2.7",
				"port": "9999"
			}
		},
        # Attività periodiche di rigproc
		"periodic": {
			"enabled": true,
			"evt_flows_timeout": 180, # Flow annullati dopo X secondi
			"periodic_check_period": 60 # Periodo della routine periodica
		},
        # Parametri di impianto
		"implant_data": {
			"password": "sielte",
			"configurazione": "binario_doppio",
			"nome_rip": "Pioltello LL",
			"nome_ivip": "Pioltello LL",
			"nome_linea": "Milano Lambrate Venezia (LL)",
			"kmetrica_impianto": "13+586LL",
			"coord_impianto": "45_29_22N 09_20_15_E",
			"prrA_bin": "dispari",
			"prrB_bin": "pari",
			"wire_calib_pari": "F.I. mosf 146mm", # Calibrazione filo
			"wire_calib_dispari": "F.I. mosf 146mm",
			"ip_remoto": "192.168.2.7",
			"loc_tratta_pari_inizio": "MELZO SCALO",
			"loc_tratta_pari_fine": "PIOLTELLO LIM.",
			"loc_tratta_dispari_inizio": "PIOLTELLO LIM.",
			"loc_tratta_dispari_fine": "MELZO SCALO",
			"cod_pic_tratta_pari": "9326",
			"cod_pic_tratta_dispari": "9325",
			"distanza_prr_IT_pari": 3, # Distanza Palo - Inizio Tratta
			"distanza_prr_IT_dispari": 3,
			"t_mosf_prrA": 5,
			"t_mosf_prrB": 5,
			"t_off_ivip_prrA": 60,
			"t_off_ivip_prrB": 60,
			"fov": "??",
			"sensor_width": "1.1inch",
			"focal_distance": "F35mm",
			"camera_brand": "AlliedVision",
			"camera_model": "Manta G-1236C"
		},
        # Collegamento sshfs (cartella remota) (rigproc)
		"sshfs": {
			"ip": "192.168.2.103",
			"user": "sielte",
			"ssh_key": "/home/sielte/.ssh/id_rsa",
			"stg_folder": "/data/shared",
			"rip_folder": "/home/sielte/code/imgs/real_remote"
		},
        # Sincronizzazione dell'ora tramite Network Time Protocol (rigproc)
		"ntp": {
			"enabled": false,
			"ip": "192.168.2.101",
			"timezone": "Europe/Rome",
			"sync_interval": 43200 # In secondi
		},
        # Ping ai server per verificarne lo stato di collegamento (rigproc)
		"ping": {
			"enabled": true,
			"cameras_ping_interval": 20, # In secondi
			"servers_ping_interval": 20 # In secondi
		},
        # Altre opzioni di rigproc
		"settings": {
			"wait_mosf": true, # Attendi che il MOSF abbia raccolto i dati sul filo
			"trim_mosf_data": true # Taglia i dati di altezza filo alla porzione di interesse
		}
	},
    # Impostazioni di rigcam
	"camera": {
        # Codice identificativo e indirizzo IP delle fotocamere
		"ids": {
			"prrA": {
				"camera_prrA_id_1": "DEV_000F314E56D7",
				"camera_prrA_id_2": "DEV_000F314E56D3",
				"camera_prrA_id_3": "DEV_000F314E56D6",
				"camera_prrA_id_4": "DEV_000F314E56D5",
				"camera_prrA_id_5": "DEV_000F314E56D4",
				"camera_prrA_id_6": "DEV_000F314F0A93",
				"camera_prrA_ip_1": "192.168.1.21",
				"camera_prrA_ip_2": "192.168.1.22",
				"camera_prrA_ip_3": "192.168.1.23",
				"camera_prrA_ip_4": "192.168.1.24",
				"camera_prrA_ip_5": "192.168.1.25",
				"camera_prrA_ip_6": "192.168.1.26"
			},
			"prrB": {
				"camera_prrB_id_1": "DEV_000F314F12F6",
				"camera_prrB_id_2": "DEV_000F314F12F4",
				"camera_prrB_id_3": "DEV_000F314F12F7",
				"camera_prrB_id_4": "DEV_000F314F12F5",
				"camera_prrB_id_5": "DEV_000F314F1147",
				"camera_prrB_id_6": "DEV_000F314F12F3",
				"camera_prrB_ip_1": "192.168.1.11",
				"camera_prrB_ip_2": "192.168.1.12",
				"camera_prrB_ip_3": "192.168.1.13",
				"camera_prrB_ip_4": "192.168.1.14",
				"camera_prrB_ip_5": "192.168.1.15",
				"camera_prrB_ip_6": "192.168.1.16"
			}
		},
        # File di configurazione delle fotocamere
		"xml_files": {
			"prrA": {
				"camera_prrA_xml_1": "/home/sielte/code/cam_xml/Dispari_1.xml",
				"camera_prrA_xml_2": "/home/sielte/code/cam_xml/Dispari_2.xml",
				"camera_prrA_xml_3": "/home/sielte/code/cam_xml/Dispari_3.xml",
				"camera_prrA_xml_4": "/home/sielte/code/cam_xml/Dispari_4.xml",
				"camera_prrA_xml_5": "/home/sielte/code/cam_xml/Dispari_5.xml",
				"camera_prrA_xml_6": "/home/sielte/code/cam_xml/Dispari_6.xml"
			},
			"prrB": {
				"camera_prrB_xml_1": "/home/sielte/code/cam_xml/Pari_1.xml",
				"camera_prrB_xml_2": "/home/sielte/code/cam_xml/Pari_2.xml",
				"camera_prrB_xml_3": "/home/sielte/code/cam_xml/Pari_3.xml",
				"camera_prrB_xml_4": "/home/sielte/code/cam_xml/Pari_4.xml",
				"camera_prrB_xml_5": "/home/sielte/code/cam_xml/Pari_5.xml",
				"camera_prrB_xml_6": "/home/sielte/code/cam_xml/Pari_6.xml"
			}
		},
        # Altre specifiche di rigcam
		"process_type": "subprocess", # subprocess / fake
		"default_path": "/home/sielte/code/exec/rigcam_1.1",
		"simultaneous_dls": 1, # Download delle immagini simultanei
		"trigger_timeout": 5, # Periodo di rilevazione trigger
		"max_frame_dl_time": 4, # Timeout download singolo frame
		"event_timeout": 90, # Timeout generale gestione evento
		"restart_attempts": 3, # Tentativi di aggancio delle fotocamere
		"ready_timeout": 60 # Timeout di partenza di rigcam
	},
    # Parametri di collegamento al bus seriale rs-485
	"io": {
		"device": "/dev/ttyS0",
		"speed": 9600,
		"timeout": 1.0,
		"parity": "none",
		"stopbits": 2,
		"cts": 0,
		"timeoutAnswer": 1.0,
		"retries": 2,
		"set_linux_permissions": true # Esegui chmod 777 per la porta seriale
	},
    # Parametri di collegamento a Kafka
	"broker": {
		"consume": {
			"broker": "192.168.2.101:9092",
			"group": "group",
			# Topic messaggi in arrivo
			"topic_req": [
				"DiagnosiSistemiIVIP_STGtoRIP",
				"AggiornamentoSW_STGtoRIP",
				"AggiornamentoImpostazioni_STGtoRIP",
				"AggiornamentoFinestraInizioTratta_STGtoRIP"
			]
		},
		"produce": {
			"broker": "192.168.2.101:9092",
			"group": "group",
			"timeout": 5.0
		}
	},
    # Impostazioni di rigboot
	"boot": {
		"exec_dir": "/home/sielte/code/exec",
		"default_exec_path": "/home/sielte/code/exec/rigproc_1.1",
		"last_version_key": "last_version", # Chiave per rilevare l'ultima versione su Redis
		"rig_start_timestamp_key": "start_timestamp",
		"rig_termination_key": "termination_message",
		"boot_check_timeout": 30,
		"exec_watch_interval": 10,
		"alive_key": ""
	},
    # Impostazioni dei logger di Python
	"logging": {
		"renew_log_files": true, # Rinnova i file di log quotidianamente
		"renewal_time": "00:00", # Orario di rinnovo
		"delete_older_logs": false, # Elimina i file di log più vecchi
		"days_to_keep": 30, # Conserva i log degli ultimi X giorni
		"bus": {
			"format": "%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s",
			"formatter": "color",
			"console_level": 10,
			"file_level": 20,
			"file_dir": "/home/sielte/code/log/bus",
			"file_name": "log_bus",
			"file_mode": "append",
			"memory_threshold": 100000000,
			"log_to_root": false
		},
		"camera": {
			"format": "%(asctime)s [%(threadName)-8.8s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s",
			"formatter": "custom",
			"console_level": 10,
			"file_level": 20,
			"file_dir": "/home/sielte/code/log/camera",
			"file_name": "log_camera",
			"file_mode": "append",
			"memory_threshold": 500000000,
			"log_to_root": true
		},
		"console": {
			"format": "%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s",
			"formatter": "color",
			"console_level": 10,
			"file_level": 20,
			"file_dir": "/home/sielte/code/log/console",
			"file_name": "log_console",
			"file_mode": "append",
			"memory_threshold": 100000000,
			"log_to_root": false
		},
		"flow": {
			"format": "%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s",
			"formatter": "alt",
			"console_level": 10,
			"file_level": 20,
			"file_dir": "/home/sielte/code/log/flow",
			"file_name": "log_flow",
			"file_mode": "append",
			"memory_threshold": 200000000,
			"log_to_root": true
		},
		"kafka": {
			"format": "%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s",
			"formatter": "color",
			"console_level": 10,
			"file_level": 20,
			"file_dir": "/home/sielte/code/log/kafka",
			"file_name": "log_kafka",
			"file_mode": "append",
			"memory_threshold": 100000000,
			"log_to_root": true
		},
		"root": {
			"format": "%(asctime)s [%(threadName)-6.6s] [%(levelname)-5.5s] {%(module)s::%(funcName)s} %(message)s",
			"formatter": "color",
			"console_level": 10,
			"file_level": 20,
			"file_dir": "/home/sielte/code/log/root",
			"file_name": "log_root",
			"file_mode": "append",
			"memory_threshold": 1000000000
		}
	}
}
```
