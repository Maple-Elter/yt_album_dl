from genericpath import exists
from youtube_dl.utils import DownloadError
from youtubesearchpython.extras import Video
from youtubesearchpython import Playlist
import youtube_dl
from pyperclip import paste
from playsound import playsound
from os import path, remove
from ffmpeg_progress_yield import FfmpegProgress
from sys import argv
from threading import Thread, active_count

gui_text = ""

#max number of download threads
num_of_threads = 4

#if thread throws an error it gets logged here for thread_controller to use
thread_errors = [0] * num_of_threads

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
def split(arr: list, x: int) -> list:
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
		print(filename)
  
		#ffmpeg options
		cmd = ["ffmpeg", "-threads", f"{threads}", "-i", f"{filename}.webm", f"{filename}.mp3"]
  
		if not exists(f"{filename}.mp3"):
			ff = FfmpegProgress(cmd)
			for progress in ff.run_command_with_progress():
					print(f"Converting Song {current_index} of {len(list1)}      {progress}%", end='\r')
					#print(f'{filename}')
		else: print(f"File: {filename}.mp3 already exists")
		
		if exists(f"{filename}.webm"):
			#delete .webm file
			remove(f"{filename}.webm")

		current_index += 1
	print('                                                                   ', end='\r')
	print(f"successfully closed thread {thread_num}")

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
			print(f"Downloading Song {current_index} of {len(list1)}      {num}%", end='\r')


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
			video = Video.getInfo(list1[i])
			filename = clean_up_string(video['title'])
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
	while active_count() > 1:
		for i in range(len(thread_errors)):
			if thread_errors[i] == 1:
				print(f"thread {i} failed, restarting thread")
				k = Thread(target=download, args=(list1[i],i))
				k.daemon=True
				k.start()
				thread_errors[i] = 0
    
#main function
def url_handler(video_url):

	# 1 means Playlist while 2 means individual video
	url_type = 0


	#checks if url is a valid url
	if 'youtube.com' not in video_url and 'youtu.be' not in video_url or not video_url:
		print("Enter a valid song URL")
		input("press enter key to exit...")
		return

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

	#list of videos
	new_list = []
	list1 = []
 
	#defaults to 1 for single video
	video_count = 1


	#if playlist
	if url_type == 1:
    		#retrieves video count of playlist as int and saves it to video_count
		playlist = Playlist.getInfo(video_url)
		video_count = int(playlist['videoCount'])

		#gets urls of videos in playlist and saves to list
		videos = Playlist.getVideos(video_url)
		for i in range(video_count):
			try:
				new_list.append(videos['videos'][i]['link'])
			except IndexError:
				break
		list1 = split(new_list, num_of_threads)
  

	#if single video
	elif url_type == 2:
		list1.append(video_url)
  
	return list1
      
#downloads from file with list of urls
#empty
def bulk_file_handler(file_location):
    return
    
#GUI
#empty
def gui():
    return
 
#driver code
if __name__ == "__main__":
    
	try:
		
  
		'''
		#if program is run with -b option get urls from file for bulk downloads
		if '-b' in argv:
			if not argv[argv.index('-b') + 1][0] == '-':
				file_location = argv[argv.index('-b') + 1]
				if file_location:
					bulk_file_handler(file_location)
				else:
					print('Please enter a file location')
					input('Press Enter to exit...')
					exit
		'''

		#if program is run with -i option get url from command line rather than clipboard
		if '-i' in argv:
			if not argv[argv.index('-i') + 1][0] == '-':
				video_url = argv[argv.index('-i') + 1]
		else:
			#gets URL of playlist or video from user clipboard
			video_url = paste()

		#run url handler function
		thread_controller(url_handler(video_url))
  
		#play bell sound when finished
		playsound((path.dirname(__file__) + '\\extra\\bell.wav'))
  
	except:
		input("press enter key to exit...")