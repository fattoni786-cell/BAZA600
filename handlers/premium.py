from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from config import (
    PREMIUM_PLANS,
    PREMIUM_PROMO_CODES,
    PREMIUM_PROMO_DAYS,
    PREMIUM_PROMO_MAX_REDEEMS,
)
from handlers.start import main_menu_text, start_keyboard
from states.premium import PremiumPromoFlow
from utils.access import premium_status_text
from utils.admin_notify import notify_admins
from utils.analytics import track_event
from utils.db import (
    count_promo_code_redemptions,
    has_redeemed_promo_code,
    record_promo_code_redemption,
)
from utils.ui import replace_screen
from utils.users import activate_premium, record_premium_payment

router = Router()


@router.message(Command("paysupport"))
async def paysupport(message: Message):
    await message.answer(
        "По вопросам оплаты Premium напиши администратору бота:\n@Mister600"
    )


def plan_button_text(user: dict, plan: dict) -> str:
    icon_by_days = {
        6: "🎓",
        60: "🕶",
        600: "👑",
    }
    badge = " • Традиционно" if plan["days"] == 600 else ""
    icon = icon_by_days.get(plan["days"], "💳")
    return f"{icon} {plan['days']} дней • {plan['price_xtr']} Stars{badge}"


def premium_keyboard(user: dict) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text=plan_button_text(user, plan),
                callback_data=f"premium_buy:{payload}",
            )
        ]
        for payload, plan in PREMIUM_PLANS.items()
    ]
    inline_keyboard.append(
        [InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="premium_promo")]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def premium_info_text(user: dict) -> str:
    lines = [
        premium_status_text(user),
        "",
        "Преимущества:",
        "• 15 персональных подборов в день",
        "• Отдельные подборки контента",
        "• Безлимитное избранное",
        "• Премиальная реакция подписчика базы💼 на контент",
        "",
        "Тарифы:",
    ]

    for plan in PREMIUM_PLANS.values():
        if plan["days"] == 600:
            lines.append(
                f"• 👑 <b>{plan['days']} дней</b> — <b>{plan['price_xtr']} Stars</b> <i>Традиционно</i>"
            )
        elif plan["days"] == 60:
            lines.append(
                f"• 🕶 <b>{plan['days']} дней</b> — <b>{plan['price_xtr']} Stars</b>"
            )
        elif plan["days"] == 6:
            lines.append(
                f"• 🎓 <b>{plan['days']} дней</b> — <b>{plan['price_xtr']} Stars</b>"
            )
        else:
            lines.append(
                f"• <b>{plan['days']} дней</b> — <b>{plan['price_xtr']} Stars</b>"
            )

    return "\n".join(lines)


def normalize_promo_code(code: str) -> str:
    return code.strip().upper()


async def activate_promo_for_user(message: Message, user: dict, raw_code: str):
    code = normalize_promo_code(raw_code)

    if not code:
        await message.answer("Напиши промокод одним сообщением.")
        return

    if not PREMIUM_PROMO_CODES:
        await message.answer(
            "Промокоды пока не настроены. БАЗА смотрит на пустую полку и делает вид, что так задумано."
        )
        return

    if code not in PREMIUM_PROMO_CODES:
        await message.answer(
            "Промокод не подошёл. Либо опечатка, либо тайный клуб сегодня без тебя."
        )
        return

    if has_redeemed_promo_code(user["telegram_id"], code):
        await message.answer(
            "Этот промокод ты уже активировал. Второй раз БАЗА делает вид, что не слышит."
        )
        return

    if PREMIUM_PROMO_MAX_REDEEMS > 0:
        redeemed_count = count_promo_code_redemptions(code)
        if redeemed_count >= PREMIUM_PROMO_MAX_REDEEMS:
            await message.answer(
                "Лимит активаций этого промокода уже закончился. Промокод был хорош, но смертен."
            )
            return

    premium_until = activate_premium(
        telegram_id=user["telegram_id"],
        duration_days=PREMIUM_PROMO_DAYS,
    )
    record_promo_code_redemption(
        user_id=user["telegram_id"],
        code=code,
        premium_until=premium_until,
    )

    track_event(
        user["telegram_id"],
        "premium_promo_activated",
        source=code,
        metadata={"days": PREMIUM_PROMO_DAYS},
    )
    await notify_admins(
        message.bot,
        (
            "🎟 Premium promo activated\n"
            f"User: {user['telegram_id']}\n"
            f"Code: {code}\n"
            f"Days: {PREMIUM_PROMO_DAYS}\n"
            f"Until: {premium_until}"
        ),
    )

    premium_until_text = datetime.fromisoformat(premium_until).strftime("%d.%m.%Y")
    await message.answer(
        (
            "🎟 <b>Промокод принят</b>\n\n"
            f"Premium открыт на <b>{PREMIUM_PROMO_DAYS} дней</b>.\n"
            f"Доступ активен до <b>{premium_until_text}</b>.\n\n"
            "БАЗА официально делает вид, что так и планировала."
        ),
        parse_mode="HTML",
        reply_markup=start_keyboard(),
    )


@router.message(F.text == "💎 Premium")
async def premium_info_button(message: Message, user: dict):
    track_event(user["telegram_id"], "premium_opened", source="bottom_nav")
    await message.answer(
        premium_info_text(user),
        reply_markup=premium_keyboard(user),
        parse_mode="HTML",
    )


@router.message(Command("promo"))
async def promo_command(message: Message, command: CommandObject, user: dict, state: FSMContext):
    code = command.args or ""
    if code:
        await state.clear()
        await activate_promo_for_user(message, user, code)
        return

    await state.set_state(PremiumPromoFlow.waiting_code)
    await message.answer(
        "🎟 <b>Напиши промокод</b>\n\n"
        "Если код настоящий, открою Premium на месяц. Если нет — сделаю вид, что это философский эксперимент.",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "premium_promo")
async def premium_promo(callback: CallbackQuery, user: dict, state: FSMContext):
    await callback.answer()
    await state.set_state(PremiumPromoFlow.waiting_code)
    await replace_screen(
        callback,
        text=(
            "🎟 <b>Напиши промокод</b>\n\n"
            "Одним сообщением. Если всё совпадёт, Premium откроется на месяц."
        ),
    )


@router.message(PremiumPromoFlow.waiting_code, F.text)
async def premium_promo_code(message: Message, user: dict, state: FSMContext):
    await state.clear()
    await activate_promo_for_user(message, user, message.text)


@router.callback_query(F.data == "premium_info")
async def premium_info(callback: CallbackQuery, user: dict):
    track_event(user["telegram_id"], "premium_opened", source="inline")
    await replace_screen(
        callback,
        text=premium_info_text(user),
        reply_markup=premium_keyboard(user),
    )


@router.callback_query(F.data.startswith("premium_buy:"))
async def premium_buy(callback: CallbackQuery, user: dict):
    await callback.answer()

    payload = callback.data.split(":", 1)[1]
    plan = PREMIUM_PLANS.get(payload)

    if not plan:
        await callback.message.answer("Тариф не найден. Попробуй ещё раз.")
        return

    track_event(
        user["telegram_id"],
        "premium_buy_clicked",
        source=payload,
        metadata={"days": plan["days"], "price_xtr": plan["price_xtr"]},
    )

    await callback.message.answer_invoice(
        title=f"Premium на {plan['days']} дней",
        description=(
            "Персональный подбор, premium-подборки и "
            "безлимитное избранное."
        ),
        payload=payload,
        currency="XTR",
        prices=[
            LabeledPrice(
                label=f"Premium {plan['days']} days",
                amount=plan["price_xtr"],
            )
        ],
    )


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    payload = pre_checkout_query.invoice_payload
    plan = PREMIUM_PLANS.get(payload)

    if not plan:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Не удалось определить тариф. Попробуй ещё раз.",
        )
        return

    if pre_checkout_query.currency != "XTR" or pre_checkout_query.total_amount != plan["price_xtr"]:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Сумма платежа не совпала с тарифом. Открой Premium ещё раз.",
        )
        return

    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, user: dict):
    payment = message.successful_payment
    plan = PREMIUM_PLANS.get(payment.invoice_payload)

    if not plan:
        return

    if payment.currency != "XTR" or payment.total_amount != plan["price_xtr"]:
        track_event(
            user["telegram_id"],
            "premium_payment_rejected",
            source=payment.invoice_payload,
            metadata={
                "amount": payment.total_amount,
                "currency": payment.currency,
                "expected_amount": plan["price_xtr"],
            },
        )
        await notify_admins(
            message.bot,
            (
                "⚠️ Premium payment mismatch\n"
                f"User: {user['telegram_id']}\n"
                f"Payload: {payment.invoice_payload}\n"
                f"Amount: {payment.total_amount} {payment.currency}\n"
                f"Expected: {plan['price_xtr']} XTR"
            ),
        )
        await message.answer(
            "Платёж пришёл с неожиданной суммой. Я не активировал Premium автоматически, админ уже получил уведомление."
        )
        return

    premium_until = activate_premium(
        telegram_id=user["telegram_id"],
        duration_days=plan["days"],
    )

    record_premium_payment(
        telegram_id=user["telegram_id"],
        payload=payment.invoice_payload,
        amount=payment.total_amount,
        currency=payment.currency,
        telegram_payment_charge_id=payment.telegram_payment_charge_id,
        provider_payment_charge_id=payment.provider_payment_charge_id,
        premium_until=premium_until,
    )

    track_event(
        user["telegram_id"],
        "premium_paid",
        source=payment.invoice_payload,
        metadata={
            "days": plan["days"],
            "amount": payment.total_amount,
            "currency": payment.currency,
        },
    )
    await notify_admins(
        message.bot,
        (
            "💎 Premium paid\n"
            f"User: {user['telegram_id']}\n"
            f"Plan: {plan['days']} days\n"
            f"Amount: {payment.total_amount} {payment.currency}\n"
            f"Until: {premium_until}"
        ),
    )

    premium_until_text = datetime.fromisoformat(premium_until).strftime("%d.%m.%Y")

    await message.answer(
        (
            "💎 <b>Premium активирован</b>\n\n"
            f"Тариф: <b>{plan['days']} дней</b>\n"
            f"Доступ открыт до <b>{premium_until_text}</b>.\n"
            "Теперь тебе доступны персональный подбор, premium-подборки "
            "и безлимитное избранное."
        ),
        parse_mode="HTML",
        reply_markup=start_keyboard(),
    )

    await message.answer(
        main_menu_text(
            {
                "telegram_id": user["telegram_id"],
                "role": "premium",
                "premium_until": premium_until,
            }
        ),
        parse_mode="HTML",
        reply_markup=start_keyboard(),
    )
