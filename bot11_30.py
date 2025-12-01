import json

import requests
from module11_30 import send_welcome, handle_start_button, send_link
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telebot.apihelper import ApiException
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv, find_dotenv
import os
from urllib.parse import urlparse
import time

load_dotenv()
API_key = os.getenv("API_KOD")
bot_username = os.getenv("BOT_USERNAME")

bot = telebot.TeleBot(API_key)

from psycopg2 import pool

DATABASE_URL = os.getenv("DATABASE_URL")

db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,  # adjust as needed
    dbname="neondb",
    user="neondb_owner",
    password="npg_w3XGEKmna6hv",
    host="ep-rapid-silence-aghzq02a-pooler.c-2.eu-central-1.aws.neon.tech",
    port="5432",
    sslmode="require"
)





def get_connection():
    return db_pool.getconn()


def release_connection(conn):
    db_pool.putconn(conn)


bmd = "CAACAgIAAxkBAAIBlmdxZi6sK42VCA3-ogaIn30MXGrmAAJnIAACKVtpSNxijIXcPOrMNgQ"

holatbot = True



import threading
def keep_connection_alive():
    while True:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")  # Simple query to keep DB alive
            cursor.close()
            release_connection(conn)
        except Exception as e:
            print(f"Keep-alive error: {e}")
        time.sleep(250)  # Run every 5 minutes


# Run keep-alive in a background thread
threading.Thread(target=keep_connection_alive, daemon=True).start()


def create_all_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        id SERIAL PRIMARY KEY,
                        channel_name TEXT,
                        channel_url TEXT,
                        num_channel INTEGER,
                        now_channel INTEGER

                    );
                ''')
    conn.commit()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blockers (
                        id SERIAL PRIMARY KEY,
                        number_blok INTEGER
                    );
                ''')
    conn.commit()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id SERIAL PRIMARY KEY,
                        file_kod INTEGER,
                        file_id TEXT,
                        file_name TEXT,
                        file_type TEXT,
                        timestamp REAL

                    );
                ''')
    conn.commit()



    cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT
                );
                """)
    conn.commit()

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT
                );
                """)
    conn.commit()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS kon_users (id SERIAL PRIMARY KEY, user_id BIGINT UNIQUE NOT NULL, referrals INTEGER);""")
    conn.commit()

    cursor.execute("""
                CREATE TABLE IF NOT EXISTS gifts (
                    id SERIAL PRIMARY KEY,
                    gift_name TEXT,
                    contest_status BOOLEAN
                );
                """)
    conn.commit()
    cursor.close()
    release_connection(conn)


create_all_database()


def save_file(file_kod, file_id, file_name, file_type):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
                INSERT INTO files (file_kod, file_id, file_name, file_type,timestamp)
                VALUES (%s,%s ,%s ,%s, %s)
            ''', (file_kod, file_id, file_name, file_type, time.time()))
        conn.commit()

    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)


# Get file metadata from the database
def get_file(file_kod):
    file = 0
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT  file_id, file_name, file_type FROM files WHERE file_kod = %s', (file_kod,))
        file = cursor.fetchall()

    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return file





def get_ani_kod(name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT  id,file_kod,file_name  FROM files;')
        fil = cursor.fetchall()
        l_a = []
        k = []
        for x in fil:
            if name in x[2].lower() and x[1] not in k:
                l_a.append(x)
                k.append(x[1])
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return l_a


def get_last_kod():
    conn = get_connection()
    cursor = conn.cursor()
    kod = 0
    try:
        cursor.execute('SELECT  file_kod  FROM files;')
        kod = max(cursor.fetchall())[0]
    except Exception as e:
        print(f"Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)

    return kod


def show_anime_list():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT  file_kod, file_name  FROM files;')
        names = cursor.fetchall()
        ls = ["Animelar Ro'yhati"]
        lr = []
        for x in names:
            if x not in lr:
                lr.append(x)
                ls.append(f"{x[0]}:  {x[1].split("\n")[0]}\n")
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return ls





def log_admin(user_id, username, first_name, last_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
                            INSERT INTO admins (user_id, username, first_name, last_name)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (user_id) DO UPDATE
                            SET username = EXCLUDED.username,
                                first_name = EXCLUDED.first_name,
                                last_name = EXCLUDED.last_name;
                        ''', (user_id, username, first_name, last_name))
        conn.commit()
    except Error as e:
        print("Error logging admin:", e)
    finally:
        cursor.close()
        release_connection(conn)


# Count total users
def count_users():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0]
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return count


# Keyboards-------------------------

def get_control_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_st = types.KeyboardButton('📊Statistika')
    item_xy = types.KeyboardButton("📃Xabar yuborish")
    item_pt = types.KeyboardButton("📬Post tayyorlash")
    item_kn = types.KeyboardButton("🎁Ko'nkurs")
    item_as = types.KeyboardButton("🎥Anime sozlash")
    item_mn = types.KeyboardButton("📥Text post")
    item_kl = types.KeyboardButton("📢Kanallar")
    item_ad = types.KeyboardButton("📋Adminlar")
    item_bh = types.KeyboardButton("🤖Bot holati")
    item_bc = types.KeyboardButton("◀️Orqaga")

    markup.row(item_st, item_xy)
    markup.row(item_pt, item_kn)
    markup.row(item_as, item_mn, item_kl)
    markup.row(item_ad, item_bh)
    markup.row(item_bc)
    return markup


def main_keyboard(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_ai = types.KeyboardButton('🔎Anime izlash')
    item_kn = types.KeyboardButton("🎁Konkurs")
    item_rk = types.KeyboardButton("💵Reklama va Homiylik")
    markup.row(item_ai)
    markup.row(item_kn, item_rk)
    if is_admin(message.chat.id):
        item_bh = types.KeyboardButton(text="🛂Boshqaruv")
        markup.row(item_bh)
    return markup


def search_keyboard():
    tip_board = InlineKeyboardMarkup()
    butname = InlineKeyboardButton(text="🏷Nom orqali izlash", switch_inline_query_current_chat="")
    butkod = InlineKeyboardButton(text="📌Kod orqali izlash", callback_data="search_kod")
    butjanr = InlineKeyboardButton(text="💬Janr orqali qidirish", callback_data="search_genre")
    butlate = InlineKeyboardButton(text="⏱️So'nngi qo'shilganlar", callback_data="search_latest")
    butxit = InlineKeyboardButton(text="👁Eng ko'p ko'rilganlar", callback_data="search_xit")
    butlist = InlineKeyboardButton(text="📚Animelar ro'yhati", callback_data="show_list")
    tip_board.add(butname, butlate)
    tip_board.add(butjanr)
    tip_board.add(butkod, butxit)
    tip_board.add(butlist)
    return tip_board


def get_contest_keyboard():
    contest_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_yq = types.KeyboardButton('🎁Yutuqlar')
    item_qa = types.KeyboardButton("📃Qoidalar")
    item_de = types.KeyboardButton("⛔️To'xtatish")
    item_st = types.KeyboardButton("🧩Boshlash")
    item_bc = types.KeyboardButton("◀️Orqaga")

    contest_keyboard.row(item_yq, item_qa)
    contest_keyboard.row(item_st, item_de)
    contest_keyboard.row(item_bc)
    return contest_keyboard


def is_admin(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM admins;")
        ids_of_admin = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)


    if user_id == 6945876603:
        return True


    for x in ids_of_admin:
        if user_id == x[0]:
            return True
    return False


# checking Inchannel----------------------------
channel_id = "@neon_katanas"


def check_user_in_channel(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT channel_name,channel_url FROM channels;")
        ll = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    bo = len(ll)
    keyboard = InlineKeyboardMarkup()
    for c in ll:
        s: str = c[1]
        url1: str = f"@{s[13:]}"
        member = bot.get_chat_member(chat_id=url1, user_id=message.chat.id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard.add(InlineKeyboardButton(text=c[0], url=c[1]))
        else:
            bo -= 1

    if bo > 0:
        start_button = InlineKeyboardButton("✅Tekshirish", callback_data="send_start")
        keyboard.add(start_button)

        bot.send_message(message.chat.id,
                         f"Assalomu alaykum \nAgar bizning xizmatlarimizdan foydalanmoqchi bo'lsangiz, Iltimos pastdagi kanallarga obuna bo'ling!",
                         reply_markup=keyboard)
        bot.send_sticker(message.chat.id, sticker=bmd)
        return False
    else:
        return True


# Starts bot--------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("send_start:"))
def a2(call):
    knlar = call.data.split(":")[1]
    knlar = knlar.split(",")
    knlar = [int(element) for element in knlar]
    print(knlar)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    handle_start_button(call, knlar)
    send_welcome(call.message)


@bot.message_handler(commands=['start'])
def a1(message):
    send_welcome(message)


# Anime Izlash ko'di--------------------------------------------------------

def say_sorry(message):
    bot.send_message(message.chat.id, "Uzr, bu xizmat vaqtinchalik ishlamayapti !")


@bot.callback_query_handler(func=lambda call: call.data == "search_kod")
def handle_kod_button(call):
    bot.answer_callback_query(call.id, "🔎Kod orqali qidirish boshlandi.\nAnime kodini kiriting...")


@bot.callback_query_handler(func=lambda call: call.data == "search_genre")
def handle_genre_button(call):
    bot.answer_callback_query(call.id, "🔎Janr orqali qidirish boshlandi.\nAnime janrini kiriting...")
    say_sorry(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "search_latest")
def handle_late_button(call):
    bot.answer_callback_query(call.id, "Sending /Anime list...")
    roy: list = show_anime_list()
    roy.reverse()
    m = ""
    k = 0
    for i in roy:
        m +="🆔" + i + "\n"
        k += 1
        if k == 6:
            break
    bot.send_message(call.message.chat.id, m)


@bot.callback_query_handler(func=lambda call: call.data == "search_xit")
def handle_xit_button(call):
    bot.answer_callback_query(call.id, "Sending /Anime list...")
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        m += "🆔" + i + "\n"
        k += 1
        if k == 6:
            break
    bot.send_message(call.message.chat.id, m)


@bot.callback_query_handler(func=lambda call: call.data == "show_list")
def handle_list_button(call):
    bot.answer_callback_query(call.id, "Sending /Anime list...")
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(call.message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")

    m += "Ko'rmoqchi bo'lgan anime kodini kiriting !"
    bot.send_message(call.message.chat.id, m)


@bot.message_handler(func=lambda message: message.text == "🔎Anime izlash" and holatbot)
def relpy_search(message):
    if check_user_in_channel(message):
        bot.send_message(message.chat.id, "🔍Qidiruv tipini tanlang:", reply_markup=search_keyboard())




# 💵Reklama va Homiylik--------------------------------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "💵Reklama va Homiylik")
def show_admin(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM admins;")
        adminlar = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    mes_to_admin: str = "🫡Iltimos reklama va homiylik bo'yicha adminlarimizga murojat qiling.\n"
    for person in adminlar:
        mes_to_admin += f"{person[0]}."
        if person[2] is not None:
            mes_to_admin += f" @{person[2]},"
        if person[3] is not None:
            mes_to_admin += f" {person[3]},"
        if person[4] is not None:
            mes_to_admin += f" {person[4]},"
        mes_to_admin += "\n"
    bot.send_message(message.chat.id, mes_to_admin)


# contest------------------------------------------------------------------------------
from contest11_30 import top_referrers_handler


@bot.callback_query_handler(func=lambda call: call.data == "show_list_kon")
def edit_text(call):
    top_referrers_handler(call.message)


@bot.message_handler(func=lambda message: message.text == "🎁Konkurs")
def k7(message):
    if check_user_in_channel(message):
        send_link(message)

@bot.message_handler(func=lambda message: message.text == "◀️Orqaga")
def back(message):
    global get_anime, get_anime_nom, anime_del, anime_change, add_uz_bool, broadcast_mode, enable_yutuq, enable_rule, konkurs_switch, get_anime_qism, get_anime_fasl
    global get_anime_janr, get_anime_hol, get_post_vid_or_photo, file_list, kd_bool, get_post_bool, add_channel_bool, del_channel_bool, hisobot_bool, enable_del, enable_add
    get_anime_qism = False
    get_anime_fasl = False
    get_anime_janr = False
    get_anime_hol = False
    file_list = []
    broadcast_mode = False
    enable_yutuq = False
    enable_rule = False
    konkurs_switch = False
    kd_bool = False
    get_post_bool = False
    add_channel_bool = False
    del_channel_bool = False
    hisobot_bool = False
    enable_add = False
    enable_del = False


    get_anime = False
    get_anime_nom = False
    anime_del = False
    anime_change = False
    add_uz_bool = False
    get_post_vid_or_photo = False
    bot.send_message(message.chat.id, "📋Bosh menyu", reply_markup=main_keyboard(message))


# Boshqaruv paneli----------------

broadcast_mode = False


@bot.message_handler(func=lambda message: message.text == "🛂Boshqaruv")
def control(message):
    if is_admin(message.chat.id):
        bot.send_message(message.chat.id, "✅Siz admin ekanligingiz tasdiqlandi.", reply_markup=get_control_keyboard())
        bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAICmWd2qLc5grUQzAkIASgXwR4-jW1FAAKfGgAC43BwSQoc1Niaab0fNgQ")
    else:
        bot.send_message(message.chat.id, "❌Siz bu tizimdan foyadalanish huquqiga ega emasiz.")
        bot.send_sticker(message.chat.id, "CAACAgQAAxkBAAICk2d2pwlY_Az7yUl1HN1qkEGGlkLmAAI2EwACGJ3wUKir7ygymVAENgQ")


# statistika tugmasi----------------------------

def blockers_pp():
    s:int = 0
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users;")
        peaple = cursor.fetchall()
        for user_id in peaple:
            try:
                bot.send_message(chat_id=user_id[0], text="Hello! Just testing 😊")
            except ApiException as e:
                if "Forbidden: bot was blocked by the user" in str(e):
                    s += 1

        cursor.execute("UPDATE blockers SET number_blok = %s WHERE id = %s", (s, 1))
        conn.commit()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return s


@bot.callback_query_handler(func=lambda call: call.data == "num_blockers")
def num_b(call):
    son = blockers_pp()
    if son is None:
        son = 0
    bot.send_message(call.message.chat.id,
                     f"❇️Faol foydalanuvchilar soni: {count_users() - int(son)}\n⭕️Blocklagan boydalanuvchilar soni: {son} ")





@bot.message_handler(func=lambda message: message.text == "📊Statistika" and is_admin(message.chat.id))
def user_num(message):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="Ma'lumotlarni yangilash", callback_data="num_blockers")
    keyboard.add(button)
    blocker_num = 0
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT number_blok FROM blockers;")
        blocker_num= cursor.fetchone()[0]
    except Exception as e:
        print(f"Database connection error: {e}")
    finally:
        cursor.close()
        release_connection(conn)
    bot.send_message(message.chat.id, f"📋Bot foydalanuvchilar soni: {count_users()}\n❇️Faol foydalanuvchilar soni: {count_users() - blocker_num}\n⭕️Blocklagan boydalanuvchilar soni: {blocker_num}\n\nPS:(Ma'lumotlarni yangilash) buyrug'i faqat botni bloklagan foydalanuvchi sonini aniqlaydi.", reply_markup=keyboard)


# Broadcast tugmasi-----------------------------

@bot.message_handler(func=lambda message: message.text == "📃Xabar yuborish" and is_admin(message.chat.id))
def start_broadcast(message):
    global broadcast_mode
    broadcast_mode = True
    bot.send_message(message.chat.id, text="❇️ Yuboriladigan xabarni shu yerga yozing…")



# "🎁Ko'nkurs"--------------------------------------------------------------------------------------------------------
from contest11_30 import prize, taking_prizes, rues, taking_rules, kon_start, kon_stop

enable_yutuq = False
enable_rule = False
konkurs_switch = False



def contest_status_check():
    conn = get_connection()
    cursor = conn.cursor()
    status: bool = False
    try:
        cursor.execute("SELECT contest_status FROM gifts;")
        status = cursor.fetchone()[0]
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return status


kon_holat = "🔴Konkurs tugagan"


@bot.message_handler(func=lambda message: message.text == "🎁Ko'nkurs" and is_admin(message.chat.id))
def referal(message):
    bot.send_message(message.chat.id, "Qiziqarli Ko'nkurslarni boshlang!😄", reply_markup=get_contest_keyboard())


@bot.message_handler(func=lambda message: message.text == "🎁Yutuqlar" and is_admin(message.chat.id))
def k1(message):
    global enable_yutuq
    enable_yutuq = True
    prize(message)


@bot.message_handler(func=lambda message: enable_yutuq and is_admin(message.chat.id))
def k2(message):
    global enable_yutuq
    enable_yutuq = False
    taking_prizes(message)


@bot.message_handler(func=lambda message: message.text == "📃Qoidalar" and is_admin(message.chat.id))
def k3(message):
    global enable_rule
    enable_rule = True
    rues(message)


@bot.message_handler(func=lambda message: enable_rule and is_admin(message.chat.id))
def k4(message):
    global enable_rule
    enable_rule = False
    taking_rules(message)


@bot.message_handler(func=lambda message: message.text == "🧩Boshlash")
def k5(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for i in range(1, 6):
            cursor.execute("UPDATE gifts SET contest_status = %s WHERE id = %s", (True, i))
        bot.send_message(message.chat.id, f"Contest status: True")
        conn.commit()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    kon_start(message)


@bot.message_handler(func=lambda message: message.text == "⛔️To'xtatish")
def k6(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        for i in range(1, 6):
            cursor.execute("UPDATE gifts SET contest_status = %s WHERE id = %s", (False, i))
        bot.send_message(message.chat.id, f"Contest status: False")
        conn.commit()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    kon_stop(message)


# 🎥Anime sozlash--------------------------------------------------------------------------------------------------
get_anime = False
get_anime_nom = False
get_anime_qism = False
get_anime_fasl = False
get_anime_janr = False
get_anime_hol = False
anime_del = False
anime_change = False
anime_kod = get_last_kod()
file_n: str = ""
file_m: str = ""
file_q: str = ""
file_f: str = ""
file_j: str = ""
file_h: str = ""
print(anime_kod)
add_uz_bool = False
file_list = []
get_post_vid_or_photo = False


@bot.message_handler(func=lambda message: message.text == "🎥Anime sozlash" and is_admin(message.chat.id))
def create_keyboard_of_anime_change(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_st = types.KeyboardButton("❇️Anime qo'shish")
    item_xy = types.KeyboardButton("🗑Anime o'chrish")
    item_pt = types.KeyboardButton("🔱O'zgartirish")
    item_bc = types.KeyboardButton("◀️Orqaga")

    markup.row(item_st, item_xy)
    markup.row(item_bc, item_pt)

    bot.send_message(message.chat.id, "Anime Sozlash bo'limi!", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "❇️Anime qo'shish" and is_admin(message.chat.id))
def add_anime(message):
    global get_anime_nom
    get_anime_nom = True
    bot.send_message(message.chat.id, "Nomini kiriting")


@bot.message_handler(func=lambda message: get_anime_nom and is_admin(message.chat.id))
def get_file_name(message):
    global file_m, get_anime_nom, get_anime_qism
    file_m = message.text
    get_anime_nom = False
    get_anime_qism = True
    bot.send_message(message.chat.id, "Qismlar sonini kiriting")


@bot.message_handler(func=lambda message: get_anime_qism and is_admin(message.chat.id))
def get_file_name(message):
    global file_q, get_anime_qism, get_anime_hol
    file_q = message.text
    get_anime_hol = True
    get_anime_qism = False
    bot.send_message(message.chat.id, "Anime holatini kiriting !")


@bot.message_handler(func=lambda message: get_anime_hol and is_admin(message.chat.id))
def get_file_name(message):
    global file_h, get_anime_fasl, get_anime_hol
    file_h = message.text
    get_anime_fasl = True
    get_anime_hol = False
    bot.send_message(message.chat.id, "Anime sifatini kiriting !")

@bot.message_handler(func=lambda message: get_anime_fasl and is_admin(message.chat.id))
def get_file_name(message):
    global file_f, get_anime_fasl, get_anime_janr
    file_f = message.text
    get_anime_janr = True
    get_anime_fasl = False
    bot.send_message(message.chat.id, "Anime janrini kiriting !")



@bot.message_handler(func=lambda message: get_anime_janr and is_admin(message.chat.id))
def get_file_name(message):
    global file_j, get_anime_janr, get_anime, get_post_vid_or_photo
    file_j = message.text
    get_anime = True
    get_anime_janr = False
    get_post_vid_or_photo = True
    bot.send_message(message.chat.id, "🖼 Suratini yoki Videosini tashlang.")


@bot.message_handler(content_types=['photo', 'video', 'document'],
                     func=lambda message: get_anime and is_admin(message.chat.id))
def handle_file_upload(message):
    global file_list, get_anime, get_post_vid_or_photo
    file_id = None
    file_name = "Unknown"

    if message.photo:
        file_id = message.photo[-1].file_id  # Get the largest photo
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        file = message.document  # Get the uploaded file info
        if file.mime_type == "video/x-matroska":  # Check if it's an MKV file
            file_id = file.file_id
            file_type = "mkv"
        elif file.mime_type == "video/mp4" or file.file_name.endswith(".mp4"):
            file_id = file.file_id
            file_type = "mp4"
        else:
            bot.reply_to(message, "⛔️Unsupported file type.")
            return
    else:
        bot.reply_to(message, "⛔️Unsupported file type.")
        return

    # Save file metadata to database
    if file_id:
        file_list.append({"message_id": message.message_id, "file_id": file_id, "file_type": file_type})
        file_list.sort(key=lambda x: x["message_id"])
    # save_file_eng(anime_kod2, file_id, file_n, file_type)

    bot.reply_to(message, f"✅{file_type.capitalize()} saved successfully! /save")
    if get_post_vid_or_photo:
        get_post_vid_or_photo = False
        bot.send_message(message.chat.id,
                         "🎥Ok, yuklamoqchi bo'lgan anime qismlarini tartib bo'yicha tashlang (1 -> 12)")


@bot.message_handler(func=lambda message: is_admin(message.chat.id), commands=["save"])
def finish_file_upload(message):
    global file_m, file_q, file_h, file_f, file_j,file_list, get_anime
    sorted_files = file_list
    anime_code = get_last_kod()+1
    get_anime = False
    file_n = f"✨{file_m}✨\n╭─────────────────────\n├‣ Holat: {file_h}\n├‣ Sifat - {file_f}\n├‣ Qism: {file_q}\n├‣ Janrlar: {file_j}\n╰──────────────────────"

    for file in sorted_files:
        save_file(anime_code, file["file_id"], file_n, file["file_type"])
    bot.reply_to(message, f"✅{file_n.split("\n")[0]} saved successfully!")
    bot.reply_to(message, f"✅Anime kodi: {anime_code}")
    file_list = []


@bot.message_handler(func=lambda message: message.text == "🗑Anime o'chrish" and is_admin(message.chat.id))
def del_anime(message):
    global anime_del
    anime_del = True
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")
    bot.send_message(message.chat.id, m)
    bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan anime kodini kiriting...")


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and anime_del)
def delete_anime_from_anime_list(message):
    global anime_del
    anime_del = False
    try:
        kod = int(message.text)
        try:
            conn = get_connection()

            cursor = conn.cursor()
        except Exception as e:
            print(f"Database connection error: {e}")
            exit()
        cursor.execute("DELETE FROM files WHERE file_kod = %s", (kod,))
        conn.commit()
        cursor.close()
        release_connection(conn)
        bot.send_message(message.chat.id, "✅Anime muvaffaqiyatli o'chirildi")
    except Exception as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik yuz berdi: {e}")


add_ep_bool1 = False
add_ep_bool2 = False
ep_num: int = 0
an_name: str = "Unknown"


@bot.callback_query_handler(func=lambda call: call.data == "ep_anime")
def change_anime_ep(call):
    global add_ep_bool1
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(call.message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")
    bot.send_message(call.message.chat.id, m)
    bot.send_message(call.message.chat.id, "Qism qo'shiladigan anime kodini kiriting...")
    add_ep_bool1 = True


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and add_ep_bool1)
def add_episode(message):
    global ep_num, an_name, add_ep_bool1, add_ep_bool2, til
    try:
        conn = get_connection()

        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()

    cursor.execute("SELECT file_kod, file_name FROM files;")
    eplist = cursor.fetchall()
    for i in eplist:
        if int(i[0]) == int(message.text):
            an_name = i[1]
            break
    if an_name == "Unknown":
        bot.send_message(message.chat.id, "Siz mavjud bo'lmagan kod kiritingiz!")
    else:
        ep_num = int(message.text)
        add_ep_bool2 = True
        bot.send_message(message.chat.id,
                         f"🎥Ok, {an_name} animesiga yuklamoqchi bo'lgan qismni/larni tartib bo'yicha tashlang...")
    add_ep_bool1 = False
    cursor.close()
    release_connection(conn)


@bot.message_handler(content_types=['video', 'document'],
                     func=lambda message: add_ep_bool2 and is_admin(message.chat.id))
def handle_file_upload(message):
    global ep_num, an_name
    file_id = 0
    file_type = 'photo'
    if message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.document:
        file = message.document  # Get the uploaded file info
        if file.mime_type == "video/x-matroska":  # Check if it's an MKV file
            file_id = file.file_id
            file_type = "mkv"
        elif file.mime_type == "video/mp4" or file.file_name.endswith(".mp4"):
            file_id = file.file_id
            file_type = "mp4"
        else:
            bot.reply_to(message, "⛔️Unsupported file type.")
    else:
        bot.reply_to(message, "⛔️Unsupported file type.")
        return

    # Save file metadata to database
    save_file(ep_num, file_id, an_name, file_type)
    bot.reply_to(message, f"✅{file_type.capitalize()} saved successfully!")


@bot.callback_query_handler(func=lambda call: call.data == "name_anime")
def change_anime_name(call):
    global anime_change
    anime_change = True
    roy = show_anime_list()
    m = ""
    k = 0
    for i in roy:
        k += 1
        if k >= 50:
            bot.send_message(call.message.chat.id, m)
            k = 0
            m = ""
        m += ("🆔" + i + "\n")
    bot.send_message(call.message.chat.id, m)
    bot.send_message(call.message.chat.id,
                     "O'zgartirmoqchi bo'lgan anime kodi va yangi nomini kiriting Eg. 1, Anime_name. Vergul bo'lishi shart.")


@bot.message_handler(func=lambda message: anime_change and is_admin(message.chat.id))
def change_name(message):
    global anime_change
    try:
        conn = get_connection()

        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    k = message.text.split(",")
    try:
        cursor.execute("UPDATE files SET file_name = %s WHERE file_kod = %s", (k[1], int(k[0])))
        conn.commit()
        bot.send_message(message.chat.id, "✅Anime muvaffaqiyatli o'zgartirildi.")

    except Exception as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik yuz berdi: {e}")
    finally:
        cursor.close()
        release_connection(conn)
        anime_change = False


@bot.message_handler(func=lambda message: message.text == "🔱O'zgartirish" and is_admin(message.chat.id))
def change_anime(message):
    keyboard = InlineKeyboardMarkup()
    button_name = InlineKeyboardButton(text="Nomini o'zgartish", callback_data="name_anime")
    button_ep = InlineKeyboardButton(text="Qismini o'zgartirish", callback_data="ep_anime")
    keyboard.add(button_ep, button_name)
    bot.send_message(message.chat.id, "Animeni qanday o'zgartirmoqchisiz ?", reply_markup=keyboard)




# 📬Post tayyorlash----------------------------------------------------------------------------------------------------------------
kd_bool = False
kd = 0
get_post_bool = False
CAPTION: str = "This is a caption for the photo!"
FILE_ID: str = "AgACAgIAAxkBAAIVLGeSgqErwpnTn6rQBDNA0MBLlueRAAJ96jEbetaRSPk5lM895IfOAQADAgADeAADNgQ"
BUTTON = {
    "inline_keyboard": [
        [
            {
                "text": "🔹👉Anime ko'rish",  # Button text
                "url": f"https://t.me/{bot_username}?start={kd}"  # URL the button links to
            }
        ]
    ]
}


@bot.callback_query_handler(func=lambda call: call.data == "send_channel")
def channelsend(call):
    global video_bool
    url7 = f"https://api.telegram.org/bot{API_key}/sendPhoto"
    url8 = f"https://api.telegram.org/bot{API_key}/sendVideo"
    if video_bool:
        response = requests.post(url8, data=get_payload())
    else:
        response = requests.post(url7, data=get_payload())

    if response.status_code == 200:
        print("Photo sent successfully!")
    else:
        print(f"Failed to send photo: {response.status_code} - {response.text}")


@bot.message_handler(func=lambda message: message.text == "📬Post tayyorlash" and is_admin(message.chat.id))
def create_post(message):
    global kd_bool
    kd_bool = True
    bot.send_message(message.chat.id, "Iltimos, Anime ko'dini kiriting.")


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and kd_bool)
def get_post(message):
    global kd, kd_bool, get_post_bool
    kd_bool = False
    get_post_bool = True
    try:
        kd = int(message.text)
        bot.send_message(message.chat.id, "Iltimos, foto va anime postingizni tashlang...")
    except Exception as e:
        bot.send_message(message.chat.id, f"Siz noto'g'ri kod kiritdingiz. Iltimos jarayonni boshqattan boshlang!")


@bot.message_handler(content_types=["text", "photo", "video"],
                     func=lambda message: is_admin(message.chat.id) and get_post_bool)
def ready_post(message):
    global kd, nm_channel, CAPTION, FILE_ID, get_post_bool, BUTTON, video_bool
    get_post_bool = False

    BUTTON = {
        "inline_keyboard": [
            [
                {
                    "text": "🔹👉Anime ko'rish",  # Button text
                    "url": f"https://t.me/{bot_username}?start={kd}"  # URL the button links to
                }
            ]
        ]
    }

    try:
        conn = get_connection()

        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()

    cursor.execute('SELECT  file_name FROM files WHERE file_kod = %s', (kd,))
    file_lost = cursor.fetchone()
    cursor.close()
    release_connection(conn)
    CAPTION = f"{file_lost[0]}"
    link = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="🔹👉Anime ko'rish", url=f"https://t.me/{bot_username}?start={kd}")
    button2 = InlineKeyboardButton(text=nm_channel, callback_data="send_channel")
    link.add(button)
    link.add(button2)
    if message.content_type == "photo":
        bot.send_photo(message.chat.id, message.photo[-1].file_id, caption=f"{file_lost[0]}",
                       reply_markup=link)
        FILE_ID = message.photo[-1].file_id
    elif message.content_type == "video":
        bot.send_video(message.chat.id, message.video.file_id, caption=f"{file_lost[0]}",
                       reply_markup=link)
        FILE_ID = message.video.file_id
        video_bool = True
    else:
        bot.send_message(message.chat.id, "Siz noto'g'ri turdagi xabar yubordiz!")


video_bool = False

# "📢Kanallar"-----------------------------------------
add_channel_bool = False
del_channel_bool = False
hisobot_bool = False
CHANNEL_ID = "@ozbek_animelar"

nm_channel: str = "Animelar"


@bot.callback_query_handler(func=lambda call: call.data == "oth_channel")
def channel_add_to_post(call):
    global hisobot_bool
    hisobot_bool = True
    bot.send_message(call.message.chat.id,
                     "Kanal nomini, silkasisini  vergul bilan ajratib kiriting .\nkanal_nomi,kanal_silkasi")


@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def channel_add_to_list(call):
    global add_channel_bool
    add_channel_bool = True
    bot.send_message(call.message.chat.id,
                     "Kanal nomi, havolasi va obunachilar sonini vergul bilan ajratib kiriting.\nMasalan:\nkanal_nomi,kanal_linki,100")


@bot.callback_query_handler(func=lambda call: call.data == "del_channel")
def channel_add_to_list(call):
    global del_channel_bool
    del_channel_bool = True
    bot.send_message(call.message.chat.id, "Kanal kodini kiriting.")


@bot.message_handler(func=lambda message: message.text == "📢Kanallar" and is_admin(message.chat.id))
def channel_list(message):
    keyboard = InlineKeyboardMarkup()
    button_add = InlineKeyboardButton(text="➕Kanal qo'shish", callback_data="add_channel")
    button_oth = InlineKeyboardButton(text="➕Post kanali", callback_data="oth_channel")
    button_del = InlineKeyboardButton(text="➖Kanal o'chrish", callback_data="del_channel")
    keyboard.add(button_oth)
    keyboard.add(button_add)
    keyboard.add(button_del)
    try:
        conn = get_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    cursor.execute("SELECT * FROM channels;")
    ch_list = cursor.fetchall()
    cursor.close()
    release_connection(conn)
    mm: str = ""
    for c in ch_list:
        mm += f"{c[0]}. {c[1]} , {c[2]} , {c[4]}\n"
    try:
        bot.send_message(message.chat.id, mm, reply_markup=keyboard)
    except:
        bot.send_message(message.chat.id, "Kanalingizni kiriting!\n\nPS:Kanalni qo‘shishdan oldin, iltimos botni ushbu kanalga administrator qilib qo‘yishni unutmang.", reply_markup=keyboard)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and add_channel_bool)
def add_channel(message):
    global add_channel_bool
    conn = get_connection()
    cursor = conn.cursor()


    m = message.text.split(",")
    try:
        cursor.execute("""
        INSERT INTO channels (channel_name,channel_url, num_channel, now_channel)
        VALUES (%s,%s,%s,%s)
        """, (m[0], m[1], m[2], 0))
        conn.commit()
        bot.send_message(message.chat.id, "✅Kanal muvoffaqiyatli qo'shildi.")
    except Error as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik: {e}")
    finally:
        add_channel_bool = False
        cursor.close()
        release_connection(conn)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and del_channel_bool)
def del_channel(message):
    global del_channel_bool
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM channels WHERE id = %s", (int(message.text),))
        conn.commit()

        bot.send_message(message.chat.id, "✅Kanal muvoffaqiyatli o'chirildi")
    except Error as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik: {e}")
    finally:
        cursor.close()
        release_connection(conn)
        del_channel_bool = False


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and hisobot_bool)
def qosh_kanal(message):
    global hisobot_bool, nm_channel, CHANNEL_ID
    hisobot_bool = False
    try:
        ll = message.text.split(",")
        CHANNEL_ID = f"@{ll[1][13:]}"
        nm_channel = ll[0]
        bot.send_message(message.chat.id, "✅Kanal muvoffaqiyatli qo'shildi.")
    except:
        bot.send_message(message.chat.id, "⛔️Kanal o'rnamadi, iltimos qayta urining.")


def get_payload():
    global CAPTION, CHANNEL_ID, FILE_ID, BUTTON, video_bool
    if video_bool:
        payload = {
            "chat_id": CHANNEL_ID,
            "video": FILE_ID,
            "caption": CAPTION,
            "reply_markup": json.dumps(BUTTON)  # Inline keyboard markup must be JSON-encoded
        }
        video_bool = False
    else:
        payload = {
            "chat_id": CHANNEL_ID,
            "photo": FILE_ID,
            "caption": CAPTION,
            "reply_markup": json.dumps(BUTTON)  # Inline keyboard markup must be JSON-encoded
        }

    return payload


# Admins tugmasi--------------------------------------
enable_add = False
enable_del = False


@bot.callback_query_handler(func=lambda call: call.data == "add_admin")
def admin_add(call):
    global enable_add, enable_del
    enable_add = True
    enable_del = False
    bot.send_message(call.message.chat.id, "📃Admin qilmoqchi bo'lgan shaxsning 'username'ini  kiriting...")


@bot.callback_query_handler(func=lambda call: call.data == "del_admin")
def admin_del(call):
    global enable_del, enable_add
    enable_del = True
    enable_add = False
    bot.send_message(call.message.chat.id, "🔢Admin raqamini jo'nating...")


@bot.message_handler(func=lambda message: message.text == "📋Adminlar" and is_admin(message.chat.id))
def show_admins(message):
    keyboard = InlineKeyboardMarkup()
    button_add = InlineKeyboardButton(text="➕Admin qo'shish", callback_data="add_admin")
    button_del = InlineKeyboardButton(text="➖Admin o'chrish", callback_data="del_admin")
    keyboard.add(button_add)
    keyboard.add(button_del)
    try:
        conn = get_connection()

        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    cursor.execute("SELECT * FROM admins;")
    adminlar = cursor.fetchall()
    mes_to_admin: str = ""
    for person in adminlar:

        mes_to_admin += f"{person[0]}."
        if person[2] is not None:
            mes_to_admin += f" {person[2]},"
        if person[3] is not None:
            mes_to_admin += f" {person[3]},"
        if person[4] is not None:
            mes_to_admin += f" {person[4]},"
        mes_to_admin += "\n"
    try:
        bot.send_message(message.chat.id, mes_to_admin, reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"Admin qo'shing !\n{e}", reply_markup=keyboard)
    finally:
        cursor.close()
        release_connection(conn)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and enable_add)
def search_admin(message):
    global enable_add

    try:
        conn = get_connection()

        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    cursor.execute("SELECT * FROM users;")
    people = cursor.fetchall()
    try:
        num = int(message.text)
        for p in people:
            if p[0] == num:
                log_admin(p[1], p[2], p[3], p[4])
                bot.send_message(message.chat.id, "✅Yangi Admin o'rnatildi")
                break

        enable_add = False

    except ValueError:
        mes_to_admin: str = ""
        for person in people:

            if message.text in person:
                mes_to_admin += f"{person[0]}."
                if person[2] is not None:
                    mes_to_admin += f" {person[2]},"
                if person[3] is not None:
                    mes_to_admin += f" {person[3]},"
                if person[4] is not None:
                    mes_to_admin += f" {person[4]},"
                mes_to_admin += "\n"
        bot.send_message(message.chat.id, f"Natijalar:\n{mes_to_admin}Ism oldidagi raqamni jo'nating")
    except Exception as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik: {e}")
        enable_add = False
    finally:
        cursor.close()
        release_connection(conn)


@bot.message_handler(func=lambda message: is_admin(message.chat.id) and enable_del)
def search_admin(message):
    global enable_del

    try:
        conn = get_connection()

        cursor = conn.cursor()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    cursor.execute("SELECT * FROM admins;")
    try:
        num = int(message.text)
        cursor.execute("DELETE FROM admins WHERE id = %s", (num,))
        conn.commit()
        enable_del = False
        bot.send_message(message.chat.id, "😎Adim muvoffaqiyatli o'chirildi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"⛔️Tizimda xatolik: {e}")
        enable_del = False
    finally:
        cursor.close()
        release_connection(conn)


# bot holati tugmasi----------------------------------
@bot.callback_query_handler(func=lambda call: call.data == "starts")
def startsbot(call):
    global holatbot
    holatbot = True
    switch(call.message)


def startbot(message):
    mes_key = InlineKeyboardMarkup()
    but1 = InlineKeyboardButton(text="✅Turn On", callback_data="starts")
    mes_key.add(but1)
    bot.send_message(message.chat.id, "⛔️Bot to'xtatildi.", reply_markup=mes_key)


@bot.callback_query_handler(func=lambda call: call.data == "stop")
def stops(call):
    global holatbot
    holatbot = False
    startbot(call.message)


@bot.message_handler(func=lambda message: message.text == "🤖Bot holati" and is_admin(message.chat.id))
def switch(message):
    global holatbot
    if is_admin(message.chat.id):
        keyboard = InlineKeyboardMarkup()
        if holatbot:
            hol = "Ishalamoqda"
        else:
            hol = "To'xtatilgan"
        button2 = InlineKeyboardButton(text="🚷Turn off", callback_data="stop")

        keyboard.add(button2)
        bot.send_message(message.chat.id, f"😇Bot holati: {hol}", reply_markup=keyboard)


# Back tugmasi---------------------------------------------



# Anime Izlash-------------------------------------------------------------------------------------------------------


@bot.message_handler(content_types=["text", "photo", "video", "audio", "document", "sticker"],
                     func=lambda message: holatbot)
def kod_check(message):
    global broadcast_mode

    mmm = message.text
    if message.chat.type in ["group", "supergroup"] and "kkk" not in message.text.lower():
        return
    elif message.chat.type in ["group", "supergroup"] and "kkk" in message.text.lower():
        mmm = message.text[4:]

    if is_admin(message.chat.id) and broadcast_mode:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users;")
            peaple = cursor.fetchall()

        except Exception as e:
            print(f"Database connection error: {e}")
            exit()
        finally:
            cursor.close()
            release_connection(conn)
        for user in peaple:
            try:
                user_id = user[1]
                if message.content_type == "text":
                    bot.send_message(user_id, message.text)
                    # Broadcast photos
                elif message.content_type == "photo":
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
                    # Broadcast videos
                elif message.content_type == "video":
                    bot.send_video(user_id, message.video.file_id, caption=message.caption)
                    # Broadcast audio
                elif message.content_type == "audio":
                    bot.send_audio(user_id, message.audio.file_id, caption=message.caption)
                    # Broadcast documents
                elif message.content_type == "document":
                    bot.send_document(user_id, message.document.file_id, caption=message.caption)
                elif message.content_type == "sticker":
                    bot.send_sticker(user_id, message.sticker.file_id)
            except Exception as e:
                print(f"⭕️️Bu userga xabar jo'natilmadi. {user}: {e}")
            finally:
                broadcast_mode = False
        bot.send_message(message.chat.id, "Xabar yuborib tugallandi.")
    else:
        try:
            file_kod = int(mmm)
            if file_kod <= (get_last_kod()+1) and get_file(file_kod) != 0:

                file_n_i = get_file(file_kod)
                k = -1
                for f in file_n_i:
                    if f:
                        saved_file_id, file_name, file_type = f
                        k += 1
                        # Send file using its file_id
                        if file_type == "photo":
                            bot.send_photo(message.chat.id, saved_file_id, caption=file_name)

                        elif file_type == 'video':
                            if k == 0:
                                bot.send_video(message.chat.id, saved_file_id, caption=file_name)
                            else:
                                bot.send_video(message.chat.id, saved_file_id, caption=f"{k} - qism")

                        else:
                            try:
                                bot.send_document(message.chat.id, saved_file_id, caption=f"{k} - qism")
                            except:
                                bot.reply_to(message, "⭕️Unknown file type.")
                    else:
                        bot.reply_to(message, "⭕️File not found.")
            else:
                bot.send_message(message.chat.id, "🙁Bu kod bizning ro'yhatimizda topilmadi.")
        except:
            ani_res_list = get_ani_kod(mmm.lower())
            l = ""
            for x in ani_res_list:
                l += f"{x[1]}:  {x[2]}\n"
            bot.send_message(message.chat.id, l)



def get_result(list1):
    results: list = []
    dont_rety: list = []
    for p in list1:
        if p[1] not in dont_rety:
            dont_rety.append(p[1])
            results.append(
                InlineQueryResultArticle(
                    id=str(p[0]),
                    title=p[2].split("\n")[0],
                    description=f"Anime is the best thing in the world 😇",
                    input_message_content=InputTextMessageContent(f"{p[1]}"),
                )
            )
    return results


@bot.inline_handler(lambda query: len(query.query) > 0)  # Only trigger when user types something
def inline_query_handler(query):
    results = get_result(get_ani_kod(query.query.lower()))

    bot.answer_inline_query(query.id, results, cache_time=1)


print("Your bot is running")

bot.polling(none_stop=True)
# bot.polling(none_stop=True, interval=1, timeout=2, long_polling_timeout=10)


# Close the database connection properly when the script exits
