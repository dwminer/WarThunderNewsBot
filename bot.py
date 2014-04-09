#!/usr/bin/python3

"""
Reddit bot for transcribing news posts from Warthunder.com into comments

Written by /u/Harakou
"""

import praw, time, re
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
newLineRegex = r"\n+"
reportRecipient = 'Harakou' #Username to which error reports should be sent
wallpaperRegex = r"[0-9]+x[0-9]+"
day = r"[0-9]{1,2}(st|nd|rd|th)"
months = [
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December"]
hoverViewStuff = "#####&#009;\n\n######&#009;\n\n#####&#009;\n\nNews Post:\n\n---"
#End config variables

#Var overrides for testing account/subreddit
#username = "ponymotebot"
#subreddit = "harakouscssplayground"

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
newLineRegex = re.compile(newLineRegex, re.M)
months = "(" + ")|(".join(months) + ")"
dateRegex = re.compile("(.*(" + months + ").*" + day + ")|(.*" + day + ".*(" + months + ".*))")


def handleError(postID, errorMessage, err):
	if postID not in failed:
		print(errorMessage)
		failed.append(postID)
		errorReport = "[](/paperbagderpy \"I just don't know what went wrong!\")" + errorMessage+ "\n\n" + str(err)
		bot.send_message(reportRecipient, 'Error Report', errorReport) 

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
					embed.replace_with("[Embed](http://www.youtube.com/watch?v=" + ytID + ")")
				for text in news.find_all('strong'):
					if dateRegex.match(text.get_text()):
						text.replace_with("[**" + text.get_text().strip() + "** ](http://www.worldtimebuddy.com/)")
					else:
						text.replace_with("**" + text.get_text().strip() + "** ")
				for text in news.find_all('em'):
					text.replace_with("* " + text.get_text().strip() + "*")

				news = news.get_text()
				news = news.replace("\t", "")
				news = news.replace("\r", "")
				news = re.sub(newLineRegex, "\n\n>", news)
				news = hoverViewStuff + news + "---\n\n^(This is a bot. | )[^(Suggestions? Problems?)](http://www.reddit.com/message/compose/?to=Harakou)^( | )[^(This project on Github)](https://github.com/Harakou/WarThunderNewsBot/)"
				post.add_comment(news)
				checked.append(post.id)
				print("Success for " + post.url)
			except error.HTTPError as err:
				handleError(post.id, "Failed to fetch " + post.url + ", Reddit submission " + post.short_link, err)
			except praw.errors.APIException as err:
				handleError(post.id, "Reddit API error posting comment for " +  post.url + ", Reddit sumbmission " + post.short_link, err)
	time.sleep(120)
