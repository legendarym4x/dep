from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta

from src.entity.models import Contact, User
from src.schemas.contact import ContactModel


async def get_contacts(skip: int, limit: int, db: AsyncSession, user: User):
    """
    The get_contacts function returns a list of contacts for the user.

    :param skip: int: Skip the first n contacts
    :param limit: int: Limit the number of contacts returned
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contact objects
    """
    query = select(Contact).filter_by(user=user).offset(skip).limit(limit)
    result = await db.execute(query)
    contacts = result.scalars().all()
    return contacts


async def get_contact_by_id(contact_id: int, db: AsyncSession, user: User):
    """
    The get_contact_by_id function returns a contact object from the database.

    :param contact_id: int: Specify the id of the contact we want to retrieve
    :param db: AsyncSession: Pass in the database session
    :param user: User: Ensure that the user is only able to get contacts that belong to them
    :return: A contact object
    """
    query = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    return contact


async def search_contacts(
        name: str | None, surname: str | None, email: str | None, limit: int, offset: int, db: AsyncSession, user: User
):
    """
    The search_contacts function searches for contacts in the database.
        Args:
            name (str): The contact's name.
            surname (str): The contact's surname.
            email (str): The contact's email address.

    :param name: str | None: Filter the contacts by name
    :param surname: str | None: Filter contacts by surname
    :param email: str | None: Filter the contacts by email
    :param limit: int: Limit the number of results returned
    :param offset: int: Skip the first n results
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Filter the contacts by user
    :return: A list of contact objects
    """
    query = select(Contact).filter_by(user=user).offset(offset).limit(limit)
    if name:
        query = query.filter(Contact.name.ilike(f"%{name}%"))
    if surname:
        query = query.filter(Contact.surname.ilike(f"%{surname}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))
    result = await db.execute(query)
    contacts = result.scalars().all()
    return contacts


async def get_contacts_with_birthdays(days: int, db: AsyncSession, user: User):
    """
    The get_contacts_with_birthdays function returns a list of contacts with birthdays within the next
        days number of days.

    :param days: int: Specify the number of days in the future to search for birthdays
    :param db: AsyncSession: Pass in the database session
    :param user: User: Specify the user whose contacts we want to get
    :return: A list of contacts with birthdays in the next x days
    """
    today = datetime.today().date()
    start = today.strftime('%m-%d')
    end = (today + timedelta(days)).strftime('%m-%d')
    query = select(Contact).filter(func.to_char(Contact.birthday, 'MM-DD').between(start, end),
                                   Contact.user_id == user.id)
    result = await db.execute(query)
    contacts = result.scalars().all()
    return contacts


async def create_contact(body: ContactModel, db: AsyncSession, user: User):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Create a new contact object
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user from the request
    :return: The contact object that was created
    """
    contact = Contact(**body.model_dump(exclude_unset=True), user=user)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactModel, db: AsyncSession, user: User):
    """
    The update_contact function updates a contact in the database.
        Args:
            contact_id (int): The id of the contact to update.
            body (ContactModel): The updated information for the specified user.

    :param contact_id: int: Identify the contact to be deleted
    :param body: ContactModel: Get the data from the request body
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Check if the user is authorized to update a contact.
    :return: A contact object
    """
    query = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    if contact:
        contact.name = body.name
        contact.surname = body.surname
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        await db.commit()
        await db.refresh(contact)
    return contact


async def delete_contact(contact_id: int, db: AsyncSession, user: User):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the contact to be deleted
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Get the user that is logged in
    :return: A contact object
    """
    query = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(query)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact
