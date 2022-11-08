from enum import Enum


class color(str, Enum):
	regular=        '\x1b[0m'
	forw_gray=    	'\x1b[1;30;40m'
	back_gray=		'\x1b[6;30;40m'
	forw_yellow=    '\x1b[1;33;40m'
	back_yellow=    '\x1b[0;30;43m'
	forw_red=       '\x1b[1;31;40m'
	back_red=      	'\x1b[0;30;41m'
	forw_green=     '\x1b[0;32;40m'
	back_green=    	'\x1b[0;30;42m'
	back_white=    	'\x1b[0;30;47m'

	# White bg
	back_white_forw_black= 	'\x1b[2;30;47m' # white bg black text
	back_white_forw_red= 	'\x1b[2;31;47m' # white bg red text
	back_white_forw_green= 	'\x1b[2;32;47m' # white bg green text
	back_white_forw_yellow= '\x1b[2;33;47m' # white bg yellow text
	back_white_forw_blue= 	'\x1b[2;34;47m' # white bg blue text
	back_white_forw_violet= '\x1b[2;35;47m' # white bg violet text
	back_white_forw_teal=	'\x1b[2;36;47m' # white bg teal text
	back_white_forw_gray=	'\x1b[2;37;47m' # white bg gray text

	# Light blue bg
	back_sky_forw_black= 	'\x1b[2;30;46m' # light blue bg black text
	back_sky_forw_red= 		'\x1b[2;31;46m' # light blue bg red text
	back_sky_forw_green= 	'\x1b[2;32;46m' # light blue bg green text
	back_sky_forw_yellow= 	'\x1b[2;33;46m' # light blue bg yellow text
	back_sky_forw_blue= 	'\x1b[2;34;46m' # light blue bg blue text
	back_sky_forw_violet= 	'\x1b[2;35;46m' # light blue bg violet text
	back_sky_forw_teal= 	'\x1b[2;36;46m' # light blue bg teal text
	back_sky_forw_gray= 	'\x1b[2;37;46m' # light blue bg gray text

