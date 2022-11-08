# Installazione

_Ultima revisione: 15 luglio 2022_

Come già specificato in altre parti della documentazione, questo software, scritto in Python, non necessita di installazione o compilazione.\
Per _installazione_, in questo documento, si intende la configurazione del sistema sul **RIP** per la messa in produzione del **RIG**.

## Requisiti

---

La preparazione del sistema per l'esecuzione automatica del RIG richiede l'installazione di alcuni componenti, descritti nel documento [Requisiti](docs/Requisiti.md).

Nello specifico, è necessario installare:

- **Redis**;
- **Python** e le sue dipendenze, compresi _Vimba_ e _rigproc_, **solo se si esegue il RIG tramite Python** (vedi [Distribuzione](docs/Distribuzione.md) per maggiori dettagli sull'esecuzione senza Python);
- **Vimba SDK**.

## Systemd

---

[Systemd](https://systemd.io/) è un gestore di processi in background per Linux, disponibile su tutte le ultime versioni di Ubuntu e Ubuntu Server.\
Esso può essere utilizzato per gestire agevolmente l'esecuzione del RIP.

Systemd necessita di un file con estensione `.service` che definisce il _servizio_, ossia il software eseguito sullo sfondo. Questo file definisce, tra le altre cose, le operazioni da svolgere all'avvio e alla terminazione del servizio. Alcuni esempi sono disponibili nella cartella `data/systemd` della repository.

Per comodità, le operazioni di avvio e arresto del servizio sono state definite in degli script a parte, rispettivamente `run.sh` e `stop.sh`, indicati nel file del servizio.

Il metodo migliore per la gestione del RIG tramite Systemd è avviare **rigboot** tramite un servizio dedicato. Esso si occuperà di **avviare rigproc** e gestirne l'esecuzione, il quale, a sua volta, **avvierà rigcam**. Questa catena di esecuzione consente di avere un software completo con l'avvio di un solo modulo (_rigman_ è uno strumento facoltativo rivolto al manutentore).

```
Systemd
|-> rigboot.service
    |-> rigboot
        |-> rigproc
            |-> rigcam
```

Nel file del servizio, è necessario indicare anche la posizione dei driver Vimba forniti insieme all'SDK. Consultare gli esempi per maggiori dettagli.

## Configurazione

---

Negli script di avvio e di arresto è necessario fornire un file di configurazione del RIG.\
Il file deve essere compilato a seconda del contesto e dell'installazione in uso. Per maggiori dettagli, consultare il documento [Configurazione](docs/Configurazione.md).
