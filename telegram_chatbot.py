import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler  
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from model.inference import load_model, run_mrc, run_reader
import time
from model.elastic_setting import *


model, tokenizer = load_model()
setting_path = "./model/setting.json"
es, user_index = es_setting("origin-meeting-wiki")
answer_set = {}
passage_set = {}
doc_set = {}
user_index = 'user'
is_fixxed = False


button1 = InlineKeyboardButton(text = '본문 보여줘📖', callback_data='본문 보기')
button2 = InlineKeyboardButton(text = '다른 답 보여줘➡️', callback_data='다른 답 보기')
button3 = InlineKeyboardButton(text = '여기서 더 질문🔎', callback_data='회의록 추가 질문하기')
button4 = InlineKeyboardButton(text = '새로운 질문 할래🧑🏻‍💻', callback_data='새로운 질문하기')
button5 = InlineKeyboardButton(text = '시작하기🔎', callback_data='시작하기')




def query(update, context):
    global now_state
    global text
    global doc_set
    global is_fixxed
    global button1
    global button2
    global button3
    global button4
    global button5
    question = update.message.text
    if question == '/start':
        mu = InlineKeyboardMarkup(inline_keyboard = [[button5]])
        update.message.reply_text(text = '시작하려면 아래 버튼을 눌러주세요', reply_markup=mu)
        pass

    mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button2, button3],[button4]])
    if is_fixxed:
        answer = run_reader(None, None, None, None, tokenizer, model, passage_set[now_state], doc_set[now_state],question)
        mu = InlineKeyboardMarkup(inline_keyboard = [[button3,button4]])
        update.message.reply_text(text = answer[0]['text'], reply_markup=mu)
        is_fixxed=False
    else:
        now_state = 0
        answer = run_mrc(None, None, None, None, tokenizer, model, question) #user_index 넣어줘야함
        # print(answer)
        if answer[0][0]['text'] != '여기서는 답을 못찾겠어..':
            update.message.reply_text(text = answer[0][0]['text'], reply_markup=mu)
            for idx, i in enumerate(answer):
                answer_set[idx] = i[0]['text']
                doc_set[idx] = i[2]
                passage_set[idx] = i[1]
        else: 
            mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button3, button4]])
            update.message.reply_text(text = '답이 존재하지 않아요 새로운 질문을 해주세요😭', reply_markup=mu)




def callback_get(update, context):
    global now_state
    global is_fixxed
    global button1
    global button2
    global button3
    global button4
    command = update.callback_query.data
    print(context)
    if command == '본문 보기':
        mu = InlineKeyboardMarkup(inline_keyboard = [[button2, button3, button4]])
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '넵 회의록을 보여드릴게요!')
        text = passage_set[now_state]
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = text, reply_markup=mu)
    elif command == '다른 답 보기':
        if now_state +1 == 1:
            print('2번째 답')
            now_state += 1
            answer = answer_set[now_state] 
            context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
            if answer != '여기서는 답을 못찾겠어..':
                mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button2, button3],[button4]])
                context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = answer, reply_markup = mu)
            else: 
                mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button2, button3],[button4]])
                context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '답이 존재하지 않아요 새로운 질문을 해주세요😭', reply_markup = mu)
        elif now_state + 1 == 2:
            print('3번째 답')
            now_state += 1
            answer = answer_set[now_state]
            context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
            if answer != '여기서는 답을 못찾겠어..':
                context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = answer)
                mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button3, button4]])
                context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = answer, reply_markup = mu)
            else: 
                mu = InlineKeyboardMarkup(inline_keyboard = [[button1, button2, button3],[button4]])
                context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '답이 존재하지 않아요 새로운 질문을 해주세요😭', reply_markup = mu)
    elif command == '회의록 추가 질문하기':
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = f"넵 관련한 추가 질문해주세요!👀" )
        is_fixxed = True
    elif command == '새로운 질문하기':
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '넵 궁금한걸 물어봐주세요😎')
    elif command == '시작하기':
        context.bot.editMessageReplyMarkup(chat_id=update.callback_query.message.chat_id,  message_id=update.callback_query.message.message_id, reply_markup=None)
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = f'회의록과 관련된 무엇이든 물어보세요!🤓')
        context.bot.sendMessage(chat_id=update.callback_query.message.chat_id, text = '회의록을 추가로 업로드하고 싶다면 첨부파일로 저한테 보내주세요!😉')
        print(update.callback_query.message.chat_id, '시작됨')
    


def download(update, context):
    global now_state
    global es 
    global user_index

    file = context.bot.get_file(update.message.document.file_id)
    downloaded_file = file.download(update.message.document.file_name)
    
    # with open('/opt/ml/final-project-level3-nlp-09/완주군 207회 회의록.txt' ,'r') as f:
    #     corpus = f.readlines()
    
    with open('./' + downloaded_file ,'r') as f:
        new_text = f.readlines()

    # print(corpus)
    new_text = preprocess(new_text[0])
    text = [ new_text ]
    text = [ {"document_text": text[i]} for i in range(len(text)) ]
    file_name = update.message.document.file_name.split('.')[0]
    es.index(index=user_index, id=file_name, body=text[0])
    update.message.reply_text( text = f'{file_name}를 업로드 했어요🥳')



if __name__ == "__main__":
    #settings for bot
    print('If you want to start, you need token for telegram chatbot')
    token =  # insert token for chatbot
    bot = telegram.Bot(token) 
    # chat_id =  # token for chat for specific user # you can insert your chat_id #bot.getUpdates()[-1].message.chat.id

    # set elasticsearch for specific user
    # es, user_index = es_setting("origin-meeting-wiki")

    print('your chat id:',chat_id)

    # start message
    # bot.sendMessage(chat_id = chat_id, text = '회의록과 관련된 무엇이든 물어보세요!🤓')
    # bot.sendMessage(chat_id = chat_id, text = '회의록을 추가로 업로드하고 싶다면 첨부파일로 저한테 보내주세요!😉')

    # make handler
    updater = Updater(token)
    updater.dispatcher.add_handler(MessageHandler(Filters.text, query))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_get))
    updater.dispatcher.add_handler(MessageHandler(Filters.document, download, pass_user_data=True))

    # start updater
    updater.start_polling()
    updater.idle()
