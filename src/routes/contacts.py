from typing import List

from fastapi import Depends, HTTPException, status, Path, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.repository import contacts as repository_contacts
from src.schemas.contact import ContactModel, ContactResponse
from src.services.auth import auth_service

router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get("/", response_model=List[ContactResponse], name="Return all contacts")
async def get_contacts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db),
                       user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts function returns a list of contacts.

    :param skip: int: Skip the first n contacts
    :param limit: int: Limit the number of contacts returned
    :param db: AsyncSession: Pass the database session to the repository layer
    :param user: User: Get the current user from the auth_service
    :return: A list of contacts
    """
    contacts = await repository_contacts.get_contacts(skip, limit, db, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                      user: User = Depends(auth_service.get_current_user)):
    """
    The get_contact function is a GET request that returns the contact with the given ID.
    If no such contact exists, it raises an HTTP 404 error.

    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the current user from the auth_service
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repository_contacts.get_contact_by_id(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
        name: str = Query(None, description="Search by name"),
        surname: str = Query(None, description="Search by surname"),
        email: str = Query(None, description="Search by email"),
        limit: int = Query(10, ge=10, le=500),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        user: User = Depends(auth_service.get_current_user)
):
    """
    The search_contacts function allows you to search for contacts by name, surname or email.
        The function returns a list of contacts that match the search criteria.
        If no contact is found, an HTTP 404 error is returned.

    :param name: str: Search by name
    :param description: Document the endpoint in the openapi schema
    :param surname: str: Search by surname
    :param description: Document the endpoint
    :param email: str: Search for a contact by email
    :param description: Provide a description of the parameter
    :param limit: int: Limit the number of contacts returned
    :param ge: Specify that the limit must be greater than or equal to 10
    :param le: Limit the number of contacts returned
    :param offset: int: Skip the first offset contacts in the database
    :param ge: Specify the minimum value for a parameter
    :param db: AsyncSession: Get the database session
    :param user: User: Get the current user from the auth_service
    :return: A list of contact objects
    """
    contacts = await repository_contacts.search_contacts(name, surname, email, limit, offset, db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacts not found")
    return contacts


@router.get("/birthdays/", response_model=List[ContactResponse])
async def get_contacts_with_birthdays(days: int = 7, db: AsyncSession = Depends(get_db),
                                      user: User = Depends(auth_service.get_current_user)):
    """
    The get_contacts_with_birthdays function returns a list of contacts with birthdays in the next 7 days.

    :param days: int: Specify how many days in advance we want to get the contacts with birthdays
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the current user from the auth_service
    :return: A list of contacts with birthdays in the next 7 days
    """
    contacts = await repository_contacts.get_contacts_with_birthdays(days, db, user)
    if contacts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contacts


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactModel, db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactModel: Pass the contact data to the function
    :param db: AsyncSession: Pass the database session to the repository
    :param user: User: Get the user from the auth_service
    :return: A contactModel instance
    """
    contact = await repository_contacts.create_contact(body, db, user)
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(body: ContactModel, contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The update_contact function updates a contact in the database.
    The function takes an id of the contact to update, and a body containing the new data for that contact.
    It returns an updated ContactModel object.

    :param body: ContactModel: Pass the contact information to be updated
    :param contact_id: int: Specify the id of the contact to be deleted
    :param db: AsyncSession: Get the database session
    :param user: User: Get the user that is currently logged in
    :return: The updated contact
    """
    contact = await repository_contacts.update_contact(contact_id, body, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int = Path(ge=1), db: AsyncSession = Depends(get_db),
                         user: User = Depends(auth_service.get_current_user)):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the contact id that will be used to find the contact in the database
    :param db: AsyncSession: Pass the database connection to the function
    :param user: User: Get the current user
    :return: A contact object
    """
    contact = await repository_contacts.delete_contact(contact_id, db, user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
