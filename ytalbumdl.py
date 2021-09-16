from genericpath import exists
from youtube_dl.utils import DownloadError
from youtubesearchpython.extras import Video
from youtubesearchpython import Playlist, VideosSearch
from pyperclip import paste
from playsound import playsound
from os import path, remove
from ffmpeg_progress_yield import FfmpegProgress
from sys import argv
from threading import Thread, active_count
import youtube_dl
import spotify_webapi as sp
from tkinter import Tk, StringVar, Label, ttk, IntVar

#some tkinter variables
root = Tk()
progressbars = []
progressbar_labels = []
progressbar_labels_text = []
progressbars_progress = []

#max number of download threads
num_of_threads = 4

#if thread throws an error it gets logged here for thread_controller to use
thread_errors = [0] * num_of_threads



#deals with displaying progress to gui window
def a(text, thread, progress):
	global progressbar_labels_text
	global progressbars_progress
	progressbar_labels_text[thread].set(text)
	progressbars_progress[thread].set(progress)
 
 
#cleans up filename to match output of ytdl
def clean_up_string(new_string):   
	for i in '\\/|*<>':
		if i in new_string:
			new_string = new_string.replace(i, '_')
	if '?' in new_string:
		new_string = new_string.replace('?', '')
	if '"' in new_string:
		new_string = new_string.replace('"', '\'')
	if ':' in new_string:
		new_string = new_string.replace(':', ' -')

	return new_string


#splits list for threads
def split_string(arr: list, x: int) -> list:
	global num_of_threads
	elements_for_each_chunk = int(len(arr)/x)
	if num_of_threads > len(arr):
		num_of_threads = len(arr)
	res = []
	count = 0

	#splits list into x even sized sublists
	for i in range(0, x):
		res.append(arr[count:count+elements_for_each_chunk])
		count += elements_for_each_chunk
  
	#distributes remaining items in list into sublists
	if (rem := len(arr) % x) >= 1:
		j = 0
		for i in arr[count:count+rem]:	
			res[j].append(i)
			j += 1
	return res


#file converter
def convert(list1, threads=0, thread_num=1):
	current_index = 1
	filename= ''
	for i in list1:
		print('                                                                   ', end='\r')
	  
		#get full filename 
		filename = clean_up_string(Video.get(i)['title'])
  
		#ffmpeg options
		cmd = ["ffmpeg", "-threads", f"{threads}", "-i", f"{filename}.webm", f"{filename}.mp3"]
  
		if not exists(f"{filename}.mp3"):
			ff = FfmpegProgress(cmd)
			for progress in ff.run_command_with_progress():
					a(f"Converting Song {current_index} of {len(list1)}      {progress}%", thread_num - 1, progress)
		else: print(f"File: {filename}.mp3 already exists")
		
		if exists(f"{filename}.webm"):
			#delete .webm file
			remove(f"{filename}.webm")

		current_index += 1
	print('                                                                   ', end='\r')
	print(f"successfully closed thread {thread_num}")
	a('Done', thread_num-1, 100)
	#print('\n', end='\r')

	
#downloader function
def download(list1, thread_num = 0):
	print(f"successfully started thread {(thread_num + 1)}")
	global thread_errors
	current_index = 0

	#progress hook
	def my_hook(d):
		if(d['status'] == 'downloading'):
			num = str(round(int(d['downloaded_bytes'])/int(d['total_bytes'])*100))
			a(f"Downloading Song {current_index} of {len(list1)}      {num}%",thread_num, num)


	#options for youtube_dl
	yld_opts = {
		'outtmpl': '%(title)s.%(ext)s',
		'quiet':True,
		'format' : '251',
		'progress_hooks' : [my_hook],
	}

	try:
		#run youtube-dl
		ydl = youtube_dl.YoutubeDL(yld_opts)
		ydl._ies = [ydl.get_info_extractor('Youtube')]
		for i in range(len(list1)):
			current_index = i + 1
			print('                                                                   ', end='\r')


			filename = clean_up_string(Video.getInfo(list1[i])['title'])
			if not exists(f"{filename}.mp3"):
				ydl.download([list1[i]])

		#convert downloaded .webm files to .mp3
		try:
			convert(list1, 0, (thread_num + 1))
		except RuntimeError:
			return
	except DownloadError:
		thread_errors[thread_num] = 1
	
 
#thread controller
def thread_controller(list1):
	global thread_errors
	
	if len(list1) > 1:
		#starts threads
		for i in range(num_of_threads):
			k = Thread(target=download, args=(list1[i],i,))
			k.daemon=True
			k.start()

	else:
		k = Thread(target=download, args=(list1,))
		k.daemon = True
		k.start()
	
	#if one of the threads quits because youtube-dl throws a DownloadError exception restarts thread
	while active_count() > 2:
		for i in range(len(thread_errors)):
			if thread_errors[i] == 1:
				print(f"thread {i} failed, restarting thread")
				k = Thread(target=download, args=(list1[i],i))
				k.daemon=True
				k.start()
				thread_errors[i] = 0
    #play bell sound when finished
	playsound((path.dirname(__file__) + '\\extra\\bell.wav'))
	root.destroy()
    
    
#url handler obvs
def url_handler(video_url):

	# 1 means Playlist while 2 means individual video
	url_type = 0

	#checks if url is a valid url
	if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
		if 'spotify.com' not in video_url or not video_url:
			print("Enter a valid song URL")
			input("press enter key to exit...")
			return

	#if the url is from youtube
	if 'youtube.com' in video_url or 'youtu.be' in video_url:
     
		#if playlist url
		if 'playlist' in video_url:
			url_type = 1

		#if url is video in playlist rather than playlist url itself, this converts it
		elif 'list' in video_url:
			ver = input("video is in playlist, download single video? y/n: ")
	
			if ver.lower() == "n":
				new_list = video_url.split('&')
				video_url = "https://www.youtube.com/playlist?" + new_list[1]
				url_type = 1
	
			elif ver.lower() == "y":
				new_list = video_url.split('&')
				video_url = new_list[0]
				url_type = 2

			else:
				print("enter y or n")
				input("press any key to exit...")
				return
				

		#if single video
		elif 'watch' in video_url or 'youtu.be' in video_url:
			url_type = 2
  
	#if the url is from spotify
	elif 'spotify.com' in video_url:
		print("Warning, spotify support is experimental may not work as expected...")
		if 'playlist' in video_url or 'album' in video_url:
			url_type = 3

		elif 'track' in video_url:
			url_type = 4

	#list of videos
	new_list = []
	list1 = []
 
	#defaults to 1 for single video
	video_count = 1


	#if yt playlist
	if url_type == 1:

		#gets urls of videos in playlist and saves to list
		videos = Playlist.getVideos(video_url)['videos']
		for i in videos:
			new_list.append(i['link'].split('&')[0])
   
		list1 = split_string(new_list, num_of_threads)
  
	#if single yt video
	elif url_type == 2:
		list1.append(video_url)

	#if spotify playlist or album
	elif url_type == 3:
		pl = sp.Playlist(video_url)
		playlist_tracks = []


		for i in pl.tracks:
			search_result = VideosSearch((i.title + ' '  + i.artist + ' ' + pl.title), limit=5).result()['result']
			j = 0
			while True:
				if 'video' not in search_result[j]['title']:
					new_list.append(search_result[j]['link'])
					j += 1
					break
			list1 = split_string(new_list, num_of_threads)

	#if single spotify track
	elif url_type == 4:
		tr = sp.Track(video_url)
		search_result = VideosSearch((tr.title + ' ' + tr.artist), limit=5).result()['result']
		for i in range(5):
			if 'video' not in search_result[i]['title']:
				list1.append(search_result[i]['link'])
				break

	thread_controller(list1)
      
#driver code
if __name__ == "__main__":
    
	try:

		#if program is run with -i option get url from command line rather than clipboard
		if '-i' in argv:
			if not argv[argv.index('-i') + 1][0] == '-':
				video_url = argv[argv.index('-i') + 1]
    
		else:
			#gets URL of playlist or video from user clipboard
			video_url = paste()
   
		#-t option for custom amount of threads
		if '-t' in argv:
			if not argv[argv.index('-t') + 1][0] == '-':
				num_of_threads = argv[argv.index('-t') + 1]
    

		#creates tk widgets based on number of threads
		for i in range(num_of_threads):
			progressbars_progress.append(IntVar(root))
			progressbars.append(ttk.Progressbar(root, variable = progressbars_progress[i]))
			progressbar_labels_text.append(StringVar(root, 'Doing Nothing...'))
			progressbar_labels.append(Label(root, textvariable=progressbar_labels_text[i]))

		#packs tk widgets into window
		for i in range(num_of_threads):
			progressbar_labels[i].pack()
			progressbars[i].pack()

		#runs download code
		thread = Thread(target=url_handler, args=(video_url,))
		thread.daemon = True
		thread.start()

		#gui window
		root.mainloop()
  
	except Exception as e:
		raise Exception(e)
		#input("press enter key to exit...")