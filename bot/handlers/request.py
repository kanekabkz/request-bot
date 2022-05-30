import logging
import re
from functools import partial
from time import time

from telegram.ext import MessageHandler, CallbackQueryHandler, Filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.utils.helpers import escape_markdown
import bot.configs as vars

logging.getLogger(__name__).setLevel(logging.INFO)



# IMPORTANT VARIABLES
OWNER_ID = vars.OWNER_ID
GROUP_ID = vars.REQUEST_GROUP_ID
CHANNEL_ID = vars.REQUEST_CHANNEL_ID
CHANNEL_LINK = vars.REQUEST_CHANNEL_LINK
REQUEST_COMPLETE_TEXT = vars.REQUEST_COMPLETE_TEXT

ON_REQUEST = "*👋Merhaba! *[{}](tg://user?id={})*\n\n🔹 {} için yapmış olduğun talebin gönderildi.\n\n🔹Talebin birazdan yanıtlanacak.\n\n🔹Adminler müsait olmayabilir. Sabırlı olmanda yarar var⏳.\n\n👇Talep durumuna buradan bakabilirsin.👇*"
REQUEST = "*Request By *[{}](tg://user?id={})*\n\nRequest: {}*"
ON_DONE = "**[{}](tg://user?id={})*😎\n\n{} Talebin kabul edildi! 🥳{}\n\n👍Bize ulaştığın için teşekkürler.\!*"
ON_REJECT = "**[{}](tg://user?id={})*😎\n\n{} için yapmış olduğun talep reddedildi. 😥\n\nSebebi: {}\n\n👍Bize ulaştığın için teşekkürler\!*"
IF_REQUEST_EMPTY = "<b>👋Hello <a href='tg://user?id={}'>{}</a>\nYour Request is Empty.\nTo Request Use:👇</b>\n<code>#request &lt;Your Request&gt;</code>"



# ADDING HANDLERS
def add_request_handlers(bot):
    bot.add_handler(
        MessageHandler(filters=Filters.chat(GROUP_ID) & Filters.entity("hashtag"), callback=user_request, run_async=True)
    )

    bot.add_handler(
        CallbackQueryHandler(pattern="done", callback=done, run_async=True)
    )

    bot.add_handler(
        CallbackQueryHandler(pattern="rejected", callback=rejected, run_async=True)
    )

    bot.add_handler(
        CallbackQueryHandler(pattern="reject", callback=reject, run_async=True)
    )

    bot.add_handler(
        CallbackQueryHandler(pattern="completed", callback=completed, run_async=True)
    )





#***************HANDLERS BELOW******************

def user_request(update, context):
    if update.message.text.lower() == "#request":
        info = update.message.from_user
        update.message.reply_text(
            text = IF_REQUEST_EMPTY.format(info.id, info.first_name),
            quote = False,
            parse_mode = "html"
        )
        return
    if update.message.text.lower().startswith("#request"):
        info = update.message.from_user
        message = update.message.text[8:].strip()
        inline_keyboard1 = [[InlineKeyboardButton("İstek Mesajı💬", url=update.message.link)],[InlineKeyboardButton("🚫Reddet", callback_data="reject"), InlineKeyboardButton("Done✅", callback_data="done")]]
        context.bot.send_message(
            chat_id = CHANNEL_ID,
            text = REQUEST.format(info.first_name, info.id, message),
            reply_markup = InlineKeyboardMarkup(inline_keyboard1),
            parse_mode = "markdown"
        )
        inline_keyboard2 = [[InlineKeyboardButton("⏳İSTEK DURUMU⏳", url=CHANNEL_LINK)]]
        update.message.reply_text(
            text = ON_REQUEST.format(info.first_name, info.id, message),
            quote = False,
            reply_markup = InlineKeyboardMarkup(inline_keyboard2),
            parse_mode = "markdown"
        )


#**************CALLBACK HANDLERS*****************

def done(update, context):
    user_info = update.callback_query.from_user
    user_status = context.bot.get_chat_member(CHANNEL_ID, user_info.id).status
    if (user_status == "creator") or (user_status == "administrator"):
        original_text = update.callback_query.message.text_markdown_v2
        inline_keyboard = [[InlineKeyboardButton("Request Completed✅", callback_data="completed")]]
        update.callback_query.message.edit_text(
            text = f"*COMPLETED✅\n\n*~{original_text}~",
            reply_markup = InlineKeyboardMarkup(inline_keyboard),
            parse_mode = "markdownv2"
        )
        details = re.match(r".*\[(.*)\].*id=(\d+)", original_text)
        context.bot.send_message(
            chat_id = GROUP_ID,
            text = ON_DONE.format(details.group(1), details.group(2), "\n".join(original_text.split("\n")[2:])[9:-1], ("\n"+REQUEST_COMPLETE_TEXT) if REQUEST_COMPLETE_TEXT != "" else ""),
            parse_mode ="markdownv2"
        )
    else:
        update.callback_query.answer(
            text = "Sen de kimsin?\nAdmin değilsin!😠",
            show_alert = True
        )

def completed(update, context):
    update.callback_query.answer(
        text = f"İstek kabul edildi!🥳\n{REQUEST_COMPLETE_TEXT}",
        show_alert = True
    )

def reject(update, context):
    user_info = update.callback_query.from_user
    user_status = context.bot.get_chat_member(CHANNEL_ID, user_info.id).status
    if (user_status == "creator") or (user_status == "administrator"):
        update.callback_query.answer(
            text = "Reddetmek için bir sebep yazın.\n60 saniyeniz var.⏱️",
            show_alert = True
        )
        original_text = update.callback_query.message.text_markdown_v2
        reason = get_value(context.dispatcher, CHANNEL_ID)
        if reason is None:
            context.bot.send_message(
                chat_id = user_info.id,
                text = f"Time Out for Rejecting\n\n{original_text}",
                parse_mode = "markdownv2"
            )
            return

        reason = escape_markdown(reason, version=2)
        inline_keyboard = [[InlineKeyboardButton("Request Rejected🚫", callback_data="rejected")]]
        update.callback_query.message.edit_text(
            text = f"*REDDEDİLDİ🚫\n\nSebebi: {reason}\n\n*~{original_text}~",
            reply_markup = InlineKeyboardMarkup(inline_keyboard),
            parse_mode = "markdownv2"
        )
        details = re.match(r".*\[(.*)\].*id=(\d+)", original_text)
        context.bot.send_message(
            chat_id = GROUP_ID,
            text = ON_REJECT.format(details.group(1), details.group(2), "\n".join(original_text.split("\n")[2:])[9:-1], reason),
            parse_mode ="markdownv2"
        )
    else:
        update.callback_query.answer(
            text = "Sen de kimsin?\nAdmin değilsin!😠",
            show_alert = True
        )

def rejected(update, context):
    update.callback_query.answer(
        text = f"İstek reddedildi.😥",
        show_alert = True
    )



#*****************OTHER FUNCTIONS*******************

def get_value(dp, chat_id):

    value = [None]
    callback = partial(manage_input, value=value)

    handler = MessageHandler(filters=Filters.chat(chat_id), callback=callback, run_async=True)

    dp.add_handler(
        handler
    )

    start = time()

    while value[0] is None:
        if (time() - start) > 60:
            break
    
    dp.remove_handler(
        handler
    )
    
    return value[0]


def manage_input(update, context, value):
    value[0] = update.channel_post.text
    update.channel_post.delete()
