#!/usr/bin/python3
import discord
import re
import unicodedata
#import pytesseract
#import os
#import urllib.request

uwuRegex = re.compile('\\b[uo0][^a-z]*[w][^a-z]*[uo0]\\b', re.IGNORECASE)

async def DoesMessageContainUWU(message):
    normalisedString = unicodedata.normalize('NFD', message.content)
    if uwuRegex.search(normalisedString):
        return True

    """
    for embed in message.embeds:
        if embed.thumbnail is None:
            continue

            async with message.channel.typing():
            processingImageName = 'local_image_{0}.jpg'.format(message.id)
            urllib.request.urlretrieve(embed.thumbnail.url, processingImageName)

            imageString = pytesseract.image_to_string(processingImageName, config="uwu --psm 3")
            os.remove(processingImageName)
            imageString = unicodedata.normalize('NFD', imageString)
            print("Image text: {0}".format(imageString))

            if uwuRegex.match(imageString):
                return True
    """
    return False