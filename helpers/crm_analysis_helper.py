from __future__ import annotations

import re
from datetime import datetime, timedelta
from urllib.parse import quote

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import (
    CRMWhatsAppLog,
    DiscountRule,
    Patient,
    PatientContactPreference,
    PatientFollowup,
    PatientManualTag,
    Visit,
    VoucherPatientTarget,
    VoucherUsage,
)

try:
    from database import Service
except Exception:
    Service = None


FOLLOWUP_STATUSES = {
    "pending": "Belum dihubungi",
    "contacted": "Sudah dihubungi",
    "waiting": "Menunggu respon",
    "menunggu_respon": "Menunggu respon",
    "booked": "Sudah booking",
    "inactive": "Tidak aktif",
    "perlu_follow_up": "Perlu follow-up",
}

FOLLOWUP_OUTCOMES = {
    "": "Belum ada hasil follow-up",
    "no_response": "Tidak Dibalas",
    "replied": "Pasien membalas",
    "asked_schedule": "Minta Jadwal",
    "booked": "Sudah booking",
    "not_interested": "Tidak Berminat",
    "contact_later": "Hubungi Nanti",
    "invalid_number": "Nomor Tidak Valid",
}

DEFAULT_MANUAL_TAGS = [
    ("vip", "VIP"),
    ("sensitif-harga", "Sensitif Harga"),
    ("perlu-follow-up", "Perlu Follow-up"),
    ("jangan-promo", "Jangan Promo"),
    ("jangan-dihubungi", "Jangan Dihubungi"),
    ("suka-jadwal-pagi", "Suka Jadwal Pagi"),
    ("suka-jadwal-sore", "Suka Jadwal Sore"),
    ("terapis-perempuan", "Terapis Perempuan"),
    ("terapis-laki-laki", "Terapis Laki-laki"),
]

MESSAGE_TEMPLATES = {
    "kontrol": "Kontrol rutin",
    "routine_polite": "Kontrol sopan",
    "routine_warm": "Kontrol hangat",
    "routine_short": "Kontrol singkat",
    "routine_neutral": "Kontrol netral",
    "routine_friendly": "Kontrol santai",
    "reaktivasi": "Aktifkan kembali",
    "reactivation_polite": "Aktifkan kembali",
    "reactivation_neutral": "Aktifkan kembali netral",
    "promo": "Promo / paket",
    "promo_polite": "Promo / paket",
    "promo_neutral": "Promo netral",
    "aftercare": "Aftercare",
    "aftercare_polite": "Aftercare",
    "aftercare_neutral": "Aftercare netral",
}

WHATSAPP_TEMPLATE_ALIASES = {
    "routine": "routine",
    "kontrol": "routine",
    "routine_polite": "routine_polite",
    "kontrol_sopan": "routine_polite",
    "routine_warm": "routine_warm",
    "kontrol_hangat": "routine_warm",
    "routine_short": "routine_short",
    "kontrol_singkat": "routine_short",
    "routine_neutral": "routine_neutral",
    "kontrol_netral": "routine_neutral",
    "routine_friendly": "routine_friendly",
    "kontrol_santai": "routine_friendly",
    "reactivation": "reactivation",
    "reaktivasi": "reactivation",
    "reactivation_polite": "reactivation_polite",
    "reaktivasi_sopan": "reactivation_polite",
    "reactivation_neutral": "reactivation_neutral",
    "reaktivasi_netral": "reactivation_neutral",
    "promo": "promo",
    "promo_polite": "promo_polite",
    "promo_neutral": "promo_neutral",
    "aftercare": "aftercare",
    "aftercare_polite": "aftercare_polite",
    "aftercare_neutral": "aftercare_neutral",
}

WHATSAPP_TEMPLATE_LABELS = {
    "routine": "Kontrol rutin",
    "routine_polite": "Kontrol sopan",
    "routine_warm": "Kontrol hangat",
    "routine_short": "Kontrol singkat",
    "routine_neutral": "Kontrol netral",
    "routine_friendly": "Kontrol santai",
    "reactivation": "Aktifkan kembali",
    "reactivation_polite": "Aktifkan kembali",
    "reactivation_neutral": "Aktifkan kembali netral",
    "promo": "Promo / paket",
    "promo_polite": "Promo / paket",
    "promo_neutral": "Promo netral",
    "aftercare": "Aftercare",
    "aftercare_polite": "Aftercare",
    "aftercare_neutral": "Aftercare netral",
}

WHATSAPP_LOCK_DAYS = {
    "routine": 7,
    "routine_polite": 7,
    "routine_warm": 7,
    "routine_short": 7,
    "routine_neutral": 7,
    "routine_friendly": 7,
    "reactivation": 7,
    "reactivation_polite": 7,
    "reactivation_neutral": 7,
    "promo": 7,
    "promo_polite": 7,
    "promo_neutral": 7,
}

WHATSAPP_LOG_STATUSES = {
    "drafted": "Draft",
    "opened": "Dibuka",
    "confirmed_sent": "Terkonfirmasi terkirim",
    "skipped_preference": "Diblokir preferensi",
    "skipped_send_lock": "Diblokir jeda kirim",
    "failed": "Gagal",
}

CRM_CLINIC_NAME = "Klinik"


def _clinic_profile():
    try:
        from settings import AppSettings
        profile = AppSettings().get_clinic_profile()
    except Exception:
        profile = {}
    clinic_name = str(profile.get("clinic_name") or CRM_CLINIC_NAME).strip()
    clinic_address = str(profile.get("clinic_address") or "").strip()
    clinic_phone = str(profile.get("clinic_phone") or "").strip()
    clinic_email = str(profile.get("clinic_email") or "").strip()
    clinic_website = str(profile.get("clinic_website") or "").strip()
    admin_label = str(profile.get("admin_label") or "Admin Klinik").strip().rstrip(",")
    return {
        "clinic_name": clinic_name,
        "clinic_address": clinic_address,
        "clinic_phone": clinic_phone,
        "clinic_email": clinic_email,
        "clinic_website": clinic_website,
        "admin_label": admin_label,
    }


def _clinic_display(profile):
    address = profile.get("clinic_address") or ""
    if address:
        return f"{profile['clinic_name']} ({address})"
    return profile["clinic_name"]


def _clinic_contact_footer(profile):
    contacts = []
    if profile.get("clinic_phone"):
        contacts.append(f"Telp/WA: {profile['clinic_phone']}")
    if profile.get("clinic_email"):
        contacts.append(f"Email: {profile['clinic_email']}")
    if profile.get("clinic_website"):
        contacts.append(f"Website: {profile['clinic_website']}")
    if not contacts:
        return ""
    return "\n\n" + " | ".join(contacts)


def _date_text(value):
    if not value:
        return ""
    return value.strftime("%Y-%m-%d")


def _friendly_date(value):
    if not value:
        return ""
    return value.strftime("%d/%m/%Y")


def _format_currency(value):
    return f"Rp {int(float(value or 0)):,}".replace(",", ".")


def _format_discount_value(rule):
    if not rule:
        return ""
    value = float(rule.discount_value or 0)
    if rule.discount_type == "percent":
        return f"{value:g}%"
    return _format_currency(value)


def _format_voucher_period(rule):
    if not rule:
        return ""
    start = rule.start_date.strftime("%Y-%m-%d") if rule.start_date else ""
    end = rule.end_date.strftime("%Y-%m-%d") if rule.end_date else ""
    if start and end:
        return f"berlaku {start} s/d {end}"
    if end:
        return f"berlaku sampai {end}"
    if start:
        return f"berlaku mulai {start}"
    return ""


def _rule_date_active(rule, now=None):
    now = now or datetime.now()
    if rule.start_date and now < rule.start_date:
        return False
    if rule.end_date:
        end_dt = rule.end_date
        if end_dt.time() == datetime.min.time():
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        if now > end_dt:
            return False
    return True


def _voucher_limit_active(session, rule, patient_id):
    total_limit = int(rule.usage_limit or 0)
    if total_limit > 0:
        total_used = session.query(func.count(VoucherUsage.id)).filter(VoucherUsage.discount_rule_id == rule.id).scalar() or 0
        if total_used >= total_limit:
            return False
    per_patient_limit = int(rule.per_patient_limit or 0)
    if per_patient_limit > 0:
        patient_used = (
            session.query(func.count(VoucherUsage.id))
            .filter(VoucherUsage.discount_rule_id == rule.id, VoucherUsage.patient_id == patient_id)
            .scalar()
            or 0
        )
        if patient_used >= per_patient_limit:
            return False
    return True


def _voucher_payload(session, rule, patient_id):
    target_ids = [
        row.patient_id
        for row in session.query(VoucherPatientTarget).filter(VoucherPatientTarget.discount_rule_id == rule.id).all()
    ]
    usage_count = session.query(func.count(VoucherUsage.id)).filter(VoucherUsage.discount_rule_id == rule.id).scalar() or 0
    is_special = bool(target_ids)
    return {
        "id": rule.id,
        "name": rule.name,
        "voucher_code": rule.voucher_code or "",
        "discount_type": rule.discount_type,
        "discount_value": float(rule.discount_value or 0),
        "discount_label": _format_discount_value(rule),
        "start_date": rule.start_date.strftime("%Y-%m-%d") if rule.start_date else "",
        "end_date": rule.end_date.strftime("%Y-%m-%d") if rule.end_date else "",
        "period_label": _format_voucher_period(rule),
        "usage_limit": rule.usage_limit,
        "per_patient_limit": rule.per_patient_limit,
        "usage_count": int(usage_count or 0),
        "is_special": is_special,
        "is_target_patient": (not is_special) or int(patient_id) in target_ids,
    }


def get_patient_active_vouchers(session, patient_id, include_general=True):
    patient_id = int(patient_id)
    if not session.get(Patient, patient_id):
        raise ValueError("Pasien tidak ditemukan.")
    rules = (
        session.query(DiscountRule)
        .filter(DiscountRule.type == "voucher", DiscountRule.is_active == True)
        .order_by(DiscountRule.priority.asc(), DiscountRule.created_at.asc())
        .all()
    )
    special = []
    general = []
    for rule in rules:
        if not _rule_date_active(rule) or not _voucher_limit_active(session, rule, patient_id):
            continue
        payload = _voucher_payload(session, rule, patient_id)
        if payload["is_special"] and payload["is_target_patient"]:
            special.append(payload)
        elif include_general and not payload["is_special"]:
            general.append(payload)
    return {"special": special, "general": general, "has_special": bool(special)}


def get_voucher_for_crm_message(session, patient_id, voucher_rule_id, allow_general=False):
    if not voucher_rule_id:
        return None
    rule = session.get(DiscountRule, int(voucher_rule_id))
    if not rule or rule.type != "voucher" or not rule.is_active:
        raise ValueError("Voucher tidak ditemukan atau tidak aktif.")
    if not _rule_date_active(rule) or not _voucher_limit_active(session, rule, int(patient_id)):
        raise ValueError("Voucher sudah tidak berlaku atau batas pemakaian habis.")
    payload = _voucher_payload(session, rule, int(patient_id))
    if payload["is_special"] and not payload["is_target_patient"]:
        raise ValueError("Voucher ini bukan untuk pasien tersebut.")
    if not payload["is_special"] and not allow_general:
        raise ValueError("Voucher umum perlu konfirmasi sebelum dimasukkan ke pesan CRM.")
    return payload


def _voucher_message_block(voucher):
    if not voucher:
        return ""
    parts = [f"Voucher khusus: {voucher.get('name') or 'Voucher'}"]
    if voucher.get("voucher_code"):
        parts.append(f"Kode: {voucher['voucher_code']}")
    if voucher.get("discount_label"):
        parts.append(f"Diskon: {voucher['discount_label']}")
    if voucher.get("period_label"):
        parts.append(voucher["period_label"])
    return "\n\n" + " | ".join(parts)


def _slugify(value):
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "tag"


def get_manual_tag_options(session=None):
    options = {value: label for value, label in DEFAULT_MANUAL_TAGS}
    if session is not None:
        try:
            rows = session.query(PatientManualTag.value, PatientManualTag.label).distinct().all()
            for value, label in rows:
                if value:
                    options[str(value)] = str(label or value)
        except Exception:
            pass
    return [
        {"type": "manual", "value": value, "label": label}
        for value, label in sorted(options.items(), key=lambda item: item[1].lower())
    ]


def _service_tag_from_name(name):
    clean_name = str(name or "").strip()
    if not clean_name:
        return None
    return {
        "type": "service",
        "label": f"Layanan: {clean_name}",
        "value": _slugify(clean_name),
    }


def _patient_service_tags(patient):
    tags = {}
    for visit in patient.visits or []:
        service_name = (
            visit.service.name
            if getattr(visit, "service", None) and getattr(visit.service, "name", None)
            else visit.service_name
        )
        tag = _service_tag_from_name(service_name)
        if tag:
            tags[tag["value"]] = tag
    return sorted(tags.values(), key=lambda item: item["label"].lower())


def _active_service_tags(session):
    if Service is None:
        return []
    try:
        query = session.query(Service.name)
        if hasattr(Service, "is_active"):
            query = query.filter(Service.is_active == True)
        rows = query.order_by(Service.name.asc()).all()
    except Exception:
        return []

    tags = {}
    for row in rows:
        try:
            service_name = row[0]
        except Exception:
            service_name = getattr(row, "name", row)
        tag = _service_tag_from_name(service_name)
        if tag:
            tags[tag["value"]] = tag
    return sorted(tags.values(), key=lambda item: item["label"].lower())


def get_patient_tags(session, patient_id):
    patient = (
        session.query(Patient)
        .options(joinedload(Patient.visits).joinedload(Visit.service))
        .filter(Patient.id == int(patient_id))
        .first()
    )
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")

    manual_rows = (
        session.query(PatientManualTag)
        .filter(PatientManualTag.patient_id == patient.id)
        .order_by(PatientManualTag.label.asc())
        .all()
    )
    manual_tags = [
        {"type": "manual", "label": row.label, "value": row.value}
        for row in manual_rows
    ]
    return _patient_service_tags(patient) + manual_tags


def save_patient_tags(session, patient_id, tags):
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")

    normalized = []
    seen = set()
    for raw in tags or []:
        if isinstance(raw, dict) and raw.get("type") not in ("", None, "manual"):
            continue
        label = str((raw.get("label") if isinstance(raw, dict) else raw) or "").strip()
        value = str((raw.get("value") if isinstance(raw, dict) else "") or "").strip()
        if not value:
            value = _slugify(label)
        if not label:
            label = value.replace("-", " ").title()
        if not value or value in seen:
            continue
        normalized.append((value, label))
        seen.add(value)

    session.query(PatientManualTag).filter(PatientManualTag.patient_id == patient.id).delete()
    for value, label in normalized:
        session.add(PatientManualTag(patient_id=patient.id, value=value, label=label))
    session.commit()
    return get_patient_tags(session, patient.id)


def get_patient_contact_preference(session, patient_id):
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")
    pref = (
        session.query(PatientContactPreference)
        .filter(PatientContactPreference.patient_id == patient.id)
        .first()
    )
    if not pref:
        return {
            "boleh_reminder_kontrol": True,
            "boleh_promo": True,
            "jangan_dihubungi": False,
            "catatan_kontak": "",
        }
    return {
        "boleh_reminder_kontrol": bool(pref.boleh_reminder_kontrol),
        "boleh_promo": bool(pref.boleh_promo),
        "jangan_dihubungi": bool(pref.jangan_dihubungi),
        "catatan_kontak": pref.catatan_kontak or "",
    }


def save_patient_contact_preference(session, patient_id, data):
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")
    pref = (
        session.query(PatientContactPreference)
        .filter(PatientContactPreference.patient_id == patient.id)
        .first()
    )
    if not pref:
        pref = PatientContactPreference(patient_id=patient.id)
        session.add(pref)
    pref.boleh_reminder_kontrol = str(data.get("boleh_reminder_kontrol", "true")).lower() in {"1", "true", "yes", "on"}
    pref.boleh_promo = str(data.get("boleh_promo", "true")).lower() in {"1", "true", "yes", "on"}
    pref.jangan_dihubungi = str(data.get("jangan_dihubungi", "false")).lower() in {"1", "true", "yes", "on"}
    pref.catatan_kontak = str(data.get("catatan_kontak") or "").strip()
    pref.updated_at = datetime.now()
    session.commit()
    return get_patient_contact_preference(session, patient.id)


def normalize_wa_number(phone):
    digits = re.sub(r"\D+", "", str(phone or ""))
    if not digits:
        raise ValueError("Nomor WhatsApp pasien kosong.")
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    elif digits.startswith("62"):
        digits = digits
    if len(digits) < 10:
        raise ValueError("Nomor WhatsApp terlalu pendek.")
    if not re.fullmatch(r"62[1-9]\d{7,13}", digits):
        raise ValueError("Nomor WhatsApp tidak valid. Gunakan nomor Indonesia yang aktif.")
    return digits


def validate_wa_number(phone):
    return normalize_wa_number(phone)


def build_whatsapp_url(phone, message):
    normalized_phone = normalize_wa_number(phone)
    text = normalize_whatsapp_message(message)
    if not text:
        raise ValueError("Pesan WhatsApp tidak boleh kosong.")
    return f"https://wa.me/{normalized_phone}?text={quote(text)}"


def normalize_whatsapp_message(message):
    text = str(message or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""
    text = re.sub(r"\n{3,}", "\n\n", text)
    if "\n" in text:
        return text

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9A-ZÀ-Þ])", text)
    paragraphs = [sentence.strip() for sentence in sentences if sentence.strip()]
    if len(paragraphs) <= 1:
        return text
    return "\n\n".join(paragraphs)


def _latest_followups(session):
    followups = (
        session.query(PatientFollowup)
        .order_by(PatientFollowup.patient_id.asc(), PatientFollowup.created_at.desc(), PatientFollowup.id.desc())
        .all()
    )
    latest = {}
    for followup in followups:
        latest.setdefault(followup.patient_id, followup)
    return latest


def _followup_due(followup, today):
    if not followup or not followup.follow_up_date:
        return "", ""
    status = followup.status or "pending"
    followup_date = followup.follow_up_date.date()
    if followup_date < today and status not in {"booked", "inactive"}:
        return "overdue", "Terlambat"
    if followup_date == today and status not in {"booked", "inactive"}:
        return "today", "Hari ini"
    if followup_date > today:
        return "scheduled", "Terjadwal"
    return "", ""


def _is_high_value(total_visits, total_spent):
    return total_spent >= 1_000_000 or total_visits >= 8


def _manual_tag_payload(rows):
    return [
        {"type": "manual", "label": row.label, "value": row.value}
        for row in sorted(rows or [], key=lambda item: str(item.label or "").lower())
    ]


def _contact_pref_payload(pref):
    if not pref:
        return {
            "boleh_reminder_kontrol": True,
            "boleh_promo": True,
            "jangan_dihubungi": False,
            "catatan_kontak": "",
        }
    return {
        "boleh_reminder_kontrol": bool(pref.boleh_reminder_kontrol),
        "boleh_promo": bool(pref.boleh_promo),
        "jangan_dihubungi": bool(pref.jangan_dihubungi),
        "catatan_kontak": pref.catatan_kontak or "",
    }


def _patient_metrics(patient, followup, now, manual_tags=None, contact_preference=None):
    visits = sorted(patient.visits or [], key=lambda visit: visit.date or datetime.min)
    total_visits = len(visits)
    total_spent = sum(float(visit.price or 0) for visit in visits)
    first_visit = visits[0].date if visits else None
    last_visit = visits[-1].date if visits else None
    days_since_last_visit = (now.date() - last_visit.date()).days if last_visit else None

    intervals = []
    for idx in range(1, len(visits)):
        if visits[idx].date and visits[idx - 1].date:
            intervals.append((visits[idx].date.date() - visits[idx - 1].date.date()).days)
    avg_visit_gap = round(sum(intervals) / len(intervals), 1) if intervals else None

    service_counts = {}
    therapist_counts = {}
    for visit in visits:
        service = visit.service_name or (visit.service.name if getattr(visit, "service", None) else "") or "Bekam"
        service_counts[service] = service_counts.get(service, 0) + 1
        if getattr(visit, "therapist", None):
            therapist_counts[visit.therapist.name] = therapist_counts.get(visit.therapist.name, 0) + 1

    top_service = max(service_counts, key=service_counts.get) if service_counts else ""
    top_therapist = max(therapist_counts, key=therapist_counts.get) if therapist_counts else ""

    high_value = _is_high_value(total_visits, total_spent)

    if total_visits == 0:
        segment = "new"
        segment_label = "Pasien baru"
        recommendation = "Belum ada kunjungan. Arahkan ke kunjungan pertama."
    elif high_value and days_since_last_visit is not None and days_since_last_visit >= 45:
        segment = "high_value_at_risk"
        segment_label = "Pasien Prioritas Perlu Dihubungi"
        recommendation = f"Pasien bernilai tinggi sudah {days_since_last_visit} hari tidak kembali. Prioritaskan follow-up personal."
    elif days_since_last_visit is not None and days_since_last_visit >= 120:
        segment = "dormant"
        segment_label = "Lama Tidak Datang"
        recommendation = f"Sudah {days_since_last_visit} hari tidak kembali. Perlu follow-up."
    elif days_since_last_visit is not None and days_since_last_visit >= 45:
        segment = "needs_followup"
        segment_label = "Perlu follow-up"
        recommendation = f"Terakhir datang {days_since_last_visit} hari lalu. Hubungi untuk kontrol."
    elif high_value:
        segment = "high_value"
        segment_label = "Pasien Prioritas"
        recommendation = "Prioritaskan relasi dan tawarkan jadwal rutin."
    elif total_visits >= 4:
        segment = "loyal"
        segment_label = "Rutin"
        recommendation = "Pasien rutin. Jaga ritme kunjungan dan catatan progres."
    else:
        segment = "active"
        segment_label = "Aktif"
        recommendation = "Masih aktif. Pantau jeda kunjungan berikutnya."

    followup_status = followup.status if followup else "pending"
    followup_due_status, followup_due_label = _followup_due(followup, now.date())

    return {
        "id": patient.id,
        "name": patient.name,
        "phone": patient.phone,
        "gender": patient.gender,
        "total_visits": total_visits,
        "total_spent": total_spent,
        "first_visit": _date_text(first_visit),
        "last_visit": _date_text(last_visit),
        "days_since_last_visit": days_since_last_visit,
        "avg_visit_gap": avg_visit_gap,
        "top_service": top_service,
        "top_therapist": top_therapist,
        "segment": segment,
        "segment_label": segment_label,
        "followup_status": followup_status,
        "followup_status_label": FOLLOWUP_STATUSES.get(followup_status, followup_status),
        "followup_outcome": followup.outcome if followup else "",
        "followup_outcome_label": FOLLOWUP_OUTCOMES.get(followup.outcome if followup else "", followup.outcome if followup else ""),
        "followup_due_status": followup_due_status,
        "followup_due_label": followup_due_label,
        "followup_note": followup.note if followup else "",
        "follow_up_date": _date_text(followup.follow_up_date) if followup else "",
        "last_contacted_at": _date_text(followup.last_contacted_at) if followup else "",
        "tags": _patient_service_tags(patient) + _manual_tag_payload(manual_tags),
        "contact_preference": _contact_pref_payload(contact_preference),
        "recommendation": recommendation,
    }


def build_crm_patients(session, segment="", status="", search="", tag_type="", tag=""):
    segment = str(segment or "").strip()
    status = str(status or "").strip()
    search = str(search or "").strip()
    tag_type = str(tag_type or "").strip()
    tag = str(tag or "").strip()
    now = datetime.now()
    latest_followups = _latest_followups(session)
    manual_tag_rows = session.query(PatientManualTag).all()
    manual_tags_by_patient = {}
    for row in manual_tag_rows:
        manual_tags_by_patient.setdefault(row.patient_id, []).append(row)
    contact_prefs = {
        pref.patient_id: pref
        for pref in session.query(PatientContactPreference).all()
    }
    patients = (
        session.query(Patient)
        .options(
            joinedload(Patient.visits).joinedload(Visit.therapist),
            joinedload(Patient.visits).joinedload(Visit.service),
        )
        .all()
    )

    rows = [
        _patient_metrics(
            patient,
            latest_followups.get(patient.id),
            now,
            manual_tags=manual_tags_by_patient.get(patient.id, []),
            contact_preference=contact_prefs.get(patient.id),
        )
        for patient in patients
    ]

    now_dt = datetime.now()
    active_rules_for_crm = (
        session.query(DiscountRule)
        .filter(DiscountRule.type == "voucher", DiscountRule.is_active == True)
        .order_by(DiscountRule.priority.asc(), DiscountRule.created_at.asc())
        .all()
    )
    special_rules_for_crm = []

    if active_rules_for_crm:
        valid_crm_rule_ids = [r.id for r in active_rules_for_crm if _rule_date_active(r, now_dt)]
        if valid_crm_rule_ids:
            crm_targets = session.query(VoucherPatientTarget).filter(VoucherPatientTarget.discount_rule_id.in_(valid_crm_rule_ids)).all()
            crm_target_map = {}
            for t in crm_targets:
                crm_target_map.setdefault(t.discount_rule_id, set()).add(t.patient_id)

            crm_usages = session.query(VoucherUsage.discount_rule_id, VoucherUsage.patient_id).filter(VoucherUsage.discount_rule_id.in_(valid_crm_rule_ids)).all()
            crm_usage_counts = {}
            crm_patient_usage_counts = {}
            for u in crm_usages:
                crm_usage_counts[u.discount_rule_id] = crm_usage_counts.get(u.discount_rule_id, 0) + 1
                crm_patient_usage_counts[(u.discount_rule_id, u.patient_id)] = crm_patient_usage_counts.get((u.discount_rule_id, u.patient_id), 0) + 1

            for rule in active_rules_for_crm:
                if rule.id not in valid_crm_rule_ids: continue
                rule_targets = crm_target_map.get(rule.id, set())
                if not rule_targets: continue

                total_limit = int(rule.usage_limit or 0)
                if total_limit > 0 and crm_usage_counts.get(rule.id, 0) >= total_limit:
                    continue
                special_rules_for_crm.append({
                    "rule": rule,
                    "targets": rule_targets,
                    "per_patient_limit": int(rule.per_patient_limit or 0)
                })

    for row in rows:
        special_count = 0
        p_id = row["id"]
        for sr in special_rules_for_crm:
            if p_id in sr["targets"]:
                pp_limit = sr["per_patient_limit"]
                if pp_limit > 0 and crm_patient_usage_counts.get((sr["rule"].id, p_id), 0) >= pp_limit:
                    continue
                special_count += 1

        row["has_special_voucher"] = special_count > 0
        row["special_voucher_count"] = special_count

    if segment:
        rows = [row for row in rows if row["segment"] == segment]
    if status:
        rows = [row for row in rows if row["followup_status"] == status]
    if tag:
        rows = [
            row for row in rows
            if any(
                item.get("value") == tag and (not tag_type or item.get("type") == tag_type)
                for item in row.get("tags", [])
            )
        ]
    if search:
        needle = search.lower()
        rows = [
            row for row in rows
            if needle in row["name"].lower() or needle in str(row["phone"] or "").lower()
        ]

    return sorted(
        rows,
        key=lambda row: (
            row["segment"] not in ("high_value_at_risk", "needs_followup", "dormant", "high_value"),
            row["followup_due_status"] not in ("overdue", "today"),
            -(row["days_since_last_visit"] or 0),
            -row["total_spent"],
        ),
    )


def build_crm_summary(session):
    rows = build_crm_patients(session)
    segments = {
        "new": 0,
        "active": 0,
        "loyal": 0,
        "high_value": 0,
        "high_value_at_risk": 0,
        "needs_followup": 0,
        "dormant": 0,
    }
    statuses = {key: 0 for key in FOLLOWUP_STATUSES}

    for row in rows:
        segments[row["segment"]] = segments.get(row["segment"], 0) + 1
        statuses[row["followup_status"]] = statuses.get(row["followup_status"], 0) + 1

    overdue_followups = sum(1 for row in rows if row.get("followup_due_status") == "overdue")
    need_followup_ids = {
        row["id"]
        for row in rows
        if row["segment"] in {"needs_followup", "dormant", "high_value_at_risk"}
        or row.get("followup_due_status") == "overdue"
    }

    return {
        "total_patients": len(rows),
        "segments": segments,
        "statuses": statuses,
        "need_followup": len(need_followup_ids),
        "overdue_followups": overdue_followups,
        "high_value": segments.get("high_value", 0),
        "high_value_at_risk": segments.get("high_value_at_risk", 0),
        "followup_statuses": FOLLOWUP_STATUSES,
        "top_followup": rows[:8],
    }


def build_crm_tag_options(session):
    rows = build_crm_patients(session)
    service_tags = {item["value"]: item for item in _active_service_tags(session)}
    manual_tags = {item["value"]: item for item in get_manual_tag_options(session)}
    for row in rows:
        for tag in row.get("tags", []):
            if tag.get("type") == "service":
                service_tags[tag["value"]] = tag
            elif tag.get("type") == "manual":
                manual_tags[tag["value"]] = tag
    return {
        "service": sorted(service_tags.values(), key=lambda item: item["label"].lower()),
        "manual": sorted(manual_tags.values(), key=lambda item: item["label"].lower()),
    }


def _clean_phone(phone):
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if digits.startswith("0"):
        return "62" + digits[1:]
    if digits.startswith("8"):
        return "62" + digits
    return digits


def _patient_salutation(row, default="Bapak/Ibu"):
    gender = str(row.get("gender") or "").strip().lower()
    if gender.startswith("perempuan"):
        return "Ibu"
    if gender.startswith("laki"):
        return "Pak"
    return default


def _patient_first_name(row):
    name = str(row.get("name") or "").strip()
    return name.split()[0] if name else ""


def build_followup_message(row, template="kontrol", clinic_name="Lancar Dynamic Admin"):
    template = template if template in MESSAGE_TEMPLATES else "kontrol"
    name = row.get("name") or "Bapak/Ibu"
    first_name = name.strip().split()[0] if name.strip() else "Bapak/Ibu"
    clinic = (clinic_name or "Lancar Dynamic Admin").strip()
    service = row.get("top_service") or "terapi"
    last_visit = row.get("last_visit") or ""
    last_visit_text = _friendly_date(datetime.strptime(last_visit, "%Y-%m-%d")) if last_visit else ""
    days = row.get("days_since_last_visit")

    intro = f"Assalamu'alaikum {first_name}, ini admin {clinic}."

    if template == "reaktivasi":
        context = (
            f"Kami cek terakhir kunjungan {last_visit_text}."
            if last_visit_text
            else "Kami ingin menyapa kembali setelah beberapa waktu belum berkunjung."
        )
        ask = "Apakah ada keluhan yang ingin dikontrol atau jadwal yang cocok untuk terapi lanjutan minggu ini?"
    elif template == "promo":
        context = f"Kami sedang menyiapkan jadwal untuk pasien yang biasa mengambil layanan {service}."
        ask = "Kalau berkenan, kami bantu cek slot terdekat dan info paket yang sesuai kebutuhan."
    elif template == "aftercare":
        context = (
            f"Semoga kondisi setelah layanan {service} kemarin semakin membaik."
            if service
            else "Semoga kondisi setelah terapi kemarin semakin membaik."
        )
        ask = "Apakah ada keluhan lanjutan atau hal yang perlu kami bantu pantau?"
    else:
        if days is not None:
            context = f"Sudah sekitar {days} hari sejak kunjungan terakhir"
            if last_visit_text:
                context += f" pada {last_visit_text}"
            context += f" untuk layanan {service}."
        else:
            context = "Kami ingin membantu menjadwalkan kunjungan pertama."
        ask = "Apakah ingin kami bantu jadwalkan kontrol atau terapi lanjutan?"

    closing = "Silakan balas pesan ini, nanti kami bantu pilihkan jadwal yang paling nyaman. Terima kasih."
    message = f"{intro}\n\n{context}\n{ask}\n\n{closing}"
    phone = _clean_phone(row.get("phone"))

    return {
        "template": template,
        "template_label": MESSAGE_TEMPLATES[template],
        "message": message,
        "phone": phone,
        "whatsapp_url": f"https://wa.me/{phone}?text={quote(message)}" if phone else "",
    }


def _recent_confirmed_whatsapp_log(session, patient_id, message_type, lock_days):
    if not lock_days:
        return None
    cutoff = datetime.now() - timedelta(days=int(lock_days))
    return (
        session.query(CRMWhatsAppLog)
        .filter(
            CRMWhatsAppLog.patient_id == int(patient_id),
            CRMWhatsAppLog.message_type == message_type,
            CRMWhatsAppLog.status == "confirmed_sent",
            CRMWhatsAppLog.confirmed_at >= cutoff,
        )
        .order_by(CRMWhatsAppLog.confirmed_at.desc(), CRMWhatsAppLog.id.desc())
        .first()
    )


def _build_lock_warning(log, message_type, lock_days):
    if not log:
        return ""
    label = WHATSAPP_TEMPLATE_LABELS.get(message_type, message_type)
    sent_at = log.confirmed_at.strftime("%Y-%m-%d %H:%M") if log.confirmed_at else "-"
    return (
        f"Pasien sudah dikonfirmasi menerima pesan {label} pada {sent_at}. "
        f"Jeda aman default {lock_days} hari. Admin bisa override manual jika memang perlu."
    )


def _whatsapp_template_message(row, template_type, variant_index=0, voucher=None):
    salutation = _patient_salutation(row)
    first_name = _patient_first_name(row)
    greeting_name = f"{salutation} {first_name}".strip() if first_name else salutation
    service = row.get("top_service") or "terapi"
    last_visit = row.get("last_visit") or ""
    last_visit_text = _friendly_date(datetime.strptime(last_visit, "%Y-%m-%d")) if last_visit else ""
    days = row.get("days_since_last_visit")
    profile = _clinic_profile()

    if template_type == "reactivation_neutral":
        context = (
            f"Kami melihat kunjungan terakhir {greeting_name} pada {last_visit_text} untuk layanan {service}."
            if last_visit_text
            else f"Kami ingin menyapa kembali dan membantu cek kebutuhan layanan {service}."
        )
        message = (
            f"Halo {greeting_name}, kami dari {profile['clinic_name']}.\n\n"
            f"{context}\n\n"
            "Jika ada keluhan yang ingin dikontrol atau ingin dibantu cek jadwal terapi lanjutan, admin siap membantu.\n\n"
            "Silakan balas pesan ini kapan saja. Terima kasih."
        )
    elif template_type in ("reactivation", "reactivation_polite"):
        context = (
            f"Kami cek kunjungan terakhir {greeting_name} pada {last_visit_text} untuk layanan {service}."
            if last_visit_text
            else f"Kami ingin menyapa kembali dan membantu cek kebutuhan layanan {service}."
        )
        ask_options = [
            "Apakah ada keluhan yang ingin dikontrol atau ingin dibantu pilih jadwal terapi lanjutan?",
            f"Jika {salutation} berkenan, kami bisa bantu cek jadwal kontrol yang nyaman minggu ini.",
        ]
        message = (
            f"Assalamu'alaikum, {greeting_name}.\n\n"
            f"Semoga {greeting_name} dalam keadaan sehat selalu.\n\n"
            f"Kami dari {profile['clinic_name']} ingin menyapa kembali. {context}\n\n"
            f"{ask_options[variant_index % len(ask_options)]}\n\n"
            f"Silakan balas pesan ini kapan saja ya, {salutation}. Nanti kami bantu carikan jadwal yang paling nyaman.\n\n"
            "Terima kasih."
        )
    elif template_type == "promo_neutral":
        context = f"Kami sedang menyiapkan info jadwal dan promo yang bisa disesuaikan dengan kebutuhan layanan {service}."
        message = (
            f"Halo {greeting_name}, kami dari {profile['clinic_name']}.\n\n"
            f"{context}\n\n"
            "Jika berkenan, admin bisa bantu kirimkan pilihan jadwal dan paket yang sesuai kebutuhan.\n\n"
            "Silakan balas pesan ini untuk cek slot terdekat. Terima kasih."
        )
    elif template_type in ("promo", "promo_polite"):
        context = f"Kami sedang menyiapkan info jadwal dan promo yang bisa disesuaikan dengan kebutuhan layanan {service}."
        ask_options = [
            "Kalau berkenan, kami bantu cek slot terdekat dan pilihan paket yang paling cocok.",
            f"Boleh kami bantu kirimkan pilihan jadwal dan paket yang sesuai kebutuhan {salutation}?",
        ]
        message = (
            f"Assalamu'alaikum, {greeting_name}.\n\n"
            "Semoga sehat selalu.\n\n"
            f"{context}\n\n"
            f"{ask_options[variant_index % len(ask_options)]}\n\n"
            f"Jika {salutation} ingin konsultasi lebih dulu, silakan balas pesan ini. Admin siap bantu.\n\n"
            "Terima kasih."
        )
    elif template_type == "aftercare_neutral":
        context = f"Semoga kondisi setelah layanan {service} semakin membaik."
        message = (
            f"Halo {greeting_name}, kami dari {profile['clinic_name']}.\n\n"
            f"{context}\n\n"
            "Apakah ada keluhan lanjutan atau hal yang perlu kami bantu pantau setelah terapi?\n\n"
            "Silakan balas pesan ini jika membutuhkan arahan dari admin. Terima kasih."
        )
    elif template_type in ("aftercare", "aftercare_polite"):
        context = f"Semoga kondisi setelah layanan {service} semakin membaik."
        ask_options = [
            "Apakah ada keluhan lanjutan atau hal yang perlu kami bantu pantau?",
            "Kalau ada reaksi atau keluhan setelah terapi, silakan kabari kami agar bisa kami bantu arahkan.",
        ]
        message = (
            f"Assalamu'alaikum, {greeting_name}.\n\n"
            f"{context}\n\n"
            f"{ask_options[variant_index % len(ask_options)]}\n\n"
            f"Silakan balas pesan ini kapan saja ya, {salutation}. Semoga lekas pulih dan sehat selalu.\n\n"
            "Terima kasih."
        )
    else:
        if days is not None:
            context = f"Sudah sekitar {days} hari sejak kunjungan terakhir"
            if last_visit_text:
                context += f" pada {last_visit_text}"
            context += f" untuk layanan {service}."
        else:
            context = f"Kami ingin membantu menjadwalkan kunjungan pertama {salutation}."

        if template_type == "routine_neutral":
            message = (
                f"Halo {greeting_name}, kami dari {profile['clinic_name']}.\n\n"
                f"Kami ingin menginformasikan bahwa {context[0].lower() + context[1:]}\n\n"
                "Jika ingin melakukan kontrol atau konsultasi lanjutan, admin siap bantu cek jadwal terdekat.\n\n"
                "Silakan balas pesan ini kapan saja. Terima kasih."
            )
        elif template_type == "routine_friendly":
            message = (
                f"Halo {greeting_name}, apa kabar?\n\n"
                f"Kami dari {profile['clinic_name']} ingin follow-up. {context}\n\n"
                "Kalau ingin kontrol lanjutan atau cek jadwal terdekat, balas pesan ini ya. Admin siap bantu.\n\n"
                "Terima kasih."
            )
        elif template_type == "routine_short":
            message = (
                f"Assalamu'alaikum, {greeting_name}.\n\n"
                f"Kami dari {profile['clinic_name']} ingin mengingatkan bahwa {context[0].lower() + context[1:]}\n\n"
                "Jika ingin kontrol atau konsultasi lanjutan, admin siap bantu cek jadwal terdekat.\n\n"
                "Terima kasih."
            )
        elif template_type == "routine_warm":
            message = (
                f"Assalamu'alaikum, {greeting_name}.\n\n"
                f"Semoga {greeting_name} dan keluarga dalam keadaan sehat selalu.\n\n"
                f"Kami dari {profile['clinic_name']} ingin follow-up kabar {greeting_name}. {context}\n\n"
                "Jika ada keluhan yang ingin dikonsultasikan atau ingin kontrol lanjutan, silakan balas pesan ini. "
                "Nanti admin bantu cek slot jadwal yang paling nyaman.\n\n"
                "Terima kasih."
            )
        else:
            message = (
                f"Assalamu'alaikum, {greeting_name}.\n\n"
                f"Semoga {greeting_name} dalam keadaan sehat selalu.\n\n"
                f"Kami dari {profile['clinic_name']} ingin menginformasikan bahwa {context[0].lower() + context[1:]}\n\n"
                "Jika ingin melakukan kontrol atau konsultasi lanjutan, admin siap bantu cek slot jadwal terdekat yang tersedia.\n\n"
                f"Silakan balas pesan ini kapan saja ya, {salutation}. Nanti kami bantu carikan jadwal yang paling nyaman.\n\n"
                "Terima kasih."
            )

    return f"{message}{_voucher_message_block(voucher)}{_clinic_contact_footer(profile)}"


def build_crm_whatsapp_link(row, template_type="routine", custom_message=None, variant_index=0, voucher=None):
    template_type = WHATSAPP_TEMPLATE_ALIASES.get(str(template_type or "").strip(), "routine")
    name = row.get("name") or "Bapak/Ibu"

    if custom_message and str(custom_message).strip():
        message = normalize_whatsapp_message(custom_message)
    else:
        message = normalize_whatsapp_message(_whatsapp_template_message(row, template_type, variant_index=variant_index, voucher=voucher))

    normalized_phone = normalize_wa_number(row.get("phone"))
    return {
        "patient_id": row.get("id"),
        "patient_name": name,
        "phone": normalized_phone,
        "whatsapp_url": build_whatsapp_url(normalized_phone, message),
        "message": message,
        "template_type": template_type,
        "template_label": WHATSAPP_TEMPLATE_LABELS.get(template_type, template_type),
        "voucher": voucher,
    }


def check_contact_warning(row, template_type):
    template_type = WHATSAPP_TEMPLATE_ALIASES.get(str(template_type or "").strip(), "routine")
    warnings = []
    pref = row.get("contact_preference") or {}
    tags = row.get("tags") or []
    tag_values = {tag.get("value") for tag in tags if tag.get("type") == "manual"}
    if pref.get("jangan_dihubungi") or "jangan-dihubungi" in tag_values:
        warnings.append("Pasien ditandai jangan dihubungi. Pastikan ada alasan jelas sebelum membuka WhatsApp.")
    if template_type in {"promo", "promo_polite"} and (pref.get("boleh_promo") is False or "jangan-promo" in tag_values):
        warnings.append("Pasien tidak mengizinkan pesan promo atau memiliki tag Jangan Promo.")
    if template_type.startswith("routine") and pref.get("boleh_reminder_kontrol") is False:
        warnings.append("Pasien tidak mengizinkan reminder kontrol.")
    if pref.get("catatan_kontak"):
        warnings.append(f"Catatan kontak: {pref['catatan_kontak']}")
    return warnings


def _contact_block_reason(row, template_type):
    template_type = WHATSAPP_TEMPLATE_ALIASES.get(str(template_type or "").strip(), "routine")
    pref = row.get("contact_preference") or {}
    tags = row.get("tags") or []
    tag_values = {tag.get("value") for tag in tags if tag.get("type") == "manual"}
    if pref.get("jangan_dihubungi") or "jangan-dihubungi" in tag_values:
        return "Pasien ditandai jangan dihubungi."
    if template_type.startswith("promo") and (pref.get("boleh_promo") is False or "jangan-promo" in tag_values):
        return "Pasien tidak mengizinkan pesan promo."
    return ""


def create_crm_whatsapp_log(
    session,
    row,
    template_type="routine",
    custom_message=None,
    override_lock=False,
    mark_opened=False,
    voucher=None,
):
    template_type = WHATSAPP_TEMPLATE_ALIASES.get(str(template_type or "").strip(), "routine")
    patient_id = int(row.get("id"))
    existing_count = (
        session.query(CRMWhatsAppLog)
        .filter(CRMWhatsAppLog.patient_id == patient_id, CRMWhatsAppLog.message_type == template_type)
        .count()
    )
    link_data = build_crm_whatsapp_link(
        row,
        template_type=template_type,
        custom_message=custom_message,
        variant_index=existing_count,
        voucher=voucher,
    )
    lock_days = WHATSAPP_LOCK_DAYS.get(template_type, 0)
    recent_log = _recent_confirmed_whatsapp_log(session, patient_id, template_type, lock_days)
    lock_warning = _build_lock_warning(recent_log, template_type, lock_days)
    contact_warnings = check_contact_warning(row, template_type)
    preference_block = _contact_block_reason(row, template_type)
    if preference_block:
        log = CRMWhatsAppLog(
            patient_id=patient_id,
            phone=link_data["phone"],
            message_type=template_type,
            message=link_data["message"],
            whatsapp_url="",
            status="skipped_preference",
            note=preference_block,
        )
        session.add(log)
        session.commit()
        link_data.update({
            "whatsapp_url": "",
            "log_id": log.id,
            "status": log.status,
            "status_label": WHATSAPP_LOG_STATUSES.get(log.status, log.status),
            "blocked": True,
            "block_reason": "preference",
            "lock_warning": preference_block,
            "contact_warnings": contact_warnings,
            "lock_active": True,
            "lock_days": lock_days,
            "override_lock": False,
        })
        return link_data
    if lock_warning and not override_lock:
        log = CRMWhatsAppLog(
            patient_id=patient_id,
            phone=link_data["phone"],
            message_type=template_type,
            message=link_data["message"],
            whatsapp_url="",
            status="skipped_send_lock",
            note=lock_warning,
        )
        session.add(log)
        session.commit()
        link_data.update({
            "whatsapp_url": "",
            "log_id": log.id,
            "status": log.status,
            "status_label": WHATSAPP_LOG_STATUSES.get(log.status, log.status),
            "blocked": True,
            "block_reason": "send_lock",
            "lock_warning": lock_warning,
            "contact_warnings": contact_warnings,
            "lock_active": True,
            "lock_days": lock_days,
            "override_lock": False,
        })
        return link_data
    all_warnings = ([lock_warning] if lock_warning else []) + contact_warnings
    status = "opened" if mark_opened else "drafted"
    note = "Dibuka manual via wa.me" if mark_opened else "Draft link WhatsApp dibuat"
    if all_warnings and not override_lock:
        note += " dengan warning kontak aktif"
    elif all_warnings and override_lock:
        note += " dengan override warning kontak"

    log = CRMWhatsAppLog(
        patient_id=patient_id,
        phone=link_data["phone"],
        message_type=template_type,
        message=link_data["message"],
        whatsapp_url=link_data["whatsapp_url"],
        status=status,
        note=note,
    )
    session.add(log)
    session.commit()

    link_data.update({
        "log_id": log.id,
        "status": log.status,
        "status_label": WHATSAPP_LOG_STATUSES.get(log.status, log.status),
        "lock_warning": "\n".join(all_warnings),
        "contact_warnings": contact_warnings,
        "lock_active": bool(all_warnings),
        "lock_days": lock_days,
        "override_lock": bool(override_lock),
    })
    return link_data


def save_patient_followup(session, patient_id, status, note="", follow_up_date=None):
    if status not in FOLLOWUP_STATUSES:
        raise ValueError("Status follow-up tidak valid.")

    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")

    parsed_follow_up_date = None
    if follow_up_date:
        try:
            parsed_follow_up_date = datetime.strptime(str(follow_up_date), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Format tanggal follow-up tidak valid. Gunakan YYYY-MM-DD.")

    now = datetime.now()
    followup = PatientFollowup(
        patient_id=patient.id,
        status=status,
        note=str(note or "").strip(),
        follow_up_date=parsed_follow_up_date,
        last_contacted_at=now if status in {"contacted", "waiting", "booked", "inactive"} else None,
    )
    session.add(followup)
    session.commit()
    return followup.id


def save_followup_outcome(session, patient_id, outcome, note="", follow_up_date=None):
    outcome = str(outcome or "").strip()
    if outcome not in FOLLOWUP_OUTCOMES or outcome == "":
        raise ValueError("Outcome follow-up tidak valid.")
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")

    parsed_follow_up_date = None
    if follow_up_date:
        try:
            parsed_follow_up_date = datetime.strptime(str(follow_up_date), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Format tanggal follow-up tidak valid. Gunakan YYYY-MM-DD.")

    latest = (
        session.query(PatientFollowup)
        .filter(PatientFollowup.patient_id == patient.id)
        .order_by(PatientFollowup.created_at.desc(), PatientFollowup.id.desc())
        .first()
    )
    status = latest.status if latest else "contacted"
    if outcome == "booked":
        status = "booked"
    elif outcome == "contact_later":
        status = "waiting"
    elif outcome in {"not_interested", "invalid_number"}:
        status = "inactive"

    followup = PatientFollowup(
        patient_id=patient.id,
        status=status,
        outcome=outcome,
        note=str(note or "").strip(),
        follow_up_date=parsed_follow_up_date,
        last_contacted_at=datetime.now(),
    )
    session.add(followup)
    session.commit()
    return {
        "status": "success",
        "id": followup.id,
        "outcome": outcome,
        "outcome_label": FOLLOWUP_OUTCOMES[outcome],
        "message": "Outcome follow-up tersimpan.",
    }


def confirm_crm_whatsapp_log(session, patient_id, log_id=None, follow_up_date=None):
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")

    query = session.query(CRMWhatsAppLog).filter(CRMWhatsAppLog.patient_id == patient.id)
    if log_id:
        log = query.filter(CRMWhatsAppLog.id == int(log_id)).first()
    else:
        log = (
            query
            .filter(CRMWhatsAppLog.status.in_(["opened", "drafted"]))
            .order_by(CRMWhatsAppLog.created_at.desc(), CRMWhatsAppLog.id.desc())
            .first()
        )
    if not log:
        raise ValueError("Log WhatsApp tidak ditemukan. Buat link WhatsApp terlebih dahulu.")

    now = datetime.now()
    log.status = "confirmed_sent"
    log.confirmed_at = now
    log.note = "pesan WhatsApp sudah dikirim/manual confirmed"
    followup_id = save_patient_followup(
        session,
        patient.id,
        "contacted",
        "pesan WhatsApp sudah dikirim/manual confirmed",
        follow_up_date=follow_up_date,
    )
    return {
        "status": "success",
        "log_id": log.id,
        "followup_id": followup_id,
        "message": "Aktivitas WhatsApp dicatat sebagai sudah dihubungi.",
    }


def mark_whatsapp_contacted(session, patient_id, follow_up_date=None):
    return confirm_crm_whatsapp_log(session, patient_id, follow_up_date=follow_up_date)["followup_id"]


def build_patient_followup_history(session, patient_id, limit=10):
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")
    followups = (
        session.query(PatientFollowup)
        .filter(PatientFollowup.patient_id == patient.id)
        .order_by(PatientFollowup.created_at.desc(), PatientFollowup.id.desc())
        .limit(int(limit or 10))
        .all()
    )
    return [
        {
            "id": followup.id,
            "status": followup.status,
            "status_label": FOLLOWUP_STATUSES.get(followup.status, followup.status),
            "outcome": followup.outcome or "",
            "outcome_label": FOLLOWUP_OUTCOMES.get(followup.outcome or "", ""),
            "note": followup.note or "",
            "follow_up_date": _date_text(followup.follow_up_date),
            "last_contacted_at": _date_text(followup.last_contacted_at),
            "created_at": followup.created_at.strftime("%Y-%m-%d %H:%M:%S") if followup.created_at else "",
        }
        for followup in followups
    ]


def build_patient_message_logs(session, patient_id, limit=10):
    patient = session.get(Patient, int(patient_id))
    if not patient:
        raise ValueError("Pasien tidak ditemukan.")
    logs = (
        session.query(CRMWhatsAppLog)
        .filter(CRMWhatsAppLog.patient_id == patient.id)
        .order_by(CRMWhatsAppLog.created_at.desc(), CRMWhatsAppLog.id.desc())
        .limit(int(limit or 10))
        .all()
    )
    return [
        {
            "id": log.id,
            "patient_id": log.patient_id,
            "phone": log.phone,
            "message_type": log.message_type,
            "message_type_label": WHATSAPP_TEMPLATE_LABELS.get(log.message_type, log.message_type),
            "message": log.message,
            "whatsapp_url": log.whatsapp_url,
            "status": log.status,
            "status_label": WHATSAPP_LOG_STATUSES.get(log.status, log.status),
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
            "confirmed_at": log.confirmed_at.strftime("%Y-%m-%d %H:%M:%S") if log.confirmed_at else "",
            "note": log.note or "",
        }
        for log in logs
    ]


def build_crm_daily_tasks(session):
    rows = build_crm_patients(session)
    priority_order = {
        "overdue": 1,
        "high_value_at_risk": 2,
        "contact_later": 3,
        "due_today": 4,
        "needs_followup": 4,
        "dormant": 5,
    }
    task_rows = []
    seen = set()
    for row in rows:
        task_type = ""
        if row.get("followup_due_status") == "overdue":
            task_type = "overdue"
        elif row.get("segment") == "high_value_at_risk":
            task_type = "high_value_at_risk"
        elif row.get("followup_outcome") == "contact_later":
            task_type = "contact_later"
        elif row.get("followup_due_status") == "today":
            task_type = "due_today"
        elif row.get("segment") == "needs_followup":
            task_type = "needs_followup"
        elif row.get("segment") == "dormant":
            task_type = "dormant"
        if not task_type or row["id"] in seen:
            continue
        seen.add(row["id"])
        task_rows.append({
            **row,
            "task_type": task_type,
            "priority": priority_order.get(task_type, 6),
        })

    task_rows.sort(key=lambda item: (item["priority"], -(item.get("days_since_last_visit") or 0), -item.get("total_spent", 0)))
    return {
        "total_tasks": len(task_rows),
        "overdue": sum(1 for row in task_rows if row["task_type"] == "overdue"),
        "due_today": sum(1 for row in task_rows if row["task_type"] == "due_today"),
        "high_priority": sum(1 for row in task_rows if row["task_type"] == "high_value_at_risk"),
        "contact_later": sum(1 for row in task_rows if row["task_type"] == "contact_later"),
        "rows": task_rows,
    }


def build_crm_conversion_report(session, start_date=None, end_date=None):
    def parse_dt(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return datetime.fromisoformat(f"{value}T00:00:00")

    start = parse_dt(start_date)
    end = parse_dt(end_date)

    log_query = session.query(CRMWhatsAppLog)
    followup_query = session.query(PatientFollowup)
    if start:
        log_query = log_query.filter(CRMWhatsAppLog.created_at >= start)
        followup_query = followup_query.filter(PatientFollowup.created_at >= start)
    if end:
        log_query = log_query.filter(CRMWhatsAppLog.created_at <= end)
        followup_query = followup_query.filter(PatientFollowup.created_at <= end)

    total_messages = log_query.count()
    confirmed_sent = log_query.filter(CRMWhatsAppLog.status == "confirmed_sent").count()
    contacted = followup_query.filter(PatientFollowup.last_contacted_at.isnot(None)).count()
    booked = (
        followup_query
        .filter(PatientFollowup.outcome == "booked")
        .with_entities(PatientFollowup.patient_id)
        .distinct()
        .count()
    )
    no_response = followup_query.filter(PatientFollowup.outcome == "no_response").count()
    not_interested = followup_query.filter(PatientFollowup.outcome == "not_interested").count()
    invalid_number = followup_query.filter(PatientFollowup.outcome == "invalid_number").count()
    return {
        "total_whatsapp_created": total_messages,
        "total_confirmed_sent": confirmed_sent,
        "total_followup_contacted": contacted,
        "total_outcome_booked": booked,
        "conversion_rate": round((booked / contacted) * 100, 2) if contacted else 0,
        "no_response_count": no_response,
        "not_interested_count": not_interested,
        "invalid_number_count": invalid_number,
    }
