from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import telebot
import psycopg2
from psycopg2 import  Error
from dotenv import load_dotenv, find_dotenv
import os
from urllib.parse import urlparse


load_dotenv(find_dotenv())
API_key = os.getenv("API_KOD11_30")

bot = telebot.TeleBot(API_key)


#url = urlparse(DATABASE_URL)

from psycopg2 import pool


DATABASE_URL = os.getenv("DATABASE_URL")

# Create a connection pool

db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,  # adjust as needed
    dbname="neondb",
    user="neondb_owner",
    password="npg_tK7QZEec4mBv",
    host="ep-delicate-bush-ag1i4dsy-pooler.c-2.eu-central-1.aws.neon.tech",
    port="5432",
    sslmode="require"
)

def get_connection():
    return db_pool.getconn()

def release_connection(conn):
    db_pool.putconn(conn)

def log_gifts(gift_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO gifts (gift_name)
        VALUES (%s);
        """, (gift_name,))

        conn.commit()
    except Error as e:
        print("Error logging user:", e)
    finally:
        cursor.close()
        release_connection(conn)




def get_top_referrers():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id, referrals FROM kon_users ORDER BY referrals DESC LIMIT 10")
        ls = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    return ls

def find_name(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users;")
        people = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)

    for id_p, user_id_p, username,first_name,last_name in people:
        if user_id_p == user_id and username is not None:
            return username
        elif user_id_p == user_id and (first_name is not None or last_name is not None):
            ans = f"{first_name} {last_name}"
            return ans
    return None



def top_referrers_handler(message: types.Message):
    top_referrers = get_top_referrers()
    if not top_referrers:
        bot.reply_to(message, "No referrals yet!")
        return

    # Format the leaderboard message
    leaderboard = "🏆 Top 10 Referrers:\n\n"
    for rank, (user_id, count) in enumerate(top_referrers, start=1):
        us_name = find_name(user_id)
        leaderboard += f"{rank}.{us_name}: {count}\n"


    bot.send_message(message.chat.id, leaderboard)



def prize(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM gifts;")
        count = cursor.fetchone()[0]

        # If table is empty → insert default gifts
        if count == 0:
            default_gifts = [
                "1- ________________",
                "2- ________________",
                "3- ________________",
                "referal yig'ish (Nakrutka urgan odam ban)",
                "3.01.2025 (Juma kuni tugaydi)"
            ]

            for gift in default_gifts:
                cursor.execute("INSERT INTO gifts (gift_name) VALUES (%s);", (gift,))
            conn.commit()
        # Now read gifts
        cursor.execute("SELECT * FROM gifts;")
        pr = cursor.fetchall()



    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    bot.send_message(message.chat.id, f"{pr[0][1]}\n{pr[1][1]}\n{pr[2][1]}\nXabar ko'rinishi shunga o'xshash bo'lsin.🤨")




def taking_prizes(message):
    conn = get_connection()
    cursor = conn.cursor()

    presents: list = message.text.split("\n")
    try:
        cursor.execute("UPDATE gifts SET gift_name = %s WHERE id = %s", (presents[0], 1))
        cursor.execute("UPDATE gifts SET gift_name = %s WHERE id = %s", (presents[1], 2))
        cursor.execute("UPDATE gifts SET gift_name = %s WHERE id = %s", (presents[2], 3))
        conn.commit()

        bot.send_message(message.chat.id, "✅Yangi yutuqlar muvaffaqiyatli o'rnatildi.")
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)


def rues(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM gifts;")
        pr = cursor.fetchall()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
        bot.send_message(message.chat.id, f"Referal yigish ...\n10.01.2025...\nXabar ko'rinishi shunga o'xshash bo'lsin.🤨")



def taking_rules(message):
    conn = get_connection()
    cursor = conn.cursor()
    presents: list = message.text.split("\n")
    try:
        cursor.execute("UPDATE gifts SET gift_name = %s WHERE id = %s", (presents[0], 4))
        cursor.execute("UPDATE gifts SET gift_name = %s WHERE id = %s", (presents[1], 5))
        bot.send_message(message.chat.id, "✅Yangi qoidalar muvaffaqiyatli o'rnatildi.")
        conn.commit()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)


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

def kon_start(message):

    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="📊O'rinlar ro'yhati", callback_data="show_list_kon")
    keyboard.add(button1)



    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM gifts;")
        pr = cursor.fetchall()
        rules = pr[3]
        kun = pr[4]

        kon_holat = "✅Davom etmoqda"
        if not contest_status_check():
            kon_holat = "🔴Konkurs tugagan"
        cursor.execute("SELECT * FROM kon_users;")
        people = cursor.fetchall()
        count = 0
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    for p in people:
        if p[1] == message.chat.id:
            count = p[2]
            break
    bot.send_message(message.chat.id,
                     f"🎉Bizning jamoa\n Konkursimizga start berdik !!!\n✏️Qoidalar : {rules[1]}\n\n🎁So'vrinlar\n🎁{pr[0][1]}\n🎁{pr[1][1]}\n🎁{pr[2][1]}\n✅Hammaga omad\n📆Konkursimiz {kun[1]}\n💰Qantashish uchun botga o'tib Konkurs knopkasini bosing!!!\n────────────────\n🔥Sizning taklif havolangiz : https://t.me/{bot.get_me().username}?start={message.chat.id}\n-\n🖇Sizning takliflaringiz : {count}\n-\n{kon_holat}",
                     reply_markup=keyboard)

def kon_stop(message):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM kon_users;")
        people = cursor.fetchall()
        for p in people:
            cursor.execute("UPDATE kon_users SET referrals = %s WHERE user_id = %s", (0, p[1]))
            conn.commit()
    except Exception as e:
        print(f"Database connection error: {e}")
        exit()
    finally:
        cursor.close()
        release_connection(conn)
    bot.send_message(message.chat.id, text = "Konkurs to'xtatildi.⛔️")



