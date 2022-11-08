from pathlib import Path
import rigboot


rigboot.debug_mode= True
rigboot.check_heartbeat= True
rigboot.exec_type= rigboot.ExecType.PYTHON
rigboot.conda_path= '~/anaconda3/bin'
rigboot.conda_env= 'rigenv'
rigboot.test_launcher= False


conf= str((Path(__file__).parent.parent.parent / 'data' / 'conf_101.json').absolute())
rigboot.main(conf)

