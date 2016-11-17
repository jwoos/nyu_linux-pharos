#!/usr/bin/python2
# Script Name: printerutils.py
# Script Function:
#	This script provides utility functions for dealing with print queues
#
# Author: Junaid Ali
# Version: 1.0

__name__ = 'printerutils'
__version__ = '1.0'

# Imports ===============================

import subprocess
import re
import tempfile
import os
import shutil
import stat

# Class definitions =====================
class PrinterUtility:
	def __init__(self, log):
		self.logger = log

	def printerExists(self, printer):
		"""
		Checks if the given printer device exists
		"""
		self.logger.info('Checking if printer %s exists' %printer)
		printerExistsCommand = ['lpoptions', '-d', printer]

		self.logger.info('Checking if printer %s already exists using command %s' %(printer, printerExistsCommand))
		try:
			printerExistsCommandResult = subprocess.check_output(printerExistsCommand,stderr=subprocess.STDOUT)
			self.logger.info('Result of printer delete command %s' %printerExistsCommandResult)
			if re.search('Unknown printer or class', printerExistsCommandResult):
				self.logger.info('Printer %s does not exists' %printer)
				return False
			else:
				self.logger.info('Printer %s already exists' %printer)
				return True
		except subprocess.CalledProcessError:
			self.logger.info('Could not check if printer exists using lpoptions command or printer does not exists')

		return False

	def deletePrinter(self, printer):
		"""
		Deletes the given printer device
		"""
		self.logger.info('Trying to delete printer device %s' %printer)
		deletePrinterCommand = ['lpadmin', '-x', printer]
		self.logger.info('Trying to delete printer %s using command %s' %(printer, deletePrinterCommand))
		try:
			deletePrinterCommandResult = subprocess.call(deletePrinterCommand)
		except subprocess.CalledProcessError:
			self.logger.error('Could not delete printer %s using lpadmin command' %printer)
			return False

		# check if printer still exists
		if not self.printerExists(printer):
			return True
		else:
			return False

	def enablePrinter(self, printer):
		"""
		Enables printer device
		"""

		acceptPrinterCommand = ['cupsaccept', printer]
		self.logger.info('Trying to enable printer %s using command %s' %(printer, acceptPrinterCommand))
		try:
			acceptPrintCommandResult = subprocess.call(acceptPrinterCommand)
			self.logger.info('Result = %s' %acceptPrintCommandResult)
		except subprocess.CalledProcessError:
			self.logger.error('Could not accept printer %s using cupsaccept command' %printer)
			return False

		enablePrinterCommand = ['cupsenable', printer]
		self.logger.info('Trying to enable printer %s using command %s' %(printer, enablePrinterCommand))
		try:
			enablePrintCommandResult = subprocess.call(enablePrinterCommand)
			self.logger.info('Result = %s' %enablePrintCommandResult)
		except subprocess.CalledProcessError:
			self.logger.error('Could not enable printer %s using cupsenable command' %printer)
			return False

		return True

	def installPrintQueue(self, printer):
		"""
		Install a print queue
		"""
		self.logger.info('Installing printer %s' %printer)

		# check if all required parameters are present
		if printer['driver'] == None or printer['model'] == None or printer['lpdserver'] == None or  printer['lpdqueue'] == None:
			self.logger.error('One of the required parameters (driver, model, lpdserver, lpdqueue) is missing. Cannot add printer')
			return False

		# Query for driver using make and model
		printerDriverPath = ''
		driverFound = False
		if printer['model'] != None:
			printerDriverPath = self.isDriverInstalled(printer['model'], printer['driver'])
			if printerDriverPath  != '':
				driverFound = True

		if driverFound:
			# Check if printer already exists.
			if self.printerExists(printer['printqueue']):
				if self.deletePrinter(printer['printqueue']):
					self.logger.info('Printer %s successfully deleted' %printer['printqueue'])
				else:
					self.logger.error('Printer %s could not be deleted' %printer['printqueue'])
					self.logger.error('Will not try to add the printer again')
					return False

			self.logger.info('Using driver path %s' %printerDriverPath)
			# Build lpadmin Command
			deviceURI = 'pharos://' + printer['lpdserver'] + '/' + printer['lpdqueue']
			lpadminCommand = ['lpadmin', '-E', '-p', printer['printqueue'] , '-v', deviceURI, '-m', printerDriverPath]
			if printer['location'] != None:
				lpadminCommand.append('-L')
				lpadminCommand.append(printer['location'])
			if printer['description'] != None:
				lpadminCommand.append('-D')
				lpadminCommand.append(printer['description'])

			# Run lpadmin command
			try:
				self.logger.info('Adding printer using lpadmin command: %s' %lpadminCommand)
				lpadmin = subprocess.check_output(lpadminCommand)
				self.logger.info('command result = %s' %lpadmin)
			except subprocess.CalledProcessError:
				self.logger.error('Could not add printer using lpadmin')

			# Enable Duplex if needed
			if printer.has_key('duplexerinstalled'):
				# check if HP printer
				if printer.has_key('make'):
					if printer['make'] in ['hp', 'HP', 'Hp', 'hP']:
						self.logger.info('Processing duplex printing for HP printer')
						if printer['duplexerinstalled'] in ['yes', 'Yes', 'yEs', 'yeS', 'YEs', 'yES', 'YES']:
							if self.setDuplexerForHPPrinter(printer['printqueue']):
								self.logger.info('successfully set duplexer for hp printer %s' %printer['printqueue'])
							else:
								self.logger.error('Could not set duplexer for hp printer %s' %printer['printqueue'])
					else:
						self.logger.info('Printer make %s is not special case. Will only process defaultduplex setting' %printer['make'])
				else:
					self.logger.warn('Printer Make is not specified. Will only process defaultduplex setting')

			# Default Duplex Printing
			if printer.has_key('defaultduplex'):
				if printer['defaultduplex'] in ['yes', 'Yes', 'yEs', 'yeS', 'YEs', 'yES', 'YES']:
					# check if HP printer
					if printer.has_key('make'):
						if printer['make'] in ['hp', 'HP', 'Hp', 'hP']:
							self.logger.info('Setting default duplex printing for HP printer %s' %printer['printqueue'])
							if self.setDefaultDuplexPrintingForHPPrinter(printer['printqueue']):
								self.logger.info('successfully set default duplex printing for hp printer %s' %printer['printqueue'])
							else:
								self.logger.error('Could not set default duplex printing for hp printer %s' %printer['printqueue'])

					if self.setDefaultDuplexPrinting(printer['printqueue']):
						self.logger.info('Successfully enabled duplexing for printer %s' %printer['printqueue'])
					else:
						self.logger.warn('Could not enable duplexing for printer %s' %printer['printqueue'])

			# Enable Printer
			if self.enablePrinter(printer['printqueue']):
				self.logger.info('Successfully enabled printer %s' %printer['printqueue'])
			else:
				self.logger.warn('Could not enable printer %s' %printer['printqueue'])

			if self.printerExists(printer['printqueue']):
				self.logger.info('Successfully created printer %s' %printer['printqueue'])
				return True
			else:
				self.logger.error('Could not create printer %s' %printer['printqueue'])
				return False

		else:
			self.logger.info('Could not find the required driver installed on the system. Cannot install printer')
			return False

	def queryPrinterOption(self, printer, option='all'):
		"""
		Queries the printer for a specific option or all options
		"""
		queryCommand = ['lpoptions', '-p', printer]
		value = ''
		allOptionsDictionary = {}
		self.logger.info('Querying printer %s for option %s' %(printer, option))
		try:
			lpoption = subprocess.check_output(queryCommand)
			allOptions = lpoption.split(' ')
			for pOption in allOptions:
				if re.search('=', pOption):
					allOptionsDictionary[pOption.split('=')[0].strip()] = pOption.split('=')[1].strip()

			if option != 'all':
				if allOptionsDictionary.has_key(option):
					value = allOptionsDictionary[option]

		except subprocess.CalledProcessError:
			self.logger.error('Could not set option %s with value %s printer %s' %(option, value, printer))

		if option != 'all':
			if value != '':
				self.logger.info('The printer has option %s set to %s' %(option, value))
			return value
		else:
			return allOptionsDictionary

	def setPrinterOption(self, printer, option, value):
		"""
		Sets a given option for the printer device
		"""
		self.logger.info('Setting option %s with value %s for printer %s' %(option, value, printer))
		optionString = option + "=" + value
		printerOptionCommand = ['lpoptions', '-p', printer, '-o', optionString]
		self.logger.info('Running lptions command %s' %printerOptionCommand)
		try:
			lpoption = subprocess.check_output(printerOptionCommand)
		except subprocess.CalledProcessError:
			self.logger.error('Could not set option %s with value %s printer %s' %(option, value, printer))
			return False

		self.logger.info('Checking if option was correctly set')
		currentValue = self.queryPrinterOption(printer, option)
		if currentValue == value:
			self.logger.info('The option %s has been correctly setup to %s for printer %s' %(option, value, printer))
		else:
			self.logger.warn('The option %s has been incorrectly setup to %s for printer %s' %(option, currentValue, printer))

	def setDuplexerForHPPrinter(self, printer):
		"""
		Enables the Duplexing unit for the HP printer
		"""
		self.logger.info('Enabling duplex unit for HP printer %s' %printer)

		# Update the driver ppd
		ppdFile = os.path.join('/etc/cups/ppd', printer + '.ppd')
		newppdFile = tempfile.NamedTemporaryFile(delete=False)

		self.logger.info('Checking if ppd file %s exists' %ppdFile)
		if os.path.exists(ppdFile):
			self.logger.info('ppd file %s exists' %ppdFile)
			ppd = open(ppdFile, 'r')
			for line in ppd:
				if line.startswith("*DefaultOptionDuplex: False", 0, len("*DefaultOptionDuplex: False")):
					newppdFile.writelines('*DefaultOptionDuplex: True\n')
				elif line.startswith("*cupsEvenDuplex: True", 0, len("*cupsEvenDuplex: True")):
					newppdFile.writelines('*cupsEvenDuplex: False\n')
				else:
					newppdFile.writelines(line)
			newppdFile.close()
			ppd.close()
			self.logger.info('successfully created file %s' %newppdFile.name)
			try:
				shutil.copy(newppdFile.name, ppdFile)
				self.logger.info('Successfully copied the modified ppd file to %s' %ppdFile)

				# update permission on new file
				if os.path.exists(ppdFile):
					self.logger.info('Updating permissions on file %s' %ppdFile)
					try:
						chmod = subprocess.call(['chmod', '644', ppdFile])
					except subprocess.CalledProcessError:
						self.logger.error('Could not change permission for file %s' %ppdFile)

				# delete temp file
				os.remove(newppdFile.name)
				self.logger.info('Successfully deleted file %s' %newppdFile)
			except IOError as (errCode, errMessage):
				logger.error('Could not copy file %s to %s' %(newppdFile.name, ppdFile))
				logger.error('Error: %s Message: %s' %(errCode, errMessage))
		else:
			self.logger.warn('ppd file %s does not exists' %ppdFile)

		self.logger.info('Successfully enabled duplex unit for printer %s' %printer)
		return True

	def setDefaultDuplexPrintingForHPPrinter(self, printer):
		"""
		Enables duplexing for HP printer
		"""
		self.logger.info('Enabling duplex printing for HP printer %s' %printer)

		# Update the driver ppd
		ppdFile = os.path.join('/etc/cups/ppd', printer + '.ppd')
		newppdFile = tempfile.NamedTemporaryFile(delete=False)

		self.logger.info('Checking if ppd file %s exists' %ppdFile)
		if os.path.exists(ppdFile):
			self.logger.info('ppd file %s exists' %ppdFile)
			ppd = open(ppdFile, 'r')
			for line in ppd:
				if line.startswith("*DefaultDuplex: None", 0, len("*DefaultDuplex: None")):
					newppdFile.writelines('*DefaultDuplex: DuplexNoTumble\n')
				elif line.startswith("*DefaultOptionDuplex: False", 0, len("*DefaultOptionDuplex: False")):
					newppdFile.writelines('*DefaultOptionDuplex: True\n')
				else:
					newppdFile.writelines(line)
			newppdFile.close()
			ppd.close()
			self.logger.info('successfully created file %s' %newppdFile.name)
			try:
				shutil.copy(newppdFile.name, ppdFile)
				self.logger.info('Successfully copied the modified ppd file to %s' %ppdFile)

				# update permission on new file
				if os.path.exists(ppdFile):
					self.logger.info('Updating permissions on file %s' %ppdFile)
					try:
						chmod = subprocess.call(['chmod', '644', ppdFile])
					except subprocess.CalledProcessError:
						self.logger.error('Could not change permission for file %s' %ppdFile)

				# delete temp file
				os.remove(newppdFile.name)
				self.logger.info('Successfully deleted file %s' %newppdFile)
			except IOError as (errCode, errMessage):
				logger.error('Could not copy file %s to %s' %(newppdFile.name, ppdFile))
				logger.error('Error: %s Message: %s' %(errCode, errMessage))
		else:
			self.logger.warn('ppd file %s does not exists' %ppdFile)

		self.logger.info('Successfully enabled duplexing for printer %s' %printer)
		return True

	def setDefaultDuplexPrinting(self, printer):
		"""
		Enables default duplex printing
		"""
		self.logger.info('Setting default duplex printing for printer %s' %printer)

		enableDuplexCommand = ['lpoptions', '-p', printer, '-o', 'duplex=DuplexNoTumble']
		self.logger.info('Enabling duplex printing for printer %s using command %s' %(printer, enableDuplexCommand))
		try:
			lpinfo = subprocess.check_output(enableDuplexCommand)
		except subprocess.CalledProcessError:
			self.logger.error('Could not enable duplexing for printer %s' %printer)
			return False

		self.logger.info('Successfully set default duplexing for printer %s' %printer)
		return True

	def getAllPrinters(self):
		"""
		returns all printers by queue backend
		e.g. lpd, usb, socket, etc.
		"""
		allPrinters = {}
		self.logger.info('Getting list of all printers by queue backend type')
		queryPrinterCommand = ['lpstat', '-p']
		printersList = []
		self.logger.info('Querying printers using command %s' %queryPrinterCommand)
		try:
			lpstat = subprocess.check_output(queryPrinterCommand)
			printersStat = lpstat.split('\n')
			for printerStat in printersStat:
				if re.match('^printer\s(?P<printer>[\w\s]+)\sis[\w\s]+', printerStat):
					printersList.append(re.match('^printer\s(?P<printer>[\w\s]+)\sis[\w\s]+', printerStat).group('printer'))
			self.logger.info('All printers = %s' %printersList)
		except subprocess.CalledProcessError:
			self.logger.error('Could not query all printers printer using lpstat')

		if len(printersList) > 0:
			for printer in printersList:
				allPrinters[printer] = self.queryPrinterOption(printer, option='all')
		self.logger.info('All printer = %s' %allPrinters)
		return allPrinters

	def isDriverInstalled(self, printerModel, printerDriver):
		"""
		Checks if the given driver for the given printer model is installed on the system
		Returns the printerDriverPath
		"""
		printerDriverPath = ''
		self.logger.info('Checking if driver %s is installed on the system for model %s' %(printerDriver, printerModel))

		# Fix Driver Name
		if printerDriver != None:
			self.logger.info('Printer driver <%s> is defined for printer model %s' %(printerDriver, printerModel))
			self.logger.info('Fixing Printer driver name')
			if re.search('\(|\)', printerDriver):
				self.logger.info('Printer Driver name <%s> contains brackets' %printerDriver)
				printerDriver = re.sub('\(', '\(', printerDriver)
				printerDriver = re.sub('\)', '\)', printerDriver)
				self.logger.info('Printer driver after fixing brackets: %s' %printerDriver)

		try:
			lpinfo = subprocess.check_output(['lpinfo', '--make-and-model', printerModel, '-m'])
		except subprocess.CalledProcessError:
			self.logger.error('Could not get printer driver details using lpinfo')
			return printerDriverPath

		# Process results of lpinfo
		driversList = lpinfo.split('\n')
		self.logger.info('Total %d drivers returned for <%s> make and model' %(len(driversList), printerModel))
		for driver in driversList:
			driverPath = driver.split(' ')[0]
			driverName = driver.lstrip(driverPath)
			# remove white spaces if any
			driverPath = driverPath.strip()
			driverName = driverName.strip()
			if driverName != '':
				self.logger.info('checking if driver <%s> matches <%s>' %(driverName, printerDriver))
				if re.search(printerDriver, driverName):
					self.logger.info('Driver matches')
					driverFound = True
					printerDriverPath = driverPath
					break
				else:
					self.logger.info('Driver %s does not match' %driverName)

		self.logger.info('Returing driver path %s' %printerDriverPath)
		return printerDriverPath
