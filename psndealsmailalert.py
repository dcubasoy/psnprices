#!/usr/bin/env python

from psnpricealert.psn import psn
from psnpricealert.utils import utils
import csv
import sys

if (sys.version_info[0] == 2):
	from email.MIMEMultipart import MIMEMultipart
	from email.MIMEBase import MIMEBase
	from email.MIMEText import MIMEText
else:
	from email.mime.multipart import MIMEMultipart
	from email.mime.base import MIMEBase
	from email.mime.text import MIMEText

import smtplib

def getMailConfig():
	mailConfig = {}
	mailConfig = utils.getJsonFile("mailconfig.json")
	return mailConfig

def getContainers(dealContainerAlertsFilename):
	containers = []
	with open(dealContainerAlertsFilename) as csvfile:
		containersReader = csv.reader(csvfile, delimiter=',', quotechar='"')
		for row in containersReader:
			container = {}
			container['containerId'] = row[0]
			container['store'] = row[1]
			containers.append(container)

	return containers


def checkContainersAndGenerateMailBody(containers):


	body = ""
	bodyElements = []

	for container in containers:
		containerId = container['containerId']
		store = container['store']

		items = psn.getItemsByContainer(containerId, store, {"platform": "ps4"})

		if (items == None):
			utils.print_enc("No items found for Container '"+containerId+"' in store "+store)
		else:

			body = """<html>
						<head>
							<style>
								div.container {
									width: 80%;
									margin: auto;
								}

								div.container .header {
									font-family: sans-serif;
									font-size: 1.0em;
									color: #E02E2E;
									background-color: #F0F3ED;
									padding: 10px;
								}

								div.item {
									float: left;
									padding: 10px;
									font-family: sans-serif;
									font-size: 0.8em;
									max-width: 250px;
								}
							</style>
						</head>
						<body>"""

			body = body + "<div class=\"container\"><p class=\"header\">Deals in Store " + store  + " for container " + container["containerId"] + "</p>"

			itemNum = 0
			for item in items:
				itemNum = itemNum + 1
				startNewRow = False

				if itemNum % 4 == 0:
					startNewRow = True

				bodyElements.append(generateBodyElement(container, item, startNewRow))

	body = body + "\n".join(bodyElements) + "</div>"
	body = body + "</body></html>"

	return body

def sendMail(body):

	mailConfig = getMailConfig()

	msg = MIMEMultipart('alternative')
	msg['From'] = mailConfig["from"]
	msg['To'] = mailConfig["to"]
	msg['Subject'] = "Playstation Network Deals"

	if (sys.version_info[0] == 2):
		sendBody = body.encode('utf-8')
	else:
		sendBody = body

	htmlMail = MIMEText(sendBody, 'html')
	msg.attach(htmlMail)

	mailServer = smtplib.SMTP(mailConfig["server"])
	mailServer.ehlo()
	mailServer.starttls()
	mailServer.ehlo()
	mailServer.login(mailConfig["username"],mailConfig["password"])
	mailServer.sendmail(mailConfig["from"], msg['To'], msg.as_string())

	mailServer.quit()


def generateBodyElement(container, item, startNewRow):

	returnBody = []

	startNewRowHtml = ""

	if startNewRow:
		startNewRowHtml = " style=\"clear: left;\""

	url = psn.getStoreUrl(item, container["store"])

	returnBody.append("<div class=\"item\"" + startNewRowHtml + ">")
	returnBody.append("<p><a href=\"" + url + "\" target=\"_new\"><img src='"+psn.getImage(item)+"'/></a></p>")
	returnBody.append("<p>"+psn.getName(item)+"</p>")
	returnBody.append("<p>Is now: "+str(psn.getPrice(item))+"</p>")
	returnBody.append("</div>")

	return "\n".join(returnBody)

def main():
	dealContainerAlertsFilename = "alert_deal_containers.csv"
	containers = getContainers(dealContainerAlertsFilename)

	body = checkContainersAndGenerateMailBody(containers)
	utils.print_enc("Finished processing")
	
	if (len(body) > 0):
		sendMail(body)
		utils.print_enc("Mail was sent")
	else:
		utils.print_enc("No mail was sent")
	
	exit(0)


if __name__ == "__main__":
    main()