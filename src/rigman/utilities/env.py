import psutil

def findProcess(p_cmdline, p_port):
    """
    Ricerca istanza processo attraveso cmdline e port number

    Parameters
    ----------
    p_cmdline: str
        Riga di lancio del processo da cercare
    p_port: str
        Porta da cercare all'interno della riga di lancio
    Return
    ------
    True processo trovato
    """
    process= []
    for proc in psutil.process_iter():
        try:
            pinfo= proc.as_dict()
            if  p_cmdline in pinfo['cmdline'][0]:
                process.append(pinfo['cmdline'][0])  
        except:
            pass
    if p_port == None:
        if len(process):
            return True
    else:                
        p_port= str(p_port)
        for proc in process:
            if p_port in proc:
                return True
    return False

process_dict= {
    'redis_cache': ['redis-server', 6379],
    'redis_persistent': ['redis-server', 6380],
    'kafka': ['kafka/bin', None],
    'zookeeper':['zookeeper.properties', None]
}

def SimpleEnvScan(p_proc_list):
    """
    Scansione delle righe di comando richieste
    """
    for key,value in p_proc_list.items():
        print("checking " + key +" : " )
        l_found= findProcess(value[0], value[1])
        print(l_found)


def ScanEnv():
    """ 
    Func wrapper, scansione presenza processi ambiente di lavoro
    """
    SimpleEnvScan(process_dict)
