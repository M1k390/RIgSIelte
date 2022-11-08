"""
Bus requests/responses keys
"""


error= 'error'


class hardware:
	mosf_tx= 'mosf_tx'
	mosf_rx= 'mosf_rx'
	trigger= 'trigger'
	io= 'io'


class module:
	videoserver= 'videoserver'
	
	mosf_tx_a= 'mosf_tx_pari'
	mosf_tx_b= 'mosf_tx_dispari'
	mosf_rx_a= 'mosf_rx_pari'
	mosf_rx_b= 'mosf_rx_dispari'
	trigger_a= 'trigger_pari'
	trigger_b= 'trigger_dispari'
	io= 'io'

	cam1_a= 'camera1_pari'
	cam2_a= 'camera2_pari'
	cam3_a= 'camera3_pari'
	cam4_a= 'camera4_pari'
	cam5_a= 'camera5_pari'
	cam6_a= 'camera6_pari'
	cam1_b= 'camera1_dispari'
	cam2_b= 'camera2_dispari'
	cam3_b= 'camera3_dispari'
	cam4_b= 'camera4_dispari'
	cam5_b= 'camera5_dispari'
	cam6_b= 'camera6_dispari'


class addr:
	videoserver= '@'
	io= 'A'
	mtx_a= 'B'
	mtx_b= 'C'
	mrx_a= 'D'
	mrx_b= 'E'
	trig_a= 'F'
	trig_b= 'G'


class cmd:
	"cmd generici, prefissi senza distinzione prr"
	mrx_wire_t0_generic= 'mrx_wire_t0_'
	mtx_vel_generic= 'mtx_vel_'
	mrx_vel_generic= 'mrx_vel_'
	mrx_wire_gneric= 'mrx_wire_'

	" cmd mnemonici, ad uso interno "
	stop ='stop'
	restart= 'restart'
	mtx_vel_a= 'mtx_vel_a'
	mtx_ver_a= 'mtx_ver_a'
	mrx_ver_a= 'mrx_ver_a'
	mtx_on_off_a= 'mtx_on_off_a'
	mrx_wire_t0_a= 'mrx_wire_t0_a'
	mrx_tmos_a= 'mrx_tmos_a'
	mrx_wire_data_a= 'mrx_wire_data_a'
	trig_ver_a= 'trig_ver_a'
	trig_setting_a= 'trig_setting_a'
	trig_on_off_a= 'trig_on_off_a'
	trig_click_a= 'trig_click_a'
	trig_status_a= 'trig_status_a'

	mtx_vel_b= 'mtx_vel_b'
	mtx_ver_b= 'mtx_ver_b'
	mrx_ver_b= 'mrx_ver_b'
	mtx_on_off_b= 'mtx_on_off_b'
	mrx_wire_t0_b= 'mrx_wire_t0_b'
	mrx_tmos_b= 'mrx_tmos_b'
	mrx_wire_data_b= 'mrx_wire_data_b'
	trig_ver_b= 'trig_ver_b'
	trig_setting_b= 'trig_setting_b'
	trig_on_off_b= 'trig_on_off_b'
	trig_click_b= 'trig_click_b'
	trig_status_b= 'trig_status_b'

	io_ver= 'io_ver'
	io_test_batt= 'io_test_batt'
	io= 'io'


data_len= {
    4: 'P',
    8: 'Q',
    16: 'R',
    32: 'S',
    64: 'T',
    128: 'U',
    256: 'V',
    512: 'W',
    1024: 'X'
}


cmd_codes={
    cmd.mtx_ver_a: chr(96),
    cmd.mtx_vel_a: 'a',
    cmd.mtx_on_off_a: 'b',

    cmd.mrx_ver_a: chr(96),
    cmd.mrx_tmos_a: 'c',
    cmd.mrx_wire_t0_a: 'd',
    cmd.mrx_wire_data_a: 'e',

    cmd.trig_ver_a: chr(96),
    cmd.trig_setting_a: 'f',
    cmd.trig_on_off_a: 'g',
    cmd.trig_click_a: 'h',
    cmd.trig_status_a: 'i',

    cmd.mtx_ver_b: chr(96),
    cmd.mtx_vel_b: 'a',
    cmd.mtx_on_off_b: 'b',

    cmd.mrx_ver_b: chr(96),
    cmd.mrx_tmos_b: 'c',
    cmd.mrx_wire_t0_b: 'd',
    cmd.mrx_wire_data_b: 'e',

    cmd.trig_ver_b: chr(96),
    cmd.trig_setting_b: 'f',
    cmd.trig_on_off_b: 'g',
    cmd.trig_click_b: 'h',
    cmd.trig_status_b: 'i',

    cmd.io_ver: chr(96),
    cmd.io_test_batt: 'j',
    cmd.io: 'k'
}


cmd_codes_reverted= {
    module.videoserver:{},
    module.io: {
        chr(96): cmd.io_ver,
        'j': cmd.io_test_batt,
        'k': cmd.io
    },
    module.mosf_tx_a: {
        chr(96): cmd.mtx_ver_a,
        'a' : cmd.mtx_vel_a,
        'b' : cmd.mtx_on_off_a
    },
    module.mosf_tx_b: {
        chr(96): cmd.mtx_ver_b,
        'a' : cmd.mtx_vel_b,
        'b' : cmd.mtx_on_off_b
    },
    module.mosf_rx_a: {
        chr(96): cmd.mrx_ver_a,
        'c': cmd.mrx_tmos_a,
        'd': cmd.mrx_wire_t0_a,
        'e': cmd.mrx_wire_data_a,
    },
    module.mosf_rx_b: {
        chr(96): cmd.mrx_ver_b,
        'c': cmd.mrx_tmos_b,
        'd': cmd.mrx_wire_t0_b,
        'e': cmd.mrx_wire_data_b,
    },
    module.trigger_a: {
        chr(96): cmd.trig_ver_a,
        'f': cmd.trig_setting_a,
        'g': cmd.trig_on_off_a,
        'h': cmd.trig_click_a,
        'i': cmd.trig_status_a,
    },
    module.trigger_b: {
        chr(96): cmd.trig_ver_b,
        'f': cmd.trig_setting_b,
        'g': cmd.trig_on_off_b,
        'h': cmd.trig_click_b,
        'i': cmd.trig_status_b,
    },
}


class data_key:
	" Dati rilevati dal bus485 "

	mtx_vers= 'mtx_vers'
	mtx_velo= 'mtx_velo'
	mtx_direction= 'mtx_direction'
	mtx_onoff= 'mtx_on_off'
	mtx_event = 'mtx_event'

	mrx_vers= 'mrx_vers'
	mrx_direction = 'mrx_direction'
	mrx_event = 'mrx_event'

	mosf_tpre= 'mosf_tPre'
	mosf_tpost= 'mosf_tPost'
	mosf_wire_t0= 'mrx_wire_t0'
	mosf_wire_data= 'mosf_wire_data'
	mosf_wire_data_ok= 'mosf_wire_data_ok'

	trig_vers= 'trig_vers'
	trig_latency= 'trig_flash_latency'
	trig_exposure= 'trig_flash_exposure'
	trig_click= 'trig_click'
	trig_cam_onoff = 'trig_cam_onoff'
	trig_flash_onoff = 'trig_flash_onoff'
	trig_flash_1_status = 'flash_1_status'
	trig_flash_2_status = 'flash_2_status'
	trig_flash_3_status = 'flash_3_status'
	trig_flash_4_status = 'flash_4_status'
	trig_flash_5_status = 'flash_5_status'
	trig_flash_6_status = 'flash_6_status'
	trig_flash_1_efficiency = 'efficiency_flash_1'
	trig_flash_2_efficiency = 'efficiency_flash_2'
	trig_flash_3_efficiency = 'efficiency_flash_3'
	trig_flash_4_efficiency = 'efficiency_flash_4'
	trig_flash_5_efficiency = 'efficiency_flash_5'
	trig_flash_6_efficiency = 'efficiency_flash_6'

	io_vers = 'io_vers'
	io= 'io'
	io_battery= 'io_battery'
	io_alim_batt= 'alim_batt'
	io_alim_24= 'alim_24vcc'
	io_sw_armadio= 'sw_armadio'
	io_rip_status = 'rip_status'
	io_rv_pari= 'rv_pari'
	io_sw_prr_pari= 'sw_prr_pari'
	io_rv_dispari= 'rv_dispari'
	io_sw_prr_dispari= 'sw_prr_dispari'
	io_ntc_c= 'ntc-c'
	io_test_batt = 'io_test_batt'

	io_IVIP_power= 'io_ivip_power'
	io_switch_prr_a= 'switch_prr_pari'
	io_switch_prr_b= 'switch_prr_dispari'
	io_ldc_a= 'ldc_prr_pari'
	io_ldc_b= 'ldc_prr_dispari'
	io_doors= 'door_opend'
	io_sens1= 'sens1'
	io_sens2= 'sens2'
	io_vent1= 'vent1'
	io_vent2= 'vent2'
	io_led= 'led'


class data_val:
	" COM data decoded keywords "

	direction_legal= "legale"
	direction_illegal= "illegale"
	bin_pari= "pari"
	bin_dispari= "dispari"

	alim_batt= 'alim_battery'
	alim_alim= 'alim_24vcc'

	flash_0= '0'
	flash_50= '50'
	flash_80= '80'
	flash_100= '100'


class mtx_event:
	" MOSF TX events "
	attesa_trigger= 'mtx_event_attesa_trigger'
	ok_trigger= 'mtx_event_ok_trigger'
	attesa_treno= 'mtx_event_attesa_treno'
	err_rimbalzo1= 'mtx_event_err_rimbalzo1'
	err_rimbalzo2= 'mtx_event_err_rimbalzo2'
	err_vel0_high= 'mtx_event_err_vel0_high'
	err_vel1_high= 'mtx_event_err_vel1_high'
	err_vel0_low= 'mtx_event_err_vel0_low'
	err_vel1_low= 'mtx_event_err_vel1_low'
	err_trigger0= 'mtx_event_err_trigger0'
	err_trigger1= 'mtx_event_err_trigger1'
	err_sens_vel1= 'mtx_event_err_sens_vel1'
	err_sens_vel2= 'mtx_event_err_sens_vel2'
	err_sens_vel1_2= 'mtx_event_err_sens_vel1_2'


mtx_event_errors= [
    mtx_event.err_rimbalzo1,
    mtx_event.err_rimbalzo2,
    mtx_event.err_vel0_high,
    mtx_event.err_vel1_high,
    mtx_event.err_vel0_low,
    mtx_event.err_vel1_low,
    mtx_event.err_trigger0,
    mtx_event.err_trigger1,
    mtx_event.err_sens_vel1,
    mtx_event.err_sens_vel2,
    mtx_event.err_sens_vel1_2
]


mtx_event_labels = {
    mtx_event.attesa_trigger: 'Attesa trigger',
    mtx_event.ok_trigger: 'OK trigger',
    mtx_event.attesa_treno: 'Stato attesa treno',
    mtx_event.err_rimbalzo1: 'Errore rimbalzo 1 (0x40)',
    mtx_event.err_rimbalzo2: 'Errore rimbalzo 2 (0x41)',
    mtx_event.err_vel0_high: 'Errore velocità0 > 470 km/h (0x42)',
    mtx_event.err_vel1_high: 'Errore velocità1 > 470 km/h (0x43)',
    mtx_event.err_vel0_low: 'Errore velocità0 < 7 km/h (0x44)',
    mtx_event.err_vel1_low: 'Errore velocità1 < 7 km/h (0x45)',
    mtx_event.err_trigger0: 'Errore Trigger0 (0x46)',
    mtx_event.err_trigger1: 'Errore Trigger1 (0x47)',
    mtx_event.err_sens_vel1: 'Errore SensoreVelocità1 (0x48)',
    mtx_event.err_sens_vel2: 'Errore SensoreVelocità2 (0x49)',
    mtx_event.err_sens_vel1_2: 'Errore SensoreVelocità1-2 (0x4a)'
}


class mrx_event:
	attesa_trigger= 'mrx_event_attesa_trigger'
	ok_trigger= 'mrx_event_ok_trigger'
	attesa_treno= 'mrx_event_attesa_treno'
	err_all_outall= 'mrx_event_err_all_outall'
	err_all_outhigh= 'mrx_event_err_all_outhigh'
	err_all_outlow= 'mrx_event_err_all_outlow'
	err_all_unreliable= 'mrx_event_err_all_unreliable'


mrx_event_labels = {
	mrx_event.attesa_trigger: 'Attesa trigger',
    mrx_event.ok_trigger: 'OK trigger',
    mrx_event.attesa_treno: 'Stato attesa treno/pant.',
    mrx_event.err_all_outall: 'Errore MOSF_RX Allineamento OutAll (0x40)',
    mrx_event.err_all_outhigh: 'Errore MOSF_RX Allineamento OutHigh (0x41)',
    mrx_event.err_all_outlow: 'Errore MOSF_RX Allineamento OutLow (0x42)',
    mrx_event.err_all_unreliable: 'Errore MOSF_RX Allineamento Unreliable (0x43)',
}


class binary:
	decimal_zero = 0x30
	decimal_max = 0x39
	day_one = 0x31
	day_max = 0x4f
	month_one = 0x31
	month_max = 0x3c
	year_zero = 0x30
	year_max = 0x39
	year_offset = 2020


class mosf_data:
	zero_value= 0x20
	max_value= 0x7f
	max_pre_time= 25
	max_post_time= 25 
	default= 25



