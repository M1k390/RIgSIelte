from pathlib import Path
import rigboot


rigboot.debug_mode= True
rigboot.check_heartbeat= True
rigboot.exec_type= rigboot.ExecType.PYTHON
rigboot.conda_path= '/opt/miniconda3'
rigboot.conda_env= 'rigenv'
rigboot.test_launcher= False


conf= str((Path(__file__).parent.parent.parent / 'data' / 'conf_111.json').absolute())
rigboot.main(conf)

