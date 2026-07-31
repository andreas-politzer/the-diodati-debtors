"""Tests for club_conversation_service — free-form messaging between
members of the same club (project vault: Personal Messages Domain
Model). No OPEN/CLOSED lifecycle, unlike BorrowingInquiry — one
ongoing conversation per (initiator, recipient, club), per Andy's
WhatsApp analogy."""

from __future__ import annotations

import pytest

from diodati_debtors.core.exceptions import NotAuthorizedError, NotFoundError
from diodati_debtors.models.user import User
from diodati_debtors.services import club_conversation_service, group_service, profile_service


def _make_user(db, email: str) -> int:
    with db() as session:
        user = User(email=email, password_hash="x", display_name="User")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id


def _make_club_members(db, founder_email: str, member_email: str, club_name: str):
    founder_id = _make_user(db, founder_email)
    member_id = _make_user(db, member_email)
    group = group_service.create_group(founder_id=founder_id, name=club_name)
    request = group_service.request_to_join(user_id=member_id, group_id=group.id)
    group_service.approve_join_request(request.id, reviewer_id=founder_id)
    return founder_id, member_id, group.id


def test_send_message_creates_new_conversation(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc1@example.com", "member_cc1@example.com", "Gothic Club 1")

    result = club_conversation_service.send_message(founder_id, member_id, "Hey, loved your review!")

    assert result.group_id == group_id
    assert len(result.messages) == 1
    assert result.messages[0].content == "Hey, loved your review!"


def test_send_message_reuses_existing_conversation(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc2@example.com", "member_cc2@example.com", "Gothic Club 2")

    first = club_conversation_service.send_message(founder_id, member_id, "First message")
    second = club_conversation_service.send_message(member_id, founder_id, "Reply from the other side")

    assert first.id == second.id
    assert len(second.messages) == 2


def test_send_message_rejects_users_without_shared_club(db):
    user_a = _make_user(db, "loner_cc1@example.com")
    user_b = _make_user(db, "loner_cc2@example.com")

    with pytest.raises(club_conversation_service.ConversationNotAllowedError):
        club_conversation_service.send_message(user_a, user_b, "Hi stranger")


def test_send_message_rejects_when_recipient_profile_is_private(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc3@example.com", "member_cc3@example.com", "Gothic Club 3")
    profile_service.update_profile(member_id, visibility="private")

    with pytest.raises(club_conversation_service.ConversationNotAllowedError):
        club_conversation_service.send_message(founder_id, member_id, "Hi!")


def test_send_message_with_explicit_group_id_validates_membership(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc4@example.com", "member_cc4@example.com", "Gothic Club 4")
    other_group = group_service.create_group(founder_id=founder_id, name="Unrelated Club")

    with pytest.raises(club_conversation_service.ConversationNotAllowedError):
        club_conversation_service.send_message(founder_id, member_id, "Hi!", group_id=other_group.id)


def test_list_conversations_for_user_includes_both_roles(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc5@example.com", "member_cc5@example.com", "Gothic Club 5")
    another_founder_id, another_member_id, _ = _make_club_members(db, "founder_cc6@example.com", "member_cc6@example.com", "Gothic Club 6")
    club_conversation_service.send_message(founder_id, member_id, "Hi")
    club_conversation_service.send_message(member_id, founder_id, "Hi back")

    results = club_conversation_service.list_conversations_for_user(founder_id)

    assert len(results) == 1


def test_open_conversation_marks_messages_as_read(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc7@example.com", "member_cc7@example.com", "Gothic Club 7")
    conversation = club_conversation_service.send_message(founder_id, member_id, "Hi!")

    result = club_conversation_service.open_conversation(conversation.id, viewer_id=member_id)

    assert result.messages[0].read_at is not None


def test_open_conversation_rejects_non_participant(db):
    founder_id, member_id, group_id = _make_club_members(db, "founder_cc8@example.com", "member_cc8@example.com", "Gothic Club 8")
    outsider_id = _make_user(db, "outsider_cc1@example.com")
    conversation = club_conversation_service.send_message(founder_id, member_id, "Hi!")

    with pytest.raises(NotAuthorizedError):
        club_conversation_service.open_conversation(conversation.id, viewer_id=outsider_id)


def test_club_conversation_service_has_no_reflex_dependency():
    with open(club_conversation_service.__file__, encoding="utf-8") as f:
        source = f.read()
    assert "import reflex" not in source
    assert "from reflex" not in source