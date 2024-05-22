import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
import numpy_financial as npf
from database import initialize_database, add_user, add_expense, get_user_id, get_expenses, add_category, get_categories, set_fixed_currency_values, get_currency

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

MAIN_MENU, CATEGORY, AMOUNT, AMOUNT_INPUT, RATE_INPUT, YEARS_INPUT, CASHFLOWS_INPUT, NEW_CATEGORY = range(8)

def set_fixed_currency_data():
    set_fixed_currency_values()

def get_currency_info(update: Update, context: CallbackContext) -> None:
    usd = get_currency("Доллар США")
    eur = get_currency("Евро")
    if usd and eur:
        update.message.reply_text(f"Курс валют на сегодня\n USD = {usd[0]} RUB\n EUR = {eur[0]} RUB")
    else:
        update.message.reply_text("Не удалось получить данные о валюте.")
        logger.error("Currency data not found in database.")

def start(update: Update, context: CallbackContext) -> None:
    logger.info("Вызвана команда /start")
    username = update.message.from_user.username
    add_user(username)
    update.message.reply_text(f'Добро пожаловать, {username}! Вы зарегистрированы.')
    help_command(update, context)

def help_command(update: Update, context: CallbackContext) -> None:
    logger.info("Вызвана команда /help")
    help_text = (
        "Доступные команды:\n"
        "/credit - Расчет ежемесячного платежа по кредиту\n"
        "/deposit - Расчет будущей суммы депозита\n"
        "/npv - Расчет чистой приведенной стоимости (NPV)\n"
        "/irr - Расчет внутренней нормы доходности (IRR)\n"
        "/expense - Управление расходами\n"
        "/currency - Просмотр курсов валют\n"
    )
    update.message.reply_text(help_text)

def credit_command(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите сумму кредита:')
    return AMOUNT_INPUT

def credit_amount_input(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['amount'] = float(update.message.text)
        update.message.reply_text('Введите процентную ставку:')
        return RATE_INPUT
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение суммы кредита.')
        return AMOUNT_INPUT

def credit_rate_input(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['rate'] = float(update.message.text)
        update.message.reply_text('Введите длительность кредита в годах:')
        return YEARS_INPUT
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение процентной ставки.')
        return RATE_INPUT

def credit_years_input(update: Update, context: CallbackContext) -> int:
    try:
        years = float(update.message.text)
        amount = context.user_data['amount']
        rate = context.user_data['rate']
        monthly_payment = npf.pmt(rate / 12 / 100, years * 12, -amount)
        update.message.reply_text(f'Ежемесячный платеж: {monthly_payment:.2f} руб.')
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение срока кредита.')
        return YEARS_INPUT
    return ConversationHandler.END

def deposit_command(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите начальную сумму депозита:')
    return AMOUNT_INPUT

def deposit_amount_input(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['initial_amount'] = float(update.message.text)
        update.message.reply_text('Введите процентную ставку:')
        return RATE_INPUT
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение начальной суммы.')
        return AMOUNT_INPUT

def deposit_rate_input(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['rate'] = float(update.message.text)
        update.message.reply_text('Введите срок депозита в годах:')
        return YEARS_INPUT
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение процентной ставки.')
        return RATE_INPUT

def deposit_years_input(update: Update, context: CallbackContext) -> int:
    try:
        years = float(update.message.text)
        initial_amount = context.user_data['initial_amount']
        rate = context.user_data['rate']
        future_value = initial_amount * (1 + rate / 100) ** years
        update.message.reply_text(f'Будущая сумма: {future_value:.2f} руб.')
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение длительности    депозита.')
        return YEARS_INPUT
    return ConversationHandler.END

def npv_command(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите процентную ставку для NPV:')
    return RATE_INPUT

def npv_rate_input(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data['rate'] = float(update.message.text)
        update.message.reply_text('Введите денежные потоки через запятую:')
        return CASHFLOWS_INPUT
    except ValueError:
        update.message.reply_text('Ошибка: введите числовое значение процентной ставки.')
        return RATE_INPUT

def npv_cashflows_input(update: Update, context: CallbackContext) -> int:
    try:
        cashflows = list(map(float, update.message.text.split(',')))
        rate = context.user_data['rate']
        npv_value = npf.npv(rate / 100, cashflows)
        update.message.reply_text(f'Чистая приведенная стоимость (NPV): {npv_value:.2f} руб.')
    except ValueError:
        update.message.reply_text('Ошибка: введите денежные потоки через запятую.')
        return CASHFLOWS_INPUT
    return ConversationHandler.END

def irr_command(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Введите денежные потоки через запятую:')
    return CASHFLOWS_INPUT

def irr_cashflows_input(update: Update, context: CallbackContext) -> int:
    try:
        cashflows = list(map(float, update.message.text.split(',')))
        irr_value = npf.irr(cashflows) * 100
        update.message.reply_text(f'Внутренняя норма доходности (IRR): {irr_value:.2f}%')
    except ValueError:
        update.message.reply_text('Ошибка: введите денежные потоки через запятую.')
        return CASHFLOWS_INPUT
    return ConversationHandler.END

def start_expense(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Выберите действие:\n'
        '1. Добавить категорию\n'
        '2. Добавить расходы\n'
        '3. Посмотреть расходы по всем категориям\n'
        'Введите /out для выхода'
    )
    return MAIN_MENU

def expense_main_menu(update: Update, context: CallbackContext) -> int:
    choice = update.message.text
    if choice == '1':
        update.message.reply_text('Введите название новой категории:')
        return NEW_CATEGORY
    elif choice == '2':
        return show_categories(update, context)
    elif choice == '3':
        username = update.message.from_user.username
        user_id = get_user_id(username)
        expenses = get_expenses(user_id)
        categories = get_categories(user_id)
        expenses_dict = {category: 0 for category in categories}
        for category, amount in expenses:
            expenses_dict[category] = amount
        expenses_text = "Ваши расходы по категориям:\n"
        for category, amount in expenses_dict.items():
            expenses_text += f"{category}: {amount:.2f} руб.\n"
        update.message.reply_text(expenses_text)
        return MAIN_MENU
    else:
        update.message.reply_text('Неверный выбор. Пожалуйста, выберите действие из списка.')
        return MAIN_MENU

def add_new_category(update: Update, context: CallbackContext) -> int:
    category = update.message.text
    username = update.message.from_user.username
    user_id = get_user_id(username)
    add_category(user_id, category)
    update.message.reply_text(f'Категория "{category}" добавлена.')
    return MAIN_MENU

def show_categories(update: Update, context: CallbackContext) -> int:
    username = update.message.from_user.username
    user_id = get_user_id(username)
    categories = get_categories(user_id)
    if not categories:
        update.message.reply_text('У вас нет категорий. Пожалуйста, добавьте категорию.')
        return MAIN_MENU

    categories_text = "Ваши категории:\n" + "\n".join(categories)
    update.message.reply_text(categories_text)
    update.message.reply_text('Пожалуйста, выберите категорию расхода:')
    return CATEGORY

def set_category(update: Update, context: CallbackContext) -> int:
    category = update.message.text
    username = update.message.from_user.username
    user_id = get_user_id(username)
    categories = get_categories(user_id)
    if category in categories:
        context.user_data['category'] = category
        update.message.reply_text(f'Вы выбрали категорию: {category}. Введите сумму расхода:')
        return AMOUNT
    else:
        update.message.reply_text('Неверная категория. Пожалуйста, выберите категорию из списка.')
        return CATEGORY

def set_amount(update: Update, context: CallbackContext) -> int:
    try:
        amount = float(update.message.text)
        username = update.message.from_user.username
        user_id = get_user_id(username)
        category = context.user_data['category']
        if user_id:
            add_expense(user_id, category, amount)
            update.message.reply_text(f'Расход добавлен: {category} - {amount:.2f} руб.')
        else:
            update.message.reply_text('Ошибка: пользователь не найден.')
    except ValueError:
        update.message.reply_text('Ошибка: неверный формат суммы. Пожалуйста, введите числовое значение.')
        return AMOUNT
    return MAIN_MENU

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Вы вышли из expense.')
    return ConversationHandler.END

def main() -> None:
    initialize_database()

    set_fixed_currency_data()

    updater = Updater(token = '6458313589:AAEdQ67R1VArW61kukpOTcTlv0o6u5MEQSs', use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("currency", get_currency_info))

    credit_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('credit', credit_command)],
        states={
            AMOUNT_INPUT: [MessageHandler(Filters.text & ~Filters.command, credit_amount_input)],
            RATE_INPUT: [MessageHandler(Filters.text & ~Filters.command, credit_rate_input)],
            YEARS_INPUT: [MessageHandler(Filters.text & ~Filters.command, credit_years_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(credit_conv_handler)

    deposit_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('deposit', deposit_command)],
        states={
            AMOUNT_INPUT: [MessageHandler(Filters.text & ~Filters.command, deposit_amount_input)],
            RATE_INPUT: [MessageHandler(Filters.text & ~Filters.command, deposit_rate_input)],
            YEARS_INPUT: [MessageHandler(Filters.text & ~Filters.command, deposit_years_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(deposit_conv_handler)

    npv_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('npv', npv_command)],
        states={
            RATE_INPUT: [MessageHandler(Filters.text & ~Filters.command, npv_rate_input)],
            CASHFLOWS_INPUT: [MessageHandler(Filters.text & ~Filters.command, npv_cashflows_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(npv_conv_handler)

    irr_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('irr', irr_command)],
        states={
            CASHFLOWS_INPUT: [MessageHandler(Filters.text & ~Filters.command, irr_cashflows_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(irr_conv_handler)

    expense_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('expense', start_expense)],
        states={
            MAIN_MENU: [MessageHandler(Filters.text & ~Filters.command, expense_main_menu)],
            NEW_CATEGORY: [MessageHandler(Filters.text & ~Filters.command, add_new_category)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, set_category)],
            AMOUNT: [MessageHandler(Filters.text & ~Filters.command, set_amount)],
        },
        fallbacks=[CommandHandler('out', cancel)]
    )
    dispatcher.add_handler(expense_conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
