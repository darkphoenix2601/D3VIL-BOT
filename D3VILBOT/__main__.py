"""
MIT License

Copyright (C) 2021 MdNoor786

This file is part of @Shasa_RoBot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import importlib
import time
import re
from sys import argv
from typing import Optional
from platform import python_version as memek

from D3VILBOT import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from D3VILBOT.modules import ALL_MODULES
from D3VILBOT.modules.helper_funcs.chat_status import is_user_admin
from D3VILBOT.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown



def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


HELP_MSG = "Click the button below to get help manu in your pm."
START_MSG = "I'm awake already!\n<b>Haven't slept since:</b> <code>{}</code>"

PM_START_TEXT = """
────「 [{}](https://telegra.ph/file/ae41ca22aaff27dfb50cc.jpg) 」────
*ʜᴇʏ! {},*
*ɪ ᴀᴍ 𝐒𝐡𝐚𝐬𝐚 ᴀɴ ᴀɴɪᴍᴇ ᴛʜᴇᴍᴇᴅ ᴀᴅᴠᴀɴᴄᴇ ɢʀᴏᴜᴏ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ʙᴏᴛ ᴡɪᴛʜ ᴀ ʟᴏᴛ ᴏғ sᴘᴇᴄɪᴀʟɪᴛʏ.*
➖➖➖➖➖➖➖➖➖➖➖➖➖
✓• *Uptime:* `{}`
➖➖➖➖➖➖➖➖➖➖➖➖➖
➛ᴛʀʏ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴋɴᴏᴡ ᴍʏ ᴀʙɪʟɪᴛɪᴇs ××
"""

GROUP_START_TEXT = """
I'm awake already!
Haven't slept since: {}
"""

buttons = [
    [
        InlineKeyboardButton(
            text=f"Add {BOT_NAME} To Your Group",
            url=f"t.me/{BOT_USERNAME}?startgroup=true",
        )
    ],
    [
        InlineKeyboardButton(text="ɪɴғᴏ", callback_data="shasa_basichelp"),
        InlineKeyboardButton(text="ɪɴʟɪɴᴇ", switch_inline_query_current_chat=""),
    ],
    [
        InlineKeyboardButton(text="ʜᴇʟᴘ", callback_data="help_back"),
    ],
]


HELP_STRINGS = """
Hey there! Myself [𝐒𝐡𝐚𝐬𝐚](https://telegra.ph/file/c3f91b87fa65cd83f306d.jpg).
I'm a Queen For Fun and help admins manage their groups ! Have a look at the following for an idea of some of the things I can help you with.

*Main* commands available:
 ➛ /help: PM's you this message.
 ➛ /help <module name>: PM's you info about that module.
 ➛ /donate: information on how to donate!
 ➛ /settings:
   ❂ in PM: will send you your settings for all supported modules.
   ❂ in a group: will redirect you to pm, with all that chat's settings.
"""

DONATE_STRING = """❂ I'm Free for Everyone ❂"""


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("D3VILBOT.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="[•༶B𝚊𝚌k༶•]", callback_data="help_back"
                                )
                            ]
                        ]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                PM_START_TEXT.format(
                    escape_markdown(context.bot.first_name),
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats(),
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_animation(
            GROUP_START_IMG,
            caption="<code>Shasa is Here For You💜\nI am Awake Since</code>: <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="sᴜᴘᴘᴏʀᴛ", url=f"https://telegram.dog/{SUPPORT_CHAT}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="ᴜᴘᴅᴀᴛᴇs",
                            url="https://telegram.dog/LionXupdates",
                        )
                    ],
                ]
            ),
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update, context):
    """#TODO
    Params:
        update  -
        context -
    """

    try:
        raise context.error
    except (Unauthorized, BadRequest):
        pass
        # remove update.message.chat_id from conversation list
    except TimedOut:
        pass
        # handle slow connection problems
    except NetworkError:
        pass
        # handle other connection problems
    except ChatMigrated:
        pass
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        pass
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "╒═══≼ ᴍᴇɴᴜ ᴏғ「 *{}* 」ᴍᴏᴅᴜʟᴇ: \n".format(HELPABLE[module].__mod_name__)
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="【༶Back༶】", callback_data="help_back"
                            ),
                            InlineKeyboardButton(
                                text="【༶Home༶】", callback_data="shasa_back"
                            ),
                        ]
                    ]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


def shasa_callback_data(update, context):
    query = update.callback_query
    uptime = get_readable_time((time.time() - StartTime))
    if query.data == "shasa_":
        query.message.edit_text(
            text="""ℹ️ ι'м *ѕнαѕα*, α ρσωєяfυℓ gяσυρ мαиαgємєит вσт вυιℓт тσ нєℓρ уσυ мαиαgє уσυя gяσυρ єαѕιℓу.
        ❍ 💜[Owner](https://t.me/Simpleboy786)💜
        ❍ 🧡[Updates](https://t.me/Shasa_News)🧡
        ❍ 🤍[Suppσrt](https://t.me/joinchat/P8HIdXOL8V9iNjRh)🤍
        ❍ 💚[LionZUb](https://t.me/LionXSupport)💚
        ❍ ❤️[ChatGrp](https://t.me/TotalNadaniya)❤️
        ✨[Vc Player Help](https://telegra.ph/Shasa-Music-08-15)✨""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="•༶Bᴀᴄᴋ༶•", callback_data="shasa_back")]]
            ),
        )
    elif query.data == "shasa_basichelp":
        query.message.edit_text(
            text=f"*Here's basic Help regarding* *How to use Me?*"
            f"\n\n• Firstly Add {dispatcher.bot.first_name} to your group by pressing [here](http://t.me/{dispatcher.bot.username}?startgroup=true)\n"
            f"\n• After adding promote me manually with full rights for faster experience.\n"
            f"\n• Than send `/admincache@Shasa_RoBot` in that chat to refresh admin list in My database.\n"
            f"\n\n*All done now use below given button's to know about use!*\n"
            f"",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="ᴀᴅᴍɪɴ", callback_data="shasa_admin"),
                        InlineKeyboardButton(text="ɴᴏᴛᴇs", callback_data="shasa_notes"),
                    ],
                    [
                        InlineKeyboardButton(
                            text="sᴜᴘᴘᴏʀᴛ", callback_data="shasa_support"
                        ),
                        InlineKeyboardButton(
                            text="ᴄʀᴇᴅɪᴛ", callback_data="shasa_credit"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="•༶Bᴀᴄᴋ༶•", callback_data="shasa_back"
                        ),
                    ],
                ]
            ),
        )
    elif query.data == "shasa_admin":
        query.message.edit_text(
            text=f"*Let's make your group bit effective now*"
            f"\nCongragulations, Miss Shasa now ready to manage your group."
            f"\n\n*Admin Tools*"
            f"\nBasic Admin tools help you to protect and powerup your group."
            f"\nYou can ban members, Kick members, Promote someone as admin through commands of bot."
            f"\n\n*Welcome*"
            f"\nLets set a welcome message to welcome new users coming to your group."
            f"send `/setwelcome [message]` to set a welcome message!",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="•༶Bᴀᴄᴋ༶•", callback_data="shasa_basichelp"
                        )
                    ]
                ]
            ),
        )

    elif query.data == "shasa_notes":
        query.message.edit_text(
            text=f"<b> Setting up notes</b>"
            f"\nYou can save message/media/audio or anything as notes"
            f"\nto get a note simply use # at the beginning of a word"
            f"\n\nYou can also set buttons for notes and filters (refer help menu)",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="•༶Bᴀᴄᴋ༶•", callback_data="shasa_basichelp"
                        )
                    ]
                ]
            ),
        )
    elif query.data == "shasa_support":
        query.message.edit_text(
            text="* Shasa support chats*" "\nJoin Support Group/Channel",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="ᴀʙᴏᴜᴛ", url="t.me/Shasa_News"),
                        InlineKeyboardButton(
                            text="ᴠᴄ ʜᴇʟᴘ", url="https://telegra.ph/Shasa-Music-08-15"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="sᴜᴘᴘᴏʀᴛ", url=f"https://telegram.dog/{SUPPORT_CHAT}"
                        ),
                        InlineKeyboardButton(
                            text="ᴜᴘᴅᴀᴛᴇs", url="https://t.me/LionXupdates"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="•༶Bᴀᴄᴋ༶•", callback_data="shasa_basichelp"
                        ),
                    ],
                ]
            ),
        )
    elif query.data == "shasa_credit":
        query.message.edit_text(
            text=f"<b> SHASA DEV'S</b>\n"
            f"\nHere Some Developers Helping in Making The Shasa RoBot",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="ᴅᴇᴠ", url="t.me/simpleboy786"),
                        InlineKeyboardButton(
                            text="ɢɪᴛʜᴜʙ", url="https://github.com/MdNoor786"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="ᴅᴇᴠ²", url="https://t.me/Copyless786"
                        ),
                        InlineKeyboardButton(
                            text="ʀᴇᴅʟɪᴏɴ", url="https://t.me/Shasa_News/12"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="•༶Bᴀᴄᴋ༶•", callback_data="shasa_basichelp"
                        ),
                    ],
                ]
            ),
        )
    elif query.data == "shasa_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
            PM_START_TEXT.format(
                escape_markdown(context.bot.first_name),
                escape_markdown(first_name),
                escape_markdown(uptime),
                sql.num_users(),
                sql.num_chats(),
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            disable_web_page_preview=False,
        )


@typing_action
def get_help(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_photo(
            HELP_IMG,
            HELP_MSG,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Open In Private Chat",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            " 〔 *{}* 〕\n".format(HELPABLE[module].__mod_name__)
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="[•༶Bᴀᴄᴋ༶•]", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    elif CHAT_SETTINGS:
        chat_name = dispatcher.bot.getChat(chat_id).title
        dispatcher.bot.send_message(
            user_id,
            text="Which module would you like to check {}'s settings for?".format(
                chat_name
            ),
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
            ),
        )
    else:
        dispatcher.bot.send_message(
            user_id,
            "Seems like there aren't any chat settings available :'(\nSend this "
            "in a group chat you're admin in to find its current settings!",
            parse_mode=ParseMode.MARKDOWN,
        )


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type == chat.PRIVATE:
        send_settings(chat.id, user.id, True)

    elif is_user_admin(chat, user.id):
        text = "Click here to get this chat's settings, as well as yours."
        msg.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Settings",
                            url="t.me/{}?start=stngs_{}".format(
                                context.bot.username, chat.id
                            ),
                        )
                    ]
                ]
            ),
        )
    else:
        text = "Click here to check your settings."


def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1902787452 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(
                f"@{SUPPORT_CHAT}",
                f"I Am Ready To Work [{GROUP_START_IMG}]",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!",
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = DisableAbleCommandHandler("test", test, run_async=True)
    start_handler = DisableAbleCommandHandler("start", start, run_async=True)

    help_handler = DisableAbleCommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_.*", run_async=True
    )

    settings_handler = DisableAbleCommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    data_callback_handler = CallbackQueryHandler(
        shasa_callback_data, pattern=r"shasa_", run_async=True
    )
    donate_handler = DisableAbleCommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(data_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info(
            f"Shasa started, Using long polling. | BOT: [@{dispatcher.bot.username}]"
        )
        updater.start_polling(
            timeout=15,
            read_latency=4,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


try:
    ubot.start()
except BaseException:
    print("Userbot Error! Have you added a STRING_SESSION in deploying??")
    sys.exit(1)

if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
    idle()
