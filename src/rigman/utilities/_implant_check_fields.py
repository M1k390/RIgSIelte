from rigproc.params import bus, redis_keys, general

TODO= 'TODO'

" Funzioni per la formattazione dei valori/chiavi ottenuti dal server in dati più leggibili "

def _direction_pant(val, args=[]):
	l_mask= {
		bus.mtx_event.attesa_trigger: 'Treno senza pantografo',
		bus.mtx_event.ok_trigger: 'Treno con pantografo'
	}
	if len(args) > 2:
		direction= args[0]
		pant= args[1]
		legal= args[2]
	else:
		direction, pant, legal= general.binario.pari, True, True
	if (val[0] == bus.mtx_event.attesa_trigger and not pant) or\
		(val[0] == bus.mtx_event.ok_trigger and pant):
		if (direction == val[1] and legal) or (direction != val[1] and not legal):
			return f'<-- ({l_mask[val[0]]}, {val[1]})'
	return ''


def _flash_status(val, args=[]):
	guasti= []
	non_disp= []
	corrotti= []
	for i, flash_status in enumerate(val):
		if flash_status == general.status_ok:
			continue
		elif flash_status == general.status_ko:
			guasti.append(i+1)
		elif flash_status == general.dato_non_disp:
			non_disp.append(i+1)
		else:
			corrotti.append(i+1)
	
	status_str= ''
	if len(guasti) > 0:
		status_str += 'Flash mal funzionanti: {}. '.format(', '.join([str(g) for g in guasti]))
	if len(non_disp) > 0:
		status_str += 'Flash non disp: {}. '.format(', '.join([str(nd) for nd in non_disp]))
	if len(corrotti) > 0:
		status_str += 'Dati corrotti: {}. '.format(', '.join([str(c) for c in corrotti]))
	return status_str


def _online_resource(val, args=[]):
	if val == general.status_ok:
		return 'online'
	elif val == general.status_ko:
		return 'offline'
	else:
		return val


"""
CAMPI
Sono ammessi i seguenti campi:
	pos: indica il numero di indice del campo
	des: descrizione del campo (nome mostrato a schermo)
	title: booleano che indica se si tratta di un titolo 
		(i titoli non richiedono il riempimento di un dato)
	cmd: indica il comando del bus richiesto (NON UTILIZZATO)
	hash: hash del dato nella cache di Redis
	key: chiave del dato nella cache di Redis
		hash e key possono essere liste nel caso in cui siano richiesti più dati
		per riempire il campo. Le due liste devono avere uguale lunghezza e vengono
		lette contemporaneamente:
			[HASH1, HASH2, ...]
			[KEY1,  KEY2,  ...]
	fun: indica una funzione facoltativa per la formattazione del dato
	args: eventuali argomenti di fun (list)
"""

FIELDS= [
	{
		'pos': '1',
		'des': 'Modulo I/O',
		'title': True
	},
	{
		'pos': '1.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.io_ver,
		'module': bus.module.io,
		'status_key': bus.data_key.io_vers
	},
	{
		'pos': '1.2',
		'des': 'Stato I_O_Allarmi',
		'cmd': bus.cmd.io,
		'module': bus.module.io,
		'status_key': bus.module.io
	},
	{
		'pos': '1.3',
		'des': 'Temperatura NTC (°C)',
		'cmd': bus.cmd.io,
		'module': bus.module.io,
		'status_key': bus.data_key.io_ntc_c
	},
	{
		'pos': '2',
		'des': 'Modulo MOSF TX Binario Pari',
		'title': True
	},
	{
		'pos': '2.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.mtx_ver_a,
		'module': bus.module.mosf_tx_a,
		'status_key': bus.data_key.mtx_vers
	},
	{
		'pos': '2.2',
		'des': 'Stato Errore Sensori/Efficenza Binario Pari',
		'cmd': bus.cmd.mtx_vel_a,
		'module': bus.module.mosf_tx_a,
		'status_key': bus.data_key.mtx_event
	},
	{
		'pos': '2.3',
		'des': 'Velocita Treno Km/h Binario Pari',
		'cmd': bus.cmd.mtx_vel_a,
		'module': bus.module.mosf_tx_a,
		'status_key': bus.data_key.mtx_velo
	},
	{
		'pos': '2.4',
		'des': 'Transito illegale Treno senza Pantografo Binario Pari',
		'cmd': bus.cmd.mtx_vel_a,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.pari, False, False]
	},
	{
		'pos': '2.5',
		'des': 'Transito illegale Treno con Pantografo Binario Pari',
		'cmd': bus.cmd.mtx_vel_a,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.pari, True, False]
	},
	{
		'pos': '2.6',
		'des': 'Transito legale Treno senza Pantografo Binario Pari',
		'cmd': bus.cmd.mtx_vel_a,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.pari, False, True]
	},
	{
		'pos': '2.7',
		'des': 'Transito legale Treno con Pantografo Binario Pari',
		'cmd': bus.cmd.mtx_vel_a,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.pari, True, True]
	},
	{
		'pos': '2.8',
		'des': 'Comando On/Off Modulo MOSF TX Binario Pari',
		'cmd': bus.cmd.mtx_on_off_a,
		'module': bus.module.mosf_tx_a,
		'status_key': bus.data_key.mtx_onoff
	},
	{
		'pos': '3',
		'des': 'Modulo MOSF TX Binario Dispari',
		'title': True
	},
	{
		'pos': '3.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.mtx_ver_b,
		'module': bus.module.mosf_tx_b,
		'status_key': bus.data_key.mtx_vers
	},
	{
		'pos': '3.2',
		'des': 'Stato Errore Sensori/Efficenza Binario Dispari',
		'cmd': bus.cmd.mtx_vel_b,
		'module': bus.module.mosf_tx_b,
		'status_key': bus.data_key.mtx_event
	},
	{
		'pos': '3.3',
		'des': 'Velocita Treno Kmh Binario Dispari',
		'cmd': bus.cmd.mtx_vel_b,
		'module': bus.module.mosf_tx_b,
		'status_key': bus.data_key.mtx_velo
	},
	{
		'pos': '3.4',
		'des': 'Transito illegale Treno senza Pantografo Binario Dispari',
		'cmd': bus.cmd.mtx_vel_b,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.dispari, False, False]
	},
	{
		'pos': '3.5',
		'des': 'Transito illegale Treno con Pantografo Binario Dispari',
		'cmd': bus.cmd.mtx_vel_b,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.dispari, True, False]
	},
	{
		'pos': '3.6',
		'des': 'Transito legale Treno senza Pantografo Binario Dispari',
		'cmd': bus.cmd.mtx_vel_b,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.dispari, False, True]
	},
	{
		'pos': '3.7',
		'des': 'Transito legale Treno con Pantografo Binario Dispari',
		'cmd': bus.cmd.mtx_vel_b,
		'module': [bus.module.mosf_tx_a, bus.module.mosf_tx_a],
		'status_key': [bus.data_key.mtx_event, bus.data_key.mtx_direction],
		'fun': _direction_pant,
		'args': [general.binario.dispari, True, True]
	},
	{
		'pos': '3.8',
		'des': 'Comando On/Off Modulo MOSF TX Binario Dispari',
		'cmd': bus.cmd.mtx_on_off_b,
		'module': bus.module.mosf_tx_b,
		'status_key': bus.data_key.mtx_onoff
	},
	{
		'pos': '4',
		'des': 'Modulo MOSF RX Binario Pari',
		'title': True
	},
	{
		'pos': '4.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.mrx_ver_a,
		'module': bus.module.mosf_rx_a,
		'status_key': bus.data_key.mrx_vers
	},
	{
		'pos': '4.2',
		'des': 'Stato Errore Sensori/Efficenza Binario Pari',
		'cmd': bus.cmd.mrx_wire_t0_a,
		'module': bus.module.mosf_rx_a,
		'status_key': bus.module.mosf_rx_a
	},
	{
		'pos': '4.3',
		'des': 'Valore Posizione linea di contatto Binario Pari',
		'cmd': bus.cmd.mrx_wire_t0_a,
		'module': bus.module.mosf_rx_a,
		'status_key': bus.data_key.mosf_wire_t0
	},
	{
		'pos': '4.4',
		'des': 'Grafico Posizione linea di contatto Binario Pari',
		'cmd': bus.cmd.mrx_wire_data_a,
		'module': bus.module.mosf_rx_a,
		'status_key': bus.data_key.mosf_wire_data_ok
	},
	{
		'pos': '5',
		'des': 'Modulo MOSF RX Binario Dispari',
		'title': True
	},
	{
		'pos': '5.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.mrx_ver_b,
		'module': bus.module.mosf_rx_b,
		'status_key': bus.data_key.mrx_vers
	},
	{
		'pos': '5.2',
		'des': 'Stato Errore Sensori/Efficenza Binario Dispari',
		'cmd': bus.cmd.mrx_wire_t0_b,
		'module': bus.module.mosf_rx_b,
		'status_key': bus.module.mosf_rx_b
	},
	{
		'pos': '5.3',
		'des': 'Valore Posizione linea di contatto Binario Dispari',
		'cmd': bus.cmd.mrx_wire_t0_b,
		'module': bus.module.mosf_rx_b,
		'status_key': bus.data_key.mosf_wire_t0
	},
	{
		'pos': '5.4',
		'des': 'Grafico Posizione linea di contatto Binario Dispari',
		'cmd': bus.cmd.mrx_wire_data_b,
		'module': bus.module.mosf_rx_b,
		'status_key': bus.data_key.mosf_wire_data_ok
	},
	{
		'pos': '6',
		'des': 'Modulo Trigger Binario Pari',
		'title': True
	},
	{
		'pos': '6.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.trig_ver_a,
		'module': bus.module.trigger_a,
		'status_key': bus.data_key.trig_vers
	},
	{
		'pos': '6.2',
		'des': 'Stato Errore/Efficienza',
		'cmd': bus.cmd.trig_status_a,
		'module': bus.module.trigger_a,
		'status_key': bus.module.trigger_a
	},
	{
		'pos': '6.3',
		'des': 'Trigger_Setting',
		'cmd': bus.cmd.trig_setting_a,
		'module': bus.module.trigger_a,
		'status_key': TODO
	},
	{
		'pos': '6.4',
		'des': 'Flash On/Off',
		'cmd': bus.cmd.trig_ver_a,
		'module': bus.module.trigger_a,
		'status_key': bus.data_key.trig_flash_onoff
	},
	{
		'pos': '6.5',
		'des': 'Camere On/Off',
		'cmd': bus.cmd.trig_ver_a,
		'module': bus.module.trigger_a,
		'status_key': bus.data_key.trig_cam_onoff
	},
	{
		'pos': '6.6',
		'des': 'Trigger_Scatto',
		'cmd': bus.cmd.trig_click_a,
		'module': bus.module.trigger_a,
		'status_key': TODO
	},
	{
		'pos': '6.7',
		'des': 'Trigger_Allarmi',
		'cmd': bus.cmd.trig_status_a,
		'module': [bus.module.trigger_a, bus.module.trigger_a, bus.module.trigger_a, bus.module.trigger_a, bus.module.trigger_a, bus.module.trigger_a],
		'status_key': [bus.data_key.trig_flash_1_status, bus.data_key.trig_flash_2_status, bus.data_key.trig_flash_3_status, bus.data_key.trig_flash_4_status, bus.data_key.trig_flash_5_status, bus.data_key.trig_flash_6_status],
		'fun': _flash_status
	},
	{
		'pos': '7',
		'des': 'Modulo Trigger Binario Dispari',
		'title': True
	},
	{
		'pos': '7.1',
		'des': 'versione del firmware',
		'cmd': bus.cmd.trig_ver_b,
		'module': bus.module.trigger_b,
		'status_key': bus.data_key.trig_vers
	},
	{
		'pos': '7.2',
		'des': 'Stato Errore/Efficienza',
		'cmd': bus.cmd.trig_status_b,
		'module': bus.module.trigger_b,
		'status_key': bus.module.trigger_b
	},
	{
		'pos': '7.3',
		'des': 'Trigger_Setting',
		'cmd': bus.cmd.trig_status_b,
		'module': bus.module.trigger_b,
		'status_key': TODO
	},
	{
		'pos': '7.4',
		'des': 'Flash On/Off',
		'cmd': bus.cmd.trig_ver_b,
		'module': bus.module.trigger_b,
		'status_key': bus.data_key.trig_flash_onoff
	},
	{
		'pos': '7.5',
		'des': 'Camere On/Off',
		'cmd': bus.cmd.trig_ver_b,
		'module': bus.module.trigger_b,
		'status_key': bus.data_key.trig_cam_onoff
	},
	{
		'pos': '7.6',
		'des': 'Trigger_Scatto',
		'cmd': bus.cmd.trig_click_b,
		'module': bus.module.trigger_b,
		'status_key': TODO
	},
	{
		'pos': '7.7',
		'des': 'Trigger_Allarmi',
		'cmd': bus.cmd.trig_status_b,
		'module': [bus.module.trigger_b, bus.module.trigger_b, bus.module.trigger_b, bus.module.trigger_b, bus.module.trigger_b, bus.module.trigger_b],
		'status_key': [bus.data_key.trig_flash_1_status, bus.data_key.trig_flash_2_status, bus.data_key.trig_flash_3_status, bus.data_key.trig_flash_4_status, bus.data_key.trig_flash_5_status, bus.data_key.trig_flash_6_status],
		'fun': _flash_status
	},
	{
		'pos': 'altro',
		'des': 'Videoserver',
		'title': True
	},
	{
		'pos': 'A',
		'des': 'Immagini locali da spedire',
		'module': bus.module.videoserver,
		'status_key': redis_keys.rip_status_field.imgs_to_recover
	},
	{
		'pos': 'B',
		'des': 'Server sshfs',
		'module': bus.module.videoserver,
		'status_key': redis_keys.rip_status_field.sshfs_connected,
		'fun': _online_resource
	},
	{
		'pos': 'C',
		'des': 'Broker Kafka',
		'module': bus.module.videoserver,
		'status_key': redis_keys.rip_status_field.broker_connected,
		'fun': _online_resource
	},
	{
		'pos': 'altro',
		'des': 'Fotocamere',
		'title': True
	},
	{
		'pos': '1P',
		'des': 'Camera 1 pari',
		'module': bus.module.cam1_a,
		'status_key': bus.module.cam1_a,
		'fun': _online_resource
	},
	{
		'pos': '2P',
		'des': 'Camera 2 pari',
		'module': bus.module.cam2_a,
		'status_key': bus.module.cam2_a,
		'fun': _online_resource
	},
	{
		'pos': '3P',
		'des': 'Camera 3 pari',
		'module': bus.module.cam3_a,
		'status_key': bus.module.cam3_a,
		'fun': _online_resource
	},
	{
		'pos': '4P',
		'des': 'Camera 4 pari',
		'module': bus.module.cam4_a,
		'status_key': bus.module.cam4_a,
		'fun': _online_resource
	},
	{
		'pos': '5P',
		'des': 'Camera 5 pari',
		'module': bus.module.cam5_a,
		'status_key': bus.module.cam5_a,
		'fun': _online_resource
	},
	{
		'pos': '6P',
		'des': 'Camera 6 pari',
		'module': bus.module.cam6_a,
		'status_key': bus.module.cam6_a,
		'fun': _online_resource
	},
	{
		'pos': '1D',
		'des': 'Camera 1 dispari',
		'module': bus.module.cam1_b,
		'status_key': bus.module.cam1_b,
		'fun': _online_resource
	},
	{
		'pos': '2D',
		'des': 'Camera 2 dispari',
		'module': bus.module.cam2_b,
		'status_key': bus.module.cam2_b,
		'fun': _online_resource
	},
	{
		'pos': '3D',
		'des': 'Camera 3 dispari',
		'module': bus.module.cam3_b,
		'status_key': bus.module.cam3_b,
		'fun': _online_resource
	},
	{
		'pos': '4D',
		'des': 'Camera 4 dispari',
		'module': bus.module.cam4_b,
		'status_key': bus.module.cam4_b,
		'fun': _online_resource
	},
	{
		'pos': '5D',
		'des': 'Camera 5 dispari',
		'module': bus.module.cam5_b,
		'status_key': bus.module.cam5_b,
		'fun': _online_resource
	},
	{
		'pos': '6D',
		'des': 'Camera 6 dispari',
		'module': bus.module.cam6_b,
		'status_key': bus.module.cam6_b,
		'fun': _online_resource
	}
]