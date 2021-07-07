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
		'outtmpl': '%(title)s.%(ext)s',
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



if __name__ == "__main__":

	#main function
	def main():

		# 1 means Playlist while 2 means individual video
		url_type = 0

		#gets URL of playlist or video from user
		video_url = input("Enter video or playlist URL of song: ")

		#checks if url is a valid youtube playlist
		if not video_url or "youtube.com" not in video_url:
			print("Enter a valid youtube URL")


		#if url is video in playlist rather than playlist url itself, this converts it
		if 'list' in video_url:
			new_list = video_url.split('&')
			video_url = "https://www.youtube.com/playlist?" + new_list[1]

		#sets mode
		if 'playlist' in video_url:
			url_type = 1
		elif 'watch' in video_url:
			url_type = 2

		#list of videos
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
					list1.append(videos['videos'][i]['link'])
				except IndexError:
					break

		#if single video
		if url_type == 2:
			list1.append(video_url)

		#downloads the video(s)
		do_stuff(video_count, list1)




#run main function
main()
