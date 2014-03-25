#!/usr/bin/python3

"""
Reddit bot for transcribing news posts from Warthunder.com into comments

Written by /u/Harakou
"""

import praw
import time
import re
from urllib import request, error
from bs4 import BeautifulSoup
from requests import exceptions

#Begin config variables
username = "doyouevenliftwaffe"
useragent = "War Thunder News bot by /u/Harakou"
subreddit = "warthunder"
newsRegex = r"http://[www\.]*warthunder\.com/en/news/.+"
imageRegex = r".*/upload/image/.*"
fullLinkRegex = r"http://.+"
reportRecipient = 'Harakou' #Username to which error reports should be sent
wallpaperRegex = r"[0-9]+x[0-9]+"
#End config variables

#init
checked = []
failed = []
bot = praw.Reddit(user_agent = useragent)
bot.login(username)
subreddit = bot.get_subreddit(subreddit)
newsRegex = re.compile(newsRegex)
imageRegex = re.compile(imageRegex)
fullLinkRegex = re.compile(fullLinkRegex)
wallpaperRegex = re.compile(wallpaperRegex)


def handleError(postID, errorMessage):
	if postID not in failed:
		print(errorMessage)
		failed.append(postID)
		errorReport = "[](/paperbagderpy \"I just don't know what went wrong!\")" + errorMessage
#		bot.send_message(reportRecipient, 'Error Report', errorReport) #Disabled until bot accumulates enough karma to avoid captcha

#Main loop'
while True:
	try:
		posts = subreddit.get_new(limit = 10)
	except exceptions.HTTPError:
		print("Fetching new posts failed. Is Reddit under heavy load?")
	for post in posts: #should be ok that this isn't in the try/catch block.
		if newsRegex.match(post.url) and post.id not in checked:
			try:
				page = BeautifulSoup(request.urlopen(post.url))
				news = page.find('div', class_ = "news-item")

				news.find('table', class_ = "share").decompose()
				for image in news.find_all('img'):
					if fullLinkRegex.match(image['src']):
						image.replace_with("[Image](" + image['src'] + ")")
					else:
						image.replace_with("[Image](" + "http://warthunder.com" + image['src'] + ")") #Converts image tags to Reddit links
				for link in news.select('a[href]'):
					if not imageRegex.match(link['href']) or wallpaperRegex.match(link.get_text()):
						link.replace_with("[" + link.get_text() + "](" + link['href'] + ")") #Converts HTML href tags to Reddit-style links
				for embed in news.find_all('iframe'):
					ytID = re.split(r"\W*", embed['src'])[5]
					embed.replace_with("[Embed](http://www.youtube.com/watch/" + ytID + ")")
				for text in news.find_all('strong'):
					text.replace_with("**" + text.get_text().strip() + "**")
				for text in news.find_all('em'):
					text.replace_with("*" + text.get_text().strip() + "*") #Using strip() here occassionally results in some awkward spaceless text, but it makes sure that there are no trailing spaces that keep the bold marks from applying.

				news = news.get_text()
				news = news.replace("\t", "")
				news = news + "---\n\n^(This is a bot. | )[^(Suggestions? Problems?)](http://www.reddit.com/message/compose/?to=Harakou)^( | Source code will be on GitHub soon^TM)"
				post.add_comment(news)
				checked.append(post.id)
				print("Success for " + post.url)
			except error.HTTPError:
				handleError(post.id, "Failed to fetch " + post.url + ", Reddit submission " + post.short_link)
			except praw.errors.APIException:
				handleError(post.id, "Reddit API error posting comment for " +  post.url + ", Reddit sumbmission " + post.short_link)
	time.sleep(120)
