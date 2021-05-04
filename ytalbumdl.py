from youtubesearchpython import *
import youtube_dl

def do_stuff(video_count, list1):
	print("Downloading", video_count, "Songs")
	current_index = 0

	#progress hook
	def my_hook(d):
		if(d['status'] == 'downloading'):
			speed = d['speed']
			downloaded_percent = int((d['downloaded_bytes']*100)/d['total_bytes'])
			print("Downloading Song", current_index, "of", video_count, "		", downloaded_percent, "%", end='\r')



	#options for youtube_dl
	yld_opts = {
		'outtmpl': '%(track)s.%(ext)s',
		'quiet':True,
		'format' : 'bestaudio/best',
		'postprocessors' : [{
			'key' : 'FFmpegExtractAudio',
			'preferredcodec' : 'mp3',
			'preferredquality' : '192',
		}],
	
		'progress_hooks' : [my_hook],
	}

	#run youtube-dl
	ydl = youtube_dl.YoutubeDL(yld_opts)
	ydl._ies = [ydl.get_info_extractor('Youtube')]
	for i in range(len(list1)):
		current_index = i + 1
		ydl.download([list1[i]])
	print('Finished Downloading Songs') 




#main function
def main():


	#gets URL of playlist from user
	video_playlist = input("Enter an album URL: ")

	#checks if url is a valid youtube playlist
	if not video_playlist or "youtube.com" not in video_playlist or 'list' not in video_playlist:
		print("Enter a yotube playlist video URL")

	#if url is video in playlist rather than playlist url itself, this converts it
	if 'watch' in video_playlist:
		new_list = video_playlist.split('&')
		video_playlist = "https://www.youtube.com/playlist?" + new_list[1]

	#if is proper playlist url
	if 'playlist' in video_playlist:

		list1 = []
		#retrieves video count of playlist as int and saves it to video_count
		playlist = Playlist.getInfo(video_playlist)
		video_count = int(playlist['videoCount'])

		#gets urls of videos in playlist and saves to list
		video = Playlist.getVideos(video_playlist)
		for i in range(video_count):
			try:
				list1.append(video['videos'][i]['link'])
			except IndexError:
				break

		do_stuff(video_count, list1)




#run main function
main()
