import json

from rigproc.commons import redisi
from rigproc.params import cli, redis_keys


redisI= redisi.staticBuild()


def show(p_msgs):
	width1= 0
	for i, l_msg in enumerate(p_msgs):
		p_msgs[i]= json.loads(l_msg)
	for l_msg in p_msgs:
		l_date, l_time= l_msg['timestamp'].split()
		l_msg['date']= l_date
		l_msg['time']= l_time
		l_max_width= max(len(l_date), len(l_time))
		width1= max(width1, l_max_width)
	answ_counter= 0
	for l_msg in p_msgs:
		try:
			l_out= ''
			l_out += (f'{cli.color.forw_green}{l_msg["date"].rjust(width1)}{cli.color.regular} | Valid:     {l_msg["valid"]}\n')
			l_out += (f'{cli.color.forw_green}{l_msg["time"].rjust(width1)}{cli.color.regular} | Source:    {l_msg["src"]}\n')
			l_out += (f'{" ".rjust(width1)} | Dest:      {l_msg["dest"]}\n')
			l_out += (f'{" ".rjust(width1)} | I/O cmd:   {l_msg["io_cmd"]}\n')
			l_out += (f'{" ".rjust(width1)} | Data:      {l_msg["data"]}\n')
			l_out += (f'{" ".rjust(width1)} | Data size: {l_msg["data_size"]}\n')
			l_out += (f'{" ".rjust(width1)} | Pos:       {l_msg["pos"]}\n')
			l_out += (f'{" ".rjust(width1)} | Message:   {l_msg["msg"]}\n')
			print(l_out)
			answ_counter += 1
		except:
			l_msg.pop('date')
			l_msg.pop('time')
			print(l_msg)
	print(f'\n> {answ_counter}/{len(p_msgs)} messaggi contenevano i campi di una risposta dal bus')


def main():
	l_msgs= redisI.cache.zrange(redis_keys.io_msg.sorted_set, 0, -1)
	show(l_msgs)

if __name__ == '__main__':
	main()