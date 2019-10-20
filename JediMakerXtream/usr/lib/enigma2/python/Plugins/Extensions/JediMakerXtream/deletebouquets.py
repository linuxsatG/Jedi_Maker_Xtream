#!/usr/bin/python
# -*- coding: utf-8 -*-

# for localized messages  	 
from . import _

from collections import OrderedDict
from Components.ActionMap import ActionMap
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from plugin import skin_path, cfg, playlist_file
from Screens.Screen import Screen

from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER

import os, json, re
import jediglobals as jglob
import globalfunctions as jfunc


class JediMakerXtream_DeleteBouquets(Screen):   
		
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		skin = skin_path + 'jmx_bouquets.xml'
		with open(skin, 'r') as f:
			self.skin = f.read()    
		self.setup_title = _('Delete Bouquets')
		
		#new list code
		self.startList = []
		self.drawList = []
		self['list'] = List(self.drawList) 
		
		self['key_red'] = StaticText(_('Cancel'))
		self['key_green'] = StaticText(_('Delete'))
		self['key_yellow'] = StaticText(_('Invert'))
		self['key_blue'] = StaticText(_('Clear All'))
		self['key_info'] = StaticText('')
		self['description'] = Label(_('Select all the iptv bouquets you wish to delete. \nPress OK to invert the selection'))
		self['lab1'] = Label('')
		
		self.playlists_all = jfunc.getPlaylistJson()
		
		self.onLayoutFinish.append(self.__layoutFinished)
		
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'], {
		 'red': self.keyCancel,
		 'green': self.deleteBouquets,
		 'yellow': self.toggleAllSelection,
		 'blue': self.clearAllSelection,
		 'save': self.deleteBouquets,
		 'cancel': self.keyCancel,
		 'ok': self.toggleSelection
		 }, -2)
		 
		self.getStartList()
		self.refresh()  

	def __layoutFinished(self):
		self.setTitle(self.setup_title)
		
		
	def buildListEntry(self, name, index, enabled):
		if enabled:
			pixmap = LoadPixmap(cached=True, path=skin_path + "images/lock_on.png")
		else:
			pixmap = LoadPixmap(cached=True, path=skin_path + "images/lock_off.png")

		return(pixmap, str(name), index, enabled)
		
	
	def getStartList(self):
		for playlist in self.playlists_all:
			if 'bouquet_info' in playlist and 'oldname' in playlist['bouquet_info']:
				self.startList.append([str(playlist['bouquet_info']['oldname']), playlist['playlist_info']['index'], False])

		self.drawList = [self.buildListEntry(x[0],x[1],x[2]) for x in self.startList]

		
	def refresh(self):
		self.drawList = []
		self.drawList = [self.buildListEntry(x[0],x[1],x[2]) for x in self.startList]
		self['list'].updateList(self.drawList)
	  
	
	def toggleSelection(self):
		if len(self['list'].list) > 0:
			idx = self['list'].getIndex()
			self.startList[idx][2] = not self.startList[idx][2]
			self.refresh()  
			
	def toggleAllSelection(self):
		for idx, item in enumerate(self['list'].list):
			self.startList[idx][2] = not self.startList[idx][2]
		self.refresh()  
		
	def getSelectionsList(self):
		return [item[0] for item in self.startList if item[2] ]
		
		
	def clearAllSelection(self):
		for idx, item in enumerate(self['list'].list):
			self.startList[idx][2] = False
		self.refresh() 

	def keyCancel(self):                
		self.close()


	def deleteBouquets(self):
		selectedBouquetList = self.getSelectionsList()
		
		for x in selectedBouquetList:
			bouquet_name = x

			cleanName = re.sub(r'[\<\>\:\"\/\\\|\?\*]', '_', str(bouquet_name))
			cleanName = re.sub(r' ', '_', cleanName)
			cleanName = re.sub(r'_+', '_', cleanName)
			
			with open('/etc/enigma2/bouquets.tv', 'r+') as f:
				lines = f.readlines()
				f.seek(0)
				for line in lines:
					if 'jmx_live_' + str(cleanName) + "_" in line or 'jmx_vod_' + str(cleanName) + "_" in line or 'jmx_series_' + str(cleanName)  + "_" in line or 'jmx_' + str(cleanName) in line:
						continue
					f.write(line)
				f.truncate()
			
			jfunc.purge('/etc/enigma2', 'jmx_live_' + str(cleanName)  + "_")
			jfunc.purge('/etc/enigma2', 'jmx_vod_' + str(cleanName)  + "_")
			jfunc.purge('/etc/enigma2', 'jmx_series_' + str(cleanName)  + "_")
			jfunc.purge('/etc/enigma2', str(cleanName) + str('.tv')) 

	

			if jglob.has_epg_importer:
				jfunc.purge('/etc/epgimport', 'jmx.' + str(cleanName) + '.channels.xml')
				jfunc.purge('/etc/epgimport', 'jmx.' + str(cleanName) + '.sources.xml')
		
			jfunc.refreshBouquets()
			self.deleteBouquetFile(bouquet_name)
			jglob.firstrun = 0
			jglob.current_selection = 0
			jglob.current_playlist = []
		self.close()
		

	def deleteBouquetFile(self, bouquet_name):
		
		for playlist in self.playlists_all:
			if 'bouquet_info' in playlist and 'name' in playlist['bouquet_info']:
				if playlist['bouquet_info']['name'] == bouquet_name:
					del playlist['bouquet_info']
					
		jglob.bouquets_exist = False
		for playlist in self.playlists_all:
			if 'bouquet_info' in playlist:
				jglob.bouquets_exist = True
				break

		if jglob.bouquets_exist == False:
			jfunc.resetUnique()
				
		# delete leftover empty dicts
		self.playlists_all = filter(None, self.playlists_all)
		 
		with open(playlist_file, 'w') as f:
			json.dump(self.playlists_all, f)