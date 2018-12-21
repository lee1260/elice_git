# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxp-506652758256-506748910048-506795381680-666516933b35e1c9fd68bb956048b03d"
slack_client_id = "506652758256.508932486294"
slack_client_secret = "38cd593ab527c66989be390a84c49821"
slack_verification = "8gJi9KbuCxIIOoEpeQsFmW5Q"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):


#여기에 함수를 구현해봅시다.
#url = re.search(r'(https?://\S+)', text.split('|')[0]).group(0)
    url = 'https://music.bugs.co.kr/chart'
    req = urllib.request.Request(url)

    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    titles = []
    keywords=[]
    artists =[]

    if "랭킹" in text:
       for i, keyword in enumerate(soup.find_all("div", class_="ranking")):
           if i < 10:
               keywords.append(keyword.find("strong").get_text().strip())

       for i, title in enumerate(soup.find_all("p", class_="title")):
           if i < 10:
               titles.append(title.get_text().strip())

       for i, artist in enumerate(soup.find_all("p", class_="artist")):
           if i < 10:
               artists.append(artist.get_text().strip())

       print(keywords)
       for i in range(10):
           keywords[i]=str(keywords[i])+"위: "+titles[i]+" / "+artists[i]

       # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
       return u'\n'.join(keywords)
# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
  print(slack_event["event"])

  if event_type == "app_mention":
      channel = slack_event["event"]["channel"]
      text = slack_event["event"]["text"]

      keywords = _crawl_naver_keywords(text)
      sc.api_call(
          "chat.postMessage",
          channel=channel,
          text=keywords
      )

      return make_response("App mention message has been sent", 200,)

  # ============= Event Type Not Found! ============= #
  # If the event_type does not have a handler
  message = "You have not added an event handler for the %s" % event_type
  # Return a helpful error message
  return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
  slack_event = json.loads(request.data)

  if "challenge" in slack_event:
      return make_response(slack_event["challenge"], 200, {"content_type":
                                                           "application/json"
                                                          })

  if slack_verification != slack_event.get("token"):
      message = "Invalid Slack verification token: %s" % (slack_event["token"])
      make_response(message, 403, {"X-Slack-No-Retry": 1})

  if "event" in slack_event:
      event_type = slack_event["event"]["type"]
      return _event_handler(event_type, slack_event)

  # If our bot hears things that are not events we've subscribed to,
  # send a quirky but helpful error response
  return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                       you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
  return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
  app.run('0.0.0.0', port=8080)