from smbus import SMBus
import curses
import time

def toS16(val):
	if val > 32767:
		val -= 65536
	return val
	
# Configure charger cell voltage and current
def setCharger(bus, volt, curr):
	bus.write_word_data(0x09, 0x14, curr)
	bus.write_word_data(0x09, 0x15, volt)
	bus.write_word_data(0x09, 0x12, 0x9912)

def configureINA219(bus):
	bus.write_word_data(0x40, 0x05, 0x0010) # Calibration
	bus.write_word_data(0x40, 0x00, 0xD739) # Power on 

def getBatteryStatus(bus):
	try:
		batt_volt = (bus.read_word_data(0x0b, 0x09)) / 1000.0
		batt_curr = toS16(bus.read_word_data(0x0b, 0x0a)) / 1000.0
		batt_pcent = bus.read_word_data(0x0b, 0x0d)
	except IOError:
		return 0, 0, 0

	return batt_volt, batt_curr, batt_pcent

def getINA219Status(bus):
	try:
		volt1 = bus.read_word_data(0x40, 0x02)
		curr1 = bus.read_word_data(0x40, 0x01)
	except IOError:
		return 0, 0

	# Endianness swap and multiply with scaling factor
	volt = ((volt1 >> 8) | ((volt1 & 0xFF) << 8)) * 0.0005
	curr = toS16((curr1 >> 8) | ((curr1 & 0xFF) << 8)) * 0.0001

	return (volt, curr)

def main(window):
	batt_det = 1
	chrg_det = 1
	chg_conn = 0
	ina_det = 1

	counter = 0

	# Initialize bus
	bus = SMBus(1)

	window.addstr(0, 0, 'Smarter Power Pack v1.0 Trial');
	
	try:
		batt_volt, batt_curr, percent = getBatteryStatus(bus)
		window.addstr(2, 2, 'Battery detected')
	except IOError,err:
		window.addstr(2, 2, 'Battery not detected!')
		batt_det = 0
	
	try:
		chrg_volt = bus.read_word_data(0x09, 0x15)		
		window.addstr(3, 2, 'Charger detected')
	except IOError,err:
		window.addstr(3, 2, 'Charger not detected!')
		chrg_det = 0

	try:
		configureINA219(bus)
		window.addstr(4, 2, 'INA219 detected')
	except IOError,err:
		window.addstr(4, 2, 'INA219 not detected!')
		ina_det = 0

	window.addstr(6, 0, 'Battery Status')
	window.addstr(10, 0, 'INA219 Status')
	
	while (batt_det | chrg_det | ina_det) != 0:
		try:
			batt_volt, batt_curr, percent  = getBatteryStatus(bus)
			ina_volt, ina_curr = getINA219Status(bus)
			
			window.move(3, 0)			
			
			if chrg_det == 1: 
				window.clrtoeol()
				chg_stat = bus.read_word_data(0x09, 0x12)
				if (chg_stat & 0x0010 == 0x0010):
					window.addstr(3, 2, 'Charger connected')
					if chg_conn == 0 & bus.read_word_data(0x09, 0x14) == 0:
						setCharger(bus, 12600, 4000)
						chg_conn = 1
				else:
					window.addstr(3, 2, 'Charger disconnected')
					if chg_conn == 1:
						setCharger(bus, 0, 0)
						chg_conn = 0

			window.move(8, 0)
			window.clrtoeol()

			counter = counter + 1
			timeto = 0
                        if counter >= 10:
                                counter = 0
				
				# Ask battery about time to empty / time to full
                                # curr = toS16(chrg_curr = bus.read_word_data(0x0B, 0x0a))		
				
				# Clear pending errors
				window.move(14, 0)
				window.clrtoeol()

			window.addstr(8, 2, '{0:.3f} V ({2:d}% charged), {1:.3f} A'.format(batt_volt, batt_curr, percent))
			
			window.move(12, 0)
			if ((ina_volt != 0) | (ina_curr != 0)):
				window.clrtoeol()
				window.addstr(12, 2, '{0:.3f} V, {1:.3f} A'.format(ina_volt, ina_curr))
			
			window.refresh()			
			time.sleep(1)

		except RuntimeError, err:
			# Display error message
			window.addstr(14, 1, 'Error' * err)
			pass

if __name__ == "__main__":
	curses.wrapper(main)

