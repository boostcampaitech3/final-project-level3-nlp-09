from tkinter import Button
from turtle import up
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler  
import telepot.namedtuple as BT
import telepot.namedtuple as MU
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# token = '5572204836:AAFC4bw49D8sUs6nS2uw8FhdFksCeHIE4kU'
# my_bot = telegram.Bot(token)

def query(update, context):
    question = update.message.text
    button1 = InlineKeyboardButton(text = '본문 보여줘📖', callback_data='본문 보기')
    button2 = InlineKeyboardButton(text = '다른 답 보여줘➡️', callback_data='다른 답 보기')
    button3 = InlineKeyboardButton(text = '여기서 더 질문🔎', callback_data='회의록 추가 질문하기')
    button4 = InlineKeyboardButton(text = '새로운 질문 할래🧑🏻‍💻', callback_data='새로운 질문하기')
    mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button2, button3],[button4]])
    update.message.reply_text(text = question, reply_markup=mu)
    # bot.sendMessage(chat_id = 5402236099, text = question, reply_markup=mu)

def callback_get(update, context):
    command = update.callback_query.data
    print(context)
    if command == '본문 보기':
        button3 = InlineKeyboardButton(text = '여기서 더 질문🔎', callback_data='회의록 추가 질문하기')
        button4 = InlineKeyboardButton(text = '새로운 질문 할래🧑🏻‍💻', callback_data='새로운 질문하기')
        mu = InlineKeyboardMarkup(inline_keyboard = [[button3, button4]])
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '회의록 본문 전문 표시', reply_markup=mu)
    elif command == '다른 답 보기':
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = f'{command} 기능을 준비중입니다')
    elif command == '회의록 추가 질문하기':
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = f'{command} 기능을 준비중입니다')
    elif command == '새로운 질문하기':
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '넵 궁금한걸 물어봐주세요😎')

def download(update, context):
    file = context.bot.get_file(update.message.document.file_id)
    file.download(update.message.document.file_name)
    update.message.reply_text( text = '회의록을 업로드 했어요🥳')


if __name__ == "__main__":
    token = '5572204836:AAFC4bw49D8sUs6nS2uw8FhdFksCeHIE4kU'
    bot = telegram.Bot(token)
    chat_id = 5402236099 #bot.getUpdates()[-1].message.chat.id
    print('your chat id:',chat_id)

    # start message
    bot.sendMessage(chat_id = chat_id, text = '회의록과 관련된 무엇이든 물어보세요!🤓')

    # make handler
    updater = Updater(token)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, query))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_get))
    updater.dispatcher.add_handler(MessageHandler(Filters.document, download, pass_user_data=True))


    updater.start_polling()
    updater.idle()

    

# class TelegramBot:

#     def __init__(self):
#         self.id = 5402236099
#         self.token = '5572204836:AAFC4bw49D8sUs6nS2uw8FhdFksCeHIE4kU'
#         self.core = telegram.Bot(self.token)
#         self.updater = Updater(self.token)

#     def start(self):
#         self.sendMessage('회의록과 관련된 무엇이든 물어보세요!')
#         self.updater.start_polling()
#         self.updater.idle()

#     def sendMessage(self, text):
#         btn1 = InlineKeyboardButton(text='회의 원문 보여줘', callback_data='1')
#         btn2 = InlineKeyboardButton(text='다른 답 알려줘', callback_data='2')
#         mu = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])
#         self.core.sendMessage(chat_id=(self.id), text=text, reply_markup=mu)

#     def add_handler(self, cmd, func):
#         self.updater.dispatcher.add_handler(CommandHandler(cmd, func))

#     def stop(self):
#         self.updater.start_polling()
#         self.updater.dispatcher.stop()
#         self.updater.job_queue.stop()
#         self.updater.stop()