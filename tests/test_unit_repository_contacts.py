import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.contact import ContactModel
from src.entity.models import Contact, User
from src.repository.contacts import get_contacts, get_contact_by_id, search_contacts, get_contacts_with_birthdays, \
    create_contact, update_contact, delete_contact


class TestContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = User(
            username="test_user",
            avatar="test_avatar",
            refresh_token="test_refresh_token",
            confirmed=True
        )
        self.session = AsyncMock(spec=AsyncSession)

    def tearDown(self):
        self.user = None
        self.session = None

    async def test_create_contact(self):
        body = ContactModel(
            name="test_name",
            surname="test_surname",
            email="test@mail.com",
            phone="1234567890",
            birthday=datetime(1997, 11, 3),
        )
        result = await create_contact(body, self.session, self.user)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.user, self.user)
        self.session.add.assert_called_once_with(result)
        self.session.commit.assert_called_once()

    async def test_get_contacts(self):
        contacts = [
            Contact(name="test_name1", surname="test_surname1", email="test1@mail.com", phone="123456789",
                    birthday="1995-06-19", user=self.user),
            Contact(name="test_name2", surname="test_surname2", email="test2@mail.com", phone="987654321",
                    birthday="1993-07-16", user=self.user),
            Contact(name="test_name3", surname="test_surname3", email="test3@mail.com", phone="987612345",
                    birthday="1992-03-12", user=self.user),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(0, 10, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_get_contact_by_id(self):
        contact_id = 1
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=contact_id, name="test_name", surname="test_surname", email="test@mail.com",
            phone="123456789", birthday="1995-06-19", user=self.user
        )
        self.session.execute.return_value = mocked_contact
        result = await get_contact_by_id(contact_id, self.session, self.user)
        self.assertEqual(result.id, contact_id)

    async def test_search_contacts(self):
        contacts = [
            Contact(name="test_name1", surname="test_surname1", email="test1@mail.com", phone="123456789",
                    birthday="1995-06-19", user=self.user),
            Contact(name="test_name2", surname="test_surname2", email="test2@mail.com", phone="987654321",
                    birthday="1993-07-16", user=self.user),
            Contact(name="test_name3", surname="test_surname3", email="test3@mail.com", phone="987612345",
                    birthday="1992-03-12", user=self.user),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await search_contacts(None, None, None, 500, 10, self.session, self.user)
        self.assertEqual(result, contacts)

        # Test search by name
        result = await search_contacts("test_name1", None, None, 500, 10, self.session, self.user)
        expected_result = [contacts[0]]
        self.assertEqual([result[0]], expected_result)

        # Test search by surname
        result = await search_contacts(None, "test_surname2", None, 500, 10, self.session, self.user)
        expected_result = [contacts[1]]
        self.assertEqual([result[1]], expected_result)

        # Test search by email
        result = await search_contacts(None, None, "test3@mail.com", 500, 10, self.session, self.user)
        expected_result = [contacts[2]]
        self.assertEqual([result[2]], expected_result)

    async def test_get_contacts_with_birthdays(self):
        days = 7
        today = datetime.today().date()
        future_birthday = today + timedelta(days=days)
        contacts = [
            Contact(name="test_name1", surname="test_surname1", email="test1@mail.com", phone="123456789",
                    birthday=future_birthday, user=self.user),
            Contact(name="test_name2", surname="test_surname2", email="test2@mail.com", phone="987654321",
                    birthday=future_birthday, user=self.user),
            Contact(name="test_name3", surname="test_surname3", email="test3@mail.com", phone="987612345",
                    birthday=future_birthday, user=self.user),
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts_with_birthdays(days, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_update_contact(self):
        body = ContactModel(
            name="test_name",
            surname="test_surname",
            email="test@mail.com",
            phone="1234567890",
            birthday=datetime(1997, 11, 3)
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1, name="test_name1", surname="test_surname1", email="test111@mail.com",
            phone="4334648536", birthday=datetime(1997, 11, 15), user=self.user
        )
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user)
        self.session.execute.return_value = mocked_contact
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.surname, body.surname)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.user, self.user)

    async def test_delete_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(
            id=1, name="test_name1", surname="test_surname1", email="test111@mail.com",
            phone="4334648536", birthday=datetime(1997, 11, 15), user=self.user
        )
        self.session.execute.return_value = mocked_contact
        result = await delete_contact(1, self.session, self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.user, self.user)


if __name__ == '__main__':
    unittest.main()
