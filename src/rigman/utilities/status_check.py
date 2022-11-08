from rigman.utilities.implant_check import get_implant_status, show


if __name__ == '__main__':
	data= get_implant_status()
	show(data)