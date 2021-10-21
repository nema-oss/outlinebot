import requests
from io import StringIO
from html.parser import HTMLParser
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def outline(update: Update, context: CallbackContext) -> None:
	link = update.message.text
	print("Received new request to outline ", link, " from ", update.message.from_user.username)
	name = "" #feel free to put whatever name you want for the author of the article
	starter = '[{"tag":"p", "children":["'
	end = '"]}]'
	print("Sending request to outline.com...")
	response = requests.get("https://api.outline.com/v3/parse_article?source_url="+link)
	print("Got a response! Cleaning contents...")
	body = response.json()['data']['html']
	print("Got the HTML body:\n", body)
	content=strip_tags(body)
	print("Stripping off tags...")
	content=content.replace(" ", "+")
	content=content.replace("\n", "+")
	content=content.replace('"', "'")
	while content[0]=="+":
		content=content[1:]
	print("Forming content...")
	content=starter+content+end
	print("New content acquired: ", content, "\nProceeding to create title...")
	title = response.json()['data']['meta']['title']
	print("New title acquired: ", title, "\nNow creating a Telegraph account...")
	createAcc = requests.get("https://api.telegra.ph/createAccount?short_name=OutlineBot&author_name=OutlineBot")
	tok = createAcc.json()['result']['access_token']
	print("Account created and token acquired: ", tok, "\nCreating Telegraph page...")
	createPage = requests.get("https://api.telegra.ph/createPage?access_token="+tok+"&title="+title+"&author_name="+name+"&content="+content+"&return_conent=true")
	if createPage.json()["ok"]==True:
		print("Successfully created a Telegraph page with url: ")
		URL = createPage.json()['result']['url']
		print(URL)
		update.message.reply_text(URL)
	else:
		print("Page creationg FAILED! Reason:", createPage.json()['error'])
		update.message.reply_text("Creation process failed! Reason: ", createPage.json()['error'])

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("") #your token goes here

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, outline))


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
