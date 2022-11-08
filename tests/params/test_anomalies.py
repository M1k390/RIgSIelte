from rigproc.params import anomalies


def test_anomalies_integrity():
	def check_val_anomaly(t_dict: dict):
		for val in t_dict.values():
			if isinstance(val, dict):
				check_val_anomaly(val)
			else:
				print(f'Checking {val}')
				assert isinstance(val, anomalies.Anomaly)
	check_val_anomaly(anomalies.status_errors_reference)