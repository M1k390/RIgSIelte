import logging

from rigproc.commons import keywords

class WrapKey:
    """ 
    Wrapper errori chiavi dizionari o chiavi in generale
    """

    def __init__(self):
        self.m_logger= logging.getLogger('root')

    def getValueError(self, p_data, *p_keys):
        """
        Estrae un valore da un dict, se manca la chiave marca incomplete

        Parameters
        ----------
            p_data: Dictionary
                data structure
            p_key: String
                key to get
        Returns
        -------
            key value, eccezione
        """
        l_def= keywords.status_inactive
        l_ret= l_def
        l_err= None if len(p_keys) else 'missing_key'
        l_data= p_data
        for l_key in p_keys:
            try:
                l_data= l_data[l_key]
                l_ret= l_data
            except Exception as e:
                self.m_logger.error(f'Chiave "{l_key}" (di {p_keys}) non trovata in {p_data}')
                return l_def, str(e)
        return l_ret, l_err
    
    def getValue(self, p_data, *p_keys):
        """
        Estrae un valore da un dict, se manca la chiave marca incomplete

        Parameters
        ----------
            p_data: Dictionary
                data structure
            p_keys: String (multiple)
                key (or nested keys) to get
        Returns
        -------
            key value, 'inactive'
        """
        return self.getValueDefault(p_data, keywords.status_inactive, *p_keys)

    def getValueDefault(self, p_data, p_default, *p_keys):
        """
        Estrae un valore da un dict, se manca la chiave marca incomplete

        Parameters
        ----------
            p_data: Dictionary
                data structure
            p_default: Default value
            p_keys: String (multiple)
                keys (or nested keys) to get
        Returns
        -------
            key value, default value
        """
        l_ret=p_default        
        l_data= p_data
        for l_key in p_keys:
            try:
                l_data= l_data[l_key]
                l_ret= l_data
            except:
                self.m_logger.error(f'Chiave "{l_key}" (di {p_keys}) non trovata in {p_data}')
                return p_default
        return l_ret

    def setValue(self, p_data, p_value, *p_keys) -> bool:
        """ 
        Inserisce un valore in una chiave o una serie di chiavi annidate di un dict
        Nel caso di chaivi annidate, se queste non esistono, le crea e inserisce come valore un dict vuoto
        Ritorna True se l'operazione è andata a buon fine
        Ritorna False se l'oggetto iniziale non è un dict, e non fa niente
        Se trova un parametro che non è un dict lungo il percorso di chiavi, lo sovrascrive
        """
        if isinstance(p_data, dict):
            l_data= p_data
            for l_key in p_keys[:-1]:
                if l_key not in l_data.keys():
                    l_data[l_key]= {}
                if not isinstance(l_data[l_key], dict):
                    l_data[l_key]= {}
                l_data= l_data[l_key]
            l_data[p_keys[-1]]= p_value
            return True
        else:
            self.m_logger.error(f'Tried to insert a key, value in a non-dict object: {p_data}')
            return False

    def compareValue(self, p_data, p_key, p_compare):
        """ Compare la chiave del campo dati con il valore fornito
        se la chiave manca da false
        """
        try:
            if p_data[p_key] ==  p_compare:
                return True
            else:
                return False
        except KeyError:
            return False


" ISTANZA "      

wrapkeys= WrapKey()