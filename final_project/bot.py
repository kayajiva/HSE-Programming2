import telebot
from telebot import apihelper
import conf
import versemorpher
import re

apihelper.proxy = {'https': 'socks5h://geek:socks@t.geekclass.ru:7777'} #задаем прокси
bot = telebot.TeleBot(conf.TOKEN)  # создаем экземпляр бота

reWord = re.compile(r'[^\W\d_]+',flags=re.UNICODE)
hokkus = versemorpher.VerseCorpa('bashuo.txt','hokku-schemes.txt')
#hokkus = versemorpher.VerseCorpa('perashki.txt','perashki-schemes.txt')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Здравствуйте! Введите слово, чтобы составить хокку с ним")
    
@bot.message_handler(func=lambda m: True)  # этот обработчик реагирует на любое сообщение
def send_verse(message):
    match = re.match(reWord, message.text)
    if not match:
        bot.send_message(message.chat.id, 'Что-то не вижу слов в вашем сообщении. Введите что-нибудь по-русски')
        return
    
    w = match[0]
    w_m = versemorpher.word2model(w)
    if w_m is None or w_m not in versemorpher.model :
        bot.send_message(message.chat.id, 'Ваше слово %s... Кажется, его нет в моей базе. Введите что-нибудь попроще. Я принимаю существительные, прилагательные, глаголы' % w)
        return
    
    bot.send_message(message.chat.id, 'Хорошо, сейчас попробую сочинить что-нибудь со словом "%s"' % w)
    res = hokkus.morphRandomHokku(w, 20)
    
    if res is None :
        bot.send_message(message.chat.id, 'Трудновата задачка... Попытаюсь ещё')
        res = hokkus.morphRandomHokku(w, 50)
        
    if res is None :
        bot.send_message(message.chat.id, 'Кажется, тут я бессилен. Попробуйте другое слово')
        return
        
    bot.send_message(message.chat.id, res)
    bot.send_message(message.chat.id, 'Я конечно не Басё... Но как вам?')

if __name__ == '__main__':
    bot.polling(none_stop=True)