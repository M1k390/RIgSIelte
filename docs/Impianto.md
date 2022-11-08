# Impianto IVIP-3D

_Ultima revisione: 15 luglio 2022_

L'impianto di rilevamento e cattura fotografica dei pantografi viene definito **IVIP-3D**.\
Esso si distingue da vecchi impianti, cosiddetti _2D_, per la capacità di scattare più fotografie contemporaneamente al fine di costruire un'immagine tridimensionale del pantografo.

## Moduli

---

I moduli dell'impianto, da non confondere con i moduli software del RIG, sono apparecchiature hardware che svolgono diverse funzioni, tutte collegate ad un unico bus seriale.

Le tipologie di modulo sono le seguenti:

- **modulo IO**: è il modulo "centrale" dell'impianto;
- **modulo Trigger**: comanda lo scatto delle fotocamere;
- **modulo MOSF-TX**;
- **modulo MOSF-RX**: raccoglie informazioni sul filo elettrico sopra al treno.

Ci sono due tipologie di impianto: a **binario singolo** o **binario doppio**.

Nel caso del binario singolo, si ha:

- 1 modulo IO;
- 1 modulo Trigger;
- 1 modulo MOSF-TX;
- 1 modulo MOSF-RX.

Nel caso del binario doppio, si ha:

- 1 modulo IO;
- 2 moduli Trigger;
- 2 moduli MOSF-TX;
- 2 moduli MOSF-RX.

I due binari, nella configurazione doppia, vengono identificati dalle lettere _a_ e _b_.

Nella terminologia ferroviaria i due binari sono _pari_ e _dispari_, ma la loro corrispondenza coi binari _a_ e _b_ non è determinata.
