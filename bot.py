#!/usr/bin/python3

"""
Reddit bot for transcribing news posts from Warthunder.com into comments

Written by /u/Harakou
"""

import praw, time, re
from urllib import request, error
from bs4 import BeautifulSoup
from requests import exceptions
from http.client import HTTPException
import socket
import traceback

#Begin config variables
username = "doyouevenliftwaffe"
useragent = "War Thunder News bot by /u/Harakou"
subreddit = "warthunder"
newsFlairID = "51e56bb2-15ba-11e3-8a1a-12313b04c5c2"
histFlairID = "173a5236-c982-11e2-a2c3-12313d17f99e"
specialFlairID = "154c23ca-9b21-11e3-9eea-12313d27e9a3"
newsRegex = r"http://[www\.]*warthunder\.com/en/news/.+"
imageRegex = r".*/upload/image/.*"
fullLinkRegex = r"http://.+"
newLineRegex = r"\n+"
updateRegex = r"Update [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
tagRegex = r"\[.*\]"
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
expandoMarkup = "#####&#009;\n\n######&#009;\n\n#####&#009;\n\nNews Post:\n\n---"
#End config variables

#Var overrides for testing account/subreddit
#username = "ponymotebot"
#subreddit = "harakouscssplayground"

#init
checked = []
failed = []
checkedNews = []
bot = praw.Reddit(user_agent = useragent)
bot.login(username)
subreddit = bot.get_subreddit(subreddit)
newsRegex = re.compile(newsRegex)
imageRegex = re.compile(imageRegex)
fullLinkRegex = re.compile(fullLinkRegex)
wallpaperRegex = re.compile(wallpaperRegex)
newLineRegex = re.compile(newLineRegex, re.M)
updateRegex = re.compile(updateRegex)
tagRegex = re.compile(tagRegex)
months = "(" + ")|(".join(months) + ")"
dateRegex = re.compile("(.*(" + months + ").*" + day + ")|(.*" + day + ".*(" + months + ".*))")

#Placeholder for actual post/news item ID logging. So horribly sloppy
skipOldPosts = (input("Skip existing Reddit posts? ") == "y")
skipOldNews = (input("Skip existing news? ") == "y")
if skipOldNews:
	newsPage = request.urlopen("http://warthunder.com/en/news/")
	newsPage = BeautifulSoup(newsPage)
	newsItems = newsPage.find_all(class_="news-item")
	for newsItem in newsItems:
		newsLink = newsItem.find('a')
		newsURL = newsLink['href']
		newsID = newsURL.split('/')[3].split('-')[0]
		checkedNews.append(newsID)
if skipOldPosts:
	posts = subreddit.get_new(limit = 10)
	for post in posts:
		if newsRegex.match(post.url):
			checked.append(post.id)
	 

def handleError(errorMessage, e, ID=-1):
	if ID not in failed:
		if not ID == -1:
			failed.append(ID)
		print(errorMessage)
		errorReport = "[](/paperbagderpy \"I just don't know what went wrong!\")" + errorMessage+ "\n\n" + str(e)
		bot.send_message(reportRecipient, 'Error Report', errorReport) 

def toRedditMarkdown(bsObj):
	for image in bsObj.find_all('img'):
		imgURL = image['src']
		imgURL = imgURL.replace("(", "\(")
		imgURL = imgURL.replace(")", "\)")
		if fullLinkRegex.match(image['src']):
			image.replace_with("[Image](" + imgURL + ")")
		else:
			image.replace_with("[Image](" + "http://warthunder.com" + imgURL + ")") #Converts image tags to Reddit links
	#add ul handling here
	for link in bsObj.select('a[href]'):
		if not imageRegex.match(link['href']) or wallpaperRegex.match(link.get_text()):
			linkURL = link['href']
			linkURL = linkURL.replace("(", "\(")
			linkURL = linkURL.replace(")", "\)")
			link.replace_with("[" + link.get_text() + "](" + linkURL + ")") #Converts HTML href tags to Reddit-style links
	for embed in bsObj.find_all('iframe'):
		ytID = re.split(r"/", embed['src'])[4]
		#It would probably be wise to actually make sure the embed link is a youtube link.
		embed.replace_with("[Embed](http://www.youtube.com/watch?v=" + ytID + ")")
	for text in bsObj.find_all('strong'):
		if dateRegex.match(text.get_text()):
			text.replace_with("[**" + text.get_text().strip() + "** ](http://www.worldtimebuddy.com/)")
		else:
			text.replace_with("**" + text.get_text().strip() + "** ")
	for text in bsObj.find_all('em'):
		text.replace_with("*" + text.get_text().strip() + "* ")

	bsObj = bsObj.get_text()
	bsObj = bsObj.replace("\t", "")
	bsObj = bsObj.replace("\r", "")
	bsObj = re.sub(newLineRegex, "\n\n>", bsObj)
	bsObj = expandoMarkup + bsObj + "\n\n---\n\n^(This is a bot. | )[^(Suggestions? Problems?)](http://www.reddit.com/message/compose/?to=Harakou)^( | )[^(This project on Github)](https://github.com/Harakou/WarThunderNewsBot/)"
	return bsObj

def transcribe(post):
	try:
		page = BeautifulSoup(request.urlopen(post.url))
		news = page.find('div', class_ = "news-item")

		news.find('table', class_ = "share").decompose()
		news = toRedditMarkdown(news)
		post.add_comment(news)
		checked.append(post.id)
		print("Commented on " + post.url)
	except error.URLError as err:
		handleError("Failed to fetch " + post.url + ", Reddit submission " + post.short_link, err, post.id)
	except socket.error as err:
		msg = "Failed to fetch news page."
		handleError(msg, err)
	except praw.errors.APIException as err:
		handleError("Reddit API error posting comment for " +  post.url + ", Reddit sumbmission " + post.short_link, err, post.id)

def main():
	while True:
		try:
			newsPage = request.urlopen("http://warthunder.com/en/news/")
			newsPage = BeautifulSoup(newsPage)
			newsItems = newsPage.find_all(class_="news-item")
			for newsItem in newsItems:
				newsLink = newsItem.find('a')
				if not updateRegex.match(newsLink.get_text()): #dealing with bug where "phantom" news links appeared that 404
					newsURL = newsLink['href']
					newsID = newsURL.split('/')[3].split('-')[0]
					if newsID not in checkedNews:
						try:
							print("attempting to submit something")
							if not fullLinkRegex.match(newsURL):
								newsURL = "http://warthunder.com" + newsURL
							subTitle = newsLink.get_text()
							tag = tagRegex.match(subTitle) 
							flair = newsFlairID
							if tag:
								if subTitle[tag.span()[0]:tag.span()[1]] in ["[Historical]", "[Commemoration]"]:
									subTitle = subTitle[tag.end():subTitle.__len__()]
									flair = histFlairID
								if subTitle[tag.span()[0]:tag.span()[1]] == "[Special]":
									subTitle = subTitle[tag.end():subTitle.__len__()]
									flair = specialFlairID 
									
							submission = subreddit.submit(title=subTitle, url=newsURL)
							bot.select_flair(item=submission, flair_template_id=flair)
							checkedNews.append(newsID)
							print("Submitted " + newsURL + " to " + subreddit.display_name)
							transcribe(submission)
						except praw.errors.AlreadySubmitted:
							print(newsURL + " has already been submitted.")
							checkedNews.append(newsID)
						except praw.errors.APIException as err:
							msg = "Error submitting " + newsURL + ". Is Reddit down?" 
							handleError(msg, err, newsID)
			
		except error.URLError as err:
			msg = "Failed to fetch news page."
			handleError(msg, err)
		except socket.error as err:
			msg = "Failed to fetch news page."
			handleError(msg, err)
		except HTTPException as err:
			msg = "Failed to fetch news page."
			handleError(msg, err)
		
		try:
			posts = subreddit.get_new(limit = 10)
			for post in posts: #why did this throw a timeout exception mutliple times? good question! The world may never know.
				if newsRegex.match(post.url) and post.id not in checked:
					transcribe(post)
		except exceptions.HTTPError:
			print("Fetching new posts failed. Is Reddit under heavy load?")
		except TimeoutError as err:
			handleError("Something timed out.", err)	

		time.sleep(120)

#This is important. It makes the program run.
try:
	main()
except Exception as err:
	handleError("Something unexpected went wrong. " + traceback.format_exc(), err)
########################
