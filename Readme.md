
![Logo](https://github.com/kachaMukabe/TheRook/blob/main/images/25643.jpg)


# The Rook

The Rook a safety bot that sits and watches your whatsapp customer chats. It ensures that all links and files coming into your support team are scanned and safe. 


## Demo

![Demo](https://github.com/kachaMukabe/TheRook/blob/main/images/output.gif)


## Features

- Watch chats and scan for URLs sent, it will highlight any unsafe or malicious URLS
- It will watch chats for any files that have been submitted and scan it for any unsafe materials
- It will redact any sensitive information like card numbers from the chat


## Roadmap

I have a few things I would like to fix up for the rook first and foremost is the file scan which is partially working at the moment.

More things on the roadmap are:

- [ ] A deployment guideline for how to set up the bot
- [ ] Setting up a database in order to keep message sessions
- [ ] Handle the whatsapp message statuses


## Lessons Learned

I learned the following things:
- I learned how to use the Whatsapp cloud API, set up a test number and was able to process received messages
- I learned about Pangea services and how to integrate them into my python application
- I relearned Fastapi and pydantic models


## License

[MIT](https://choosealicense.com/licenses/mit/)

